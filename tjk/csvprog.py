"""TJK'dan elle indirilen 'Günlük Yarış Programı' CSV dosyalarını okur.
Dosyalar data/tjk_csv/ klasörüne yüklenir (adı önemli değil; hipodrom ve tarih dosyanın ilk satırından okunur).
Koşu bilgisi: saat, cins, yaş şartı, mesafe, pist, rekor derece, ikramiye + ekürlü atlar."""
import os, re, glob, datetime
import pandas as pd
from . import ortak as O

KLASOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tjk_csv")


def _sn(s):
    """'1.32.97' veya '1:37.16' -> saniye"""
    m = re.match(r"^\s*(\d+)[.:](\d{2})[.](\d{1,2})\s*$", str(s or ""))
    return int(m.group(1)) * 60 + int(m.group(2)) + float("0." + m.group(3)) if m else None


def _hip(ad):
    k = ad.strip().translate(O.TR).lower()
    for h, a in O.AD.items():
        if a.translate(O.TR).lower() == k:
            return h
    return None


def oku_dosya(yol):
    """-> (tarih, hipodrom, {kosu: bilgi dict}, {kosu: {at_no: {...}}}, ekurlu set((kosu,no)))"""
    metin = open(yol, encoding="utf-8-sig").read().replace("\r", "")
    sat = metin.split("\n")
    p = sat[0].split(";")
    hip = _hip(p[0])
    d = re.search(r"(\d{2})/(\d{2})/(\d{4})", sat[0])
    if not hip or not d:
        return None
    tarih = f"{d.group(3)}-{d.group(2)}-{d.group(1)}"
    kosular, atlar, ekur = {}, {}, set()
    kn = None
    for s in sat[1:]:
        m = re.match(r"^(\d+)\.\s*Kosu\s*:\s*(\d{1,2})[.:](\d{2});(.*)$", s)
        if m:
            kn = int(m.group(1)); saat = f"{int(m.group(2)):02d}:{m.group(3)}"
            alan = [a.strip() for a in m.group(4).split(";")]
            mes = next((int(re.match(r"(\d+)m", a).group(1)) for a in alan if re.match(r"^\d{3,4}m$", a)), None)
            pist = next((a for a in alan if a in ("Kum", "Çim", "Sentetik")), None)
            rek = next((_sn(a.split(":", 1)[1]) for a in alan if a.startswith("Rekor")), None)
            yas = alan[1] if len(alan) > 1 else None
            kosular[kn] = {"saat": saat, "cins": alan[0], "yas": yas, "mesafe": mes, "pist": pist,
                           "rekor_sn": rek, "ikramiye1": None}
            atlar[kn] = {}
            continue
        if kn and s.startswith("1.)") and kosular[kn]["ikramiye1"] is None:
            mm = re.match(r"1\.\)([\d.]+)", s)
            if mm:
                kosular[kn]["ikramiye1"] = int(mm.group(1).replace(".", ""))
            continue
        if kn and re.match(r"^\d+;", s):
            f = s.split(";")
            if len(f) >= 16:
                kilo = re.match(r"^([\d,]+)\s*(?:([+-][\d.]+))?", f[5].strip())
                atlar[kn][int(f[0])] = {"hnd": int(f[11]) if f[11].strip().isdigit() else None,
                                        "eid_sn": _sn(f[15]),
                                        "kilo": float(kilo.group(1).replace(",", ".")) if kilo else None,
                                        "kilo_fark": float(kilo.group(2)) if kilo and kilo.group(2) else 0.0}
            continue
        if "eküridir" in s:
            ek = re.findall(r"\((\d+)\)", s.split("eküridir")[0])
            for x in ek:
                ekur.add((kn, int(x)))
    return tarih, hip, kosular, atlar, ekur


def gunun(tarih):
    """tarih (YYYY-MM-DD) için klasördeki tüm hipodrom dosyaları -> {hipodrom: (kosular, atlar, ekur)}"""
    out = {}
    for yol in glob.glob(os.path.join(KLASOR, "*.csv")):
        try:
            r = oku_dosya(yol)
        except Exception as e:
            print("CSV okunamadı:", yol, e); continue
        if r and r[0] == tarih:
            out[r[1]] = r[2:]
    return out


def bilgi_metni(k):
    p = [k["cins"], k["yas"]]
    mp = " ".join(str(x) for x in (k["mesafe"] and f"{k['mesafe']}m", k["pist"]) if x)
    return " · ".join([x for x in p if x] + ([mp] if mp else []))


def kaydet(tarih, hip, kosular, atlar, veri_dizin):
    """data/kosu/YYYY-MM.csv.gz ve data/kosu_at/YYYY-MM.csv.gz (eğitim için birikir)."""
    kr = [{"tarih": tarih, "hipodrom": hip, "kosu": k, **v} for k, v in kosular.items()]
    ar = [{"tarih": tarih, "hipodrom": hip, "kosu": k, "no": n, **v} for k, d in atlar.items() for n, v in d.items()]
    for ad, rows, anahtar in (("kosu", kr, ["tarih", "hipodrom", "kosu"]), ("kosu_at", ar, ["tarih", "hipodrom", "kosu", "no"])):
        if not rows:
            continue
        yol = os.path.join(veri_dizin, ad, tarih[:7] + ".csv.gz")
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        yeni = pd.DataFrame(rows)
        if os.path.exists(yol):
            yeni = pd.concat([pd.read_csv(yol), yeni], ignore_index=True).drop_duplicates(anahtar, keep="last")
        yeni.sort_values(anahtar).to_csv(yol, index=False)
