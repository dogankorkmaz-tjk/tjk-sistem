"""Elle indirilen TJK 'Günlük Yarış Sonuçları' CSV'si ve 'Kronometrik Dereceler ve Muhtemel Ganyanlar' (.doc/HTML) dosyalarını okur.
Çıktılar: data/odeme (tüm bahis ikramiyeleri), data/zengin (at başına son AGF + fark), data/kron (Son 800 + farklar), data/havuz (altılı/5'li... dağıtılacak tutarlar)."""
import os, re, glob, html as _html
import numpy as np, pandas as pd
from . import ortak as O
from .csvprog import _hip

KOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SONUC_KLASOR = os.path.join(KOK, "tjk_sonuc")
KRON_KLASOR = os.path.join(KOK, "tjk_kron")


def _tl(s):
    return float(str(s).replace(".", "").replace(",", "."))


DEVIR = re.compile(r"((?:\d+\.\s*)?[A-Za-zÇĞİÖŞÜçğıöşü0-9' ]+?)\(([\d/,.]+)\)\s*:\s*Bilen çıkmamıştır,\s*([\d.,]+)\s*TL devretmiştir")
ODEME = re.compile(r"((?:\d+\.\s*)?[A-Za-zÇĞİÖŞÜçğıöşü0-9' ]+?)\(([\d/,.]+)\)\s*:\s*([\d.]+,\d+)\s*TL")


KOD = {"SK", "KG", "DB", "K", "SKG", "GKR", "SGKR", "OF", "ÖG", "YP"}
_PROG = {}


def _norm(a):
    a = re.sub(r"[^A-ZÇĞİÖŞÜ0-9]", "", a.upper().replace("İ", "I").replace("I", "I"))
    return a.replace("Ç", "C").replace("Ğ", "G").replace("Ö", "O").replace("Ş", "S").replace("Ü", "U")


def _ad_kod(ad):
    t = ad.replace("(Koşmaz)", "").split(); k = []
    while t and t[-1] in KOD:
        k.append(t.pop())
    return " ".join(t), " ".join(sorted(k))


def _prog_no(tarih, hip, kosu, ad):
    """Sonuç CSV'sindeki ilk sütun BİTİŞ SIRASIDIR (program numarası değil). At adından program numarasını bulur."""
    ay = tarih[:7]
    if ay not in _PROG:
        yol = os.path.join(KOK, "program", ay + ".csv.gz")
        _PROG[ay] = pd.read_csv(yol) if os.path.exists(yol) else pd.DataFrame(columns=["tarih", "hipodrom", "kosu", "no", "p_at"])
    p = _PROG[ay]; p = p[(p.tarih == tarih) & (p.hipodrom == hip) & (p.kosu == kosu)]
    h = {_norm(str(r.p_at)): int(r.no) for r in p.itertuples()}
    return h.get(_norm(ad))


def oku_sonuc_csv(yol):
    metin = open(yol, encoding="utf-8-sig").read().replace("\r", "")
    sat = metin.split("\n")
    hip = _hip(sat[0].split(";")[0]); d = re.search(r"(\d{2})/(\d{2})/(\d{4})", sat[0])
    if not hip or not d:
        return None
    tarih = f"{d.group(3)}-{d.group(2)}-{d.group(1)}"
    odeme, zengin, kn = [], [], None
    for s in sat[1:]:
        m = re.match(r"^(\d+)\.\s*Kosu\s*:", s)
        if m:
            kn = int(m.group(1)); continue
        if kn and re.match(r"^\d+;", s):
            f = s.split(";")
            if len(f) >= 15:
                a = re.match(r"%([\d.]+)\((\d+)\)", f[10].strip())
                fk = f[14].strip().replace("  ", " ")
                adx, kod = _ad_kod(f[1].strip())
                pno = _prog_no(tarih, hip, kn, adx)
                if pno is None:
                    continue                                  # program numarası bulunamayan at atlanır (yanlış eşleşmeyi önle)
                zengin.append({"tarih": tarih, "hipodrom": hip, "kosu": kn, "no": pno, "sira": int(f[0]), "ad": adx, "kod": kod,
                               "agf_son": float(a.group(1)) if a else np.nan, "agf_sira": int(a.group(2)) if a else np.nan,
                               "h": int(f[11]) if f[11].strip().isdigit() else np.nan, "fark_txt": fk, "fark_boy": O.fark_boy(fk)})
            continue
        if kn and ("TL" in s):
            for x in DEVIR.finditer(s):
                ad = x.group(1).strip(); sq = re.match(r"^(\d+)\.\s*(.*)$", ad)
                # bu satırdaki devir tutarı İngilizce biçimde yazılmış: 104,912.44
                odeme.append({"tarih": tarih, "hipodrom": hip, "kosu": kn, "tur": (sq.group(2) if sq else ad).upper() + " DEVİR",
                              "seq": int(sq.group(1)) if sq else 0, "kombo": x.group(2), "tutar": float(x.group(3).replace(",", ""))})
            for x in ODEME.finditer(s):
                ad = x.group(1).strip()
                sq = re.match(r"^(\d+)\.\s*(.*)$", ad)
                odeme.append({"tarih": tarih, "hipodrom": hip, "kosu": kn, "tur": (sq.group(2) if sq else ad).upper(),
                              "seq": int(sq.group(1)) if sq else 0, "kombo": x.group(2), "tutar": _tl(x.group(3))})
    return tarih, hip, odeme, zengin


def oku_kron(yol):
    b = open(yol, encoding="utf-8").read()
    t = re.sub(r"<style.*?</style>", "", b, flags=re.S); t = re.sub(r"<[^>]+>", "|", t); t = _html.unescape(t)
    t = re.sub(r"\|\s*(\|\s*)+", "|", t); t = re.sub(r"[ \t\r\n]+", " ", t)
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})\s+(\S+)\s+Ko", t)
    hip = _hip(m.group(4)) if m else None
    if not hip:
        return None
    tarih = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    kosu, havuz = [], []
    hv_ = re.search(r"Hava:\s*([^|]*)", t)
    hava = hv_.group(1).strip() if hv_ else ""  # ör. "Açık Kum Pist: Normal Çim Pist: 3.3 (Normal) Durum: 21C,Açık,Nem%55"
    parcalar = re.split(r"\|(\d+)\. Koşu: ", t)
    for i in range(1, len(parcalar) - 1, 2):
        kn = int(parcalar[i]); g = parcalar[i + 1]
        s8 = re.search(r"Son 800 :\s*([\d.\-]*)", g); fk = re.search(r"Farklar : ([^|]*)", g)
        kosu.append({"tarih": tarih, "hipodrom": hip, "kosu": kn, "son800": (s8.group(1) if s8 else "") or "",
                     "farklar": (fk.group(1).strip() if fk else ""), "hava_pist": hava})
    dz = re.search(r"Dağıtılacak Tutarlar:(.*)$", t)
    if dz:
        for x in re.finditer(r"\|?\s*((?:\d+\.\s*)?[^|:]+?)\s*:\s*([\d.]+,\d+)\s*TL", dz.group(1)):
            ad = x.group(1).strip(); sq = re.match(r"^(\d+)\.\s*(.*)$", ad)
            havuz.append({"tarih": tarih, "hipodrom": hip, "tur": (sq.group(2) if sq else ad).upper(),
                          "seq": int(sq.group(1)) if sq else 0, "tutar": _tl(x.group(2))})
    return tarih, hip, kosu, havuz


def _yaz(ad, df, anahtar):
    if df is None or not len(df):
        return 0
    for ay, g in df.groupby(df.tarih.str[:7]):
        yol = os.path.join(KOK, ad, f"{ay}.csv.gz"); os.makedirs(os.path.dirname(yol), exist_ok=True)
        if os.path.exists(yol):
            g = pd.concat([pd.read_csv(yol), g], ignore_index=True)
        g.drop_duplicates(anahtar, keep="last").sort_values(anahtar).to_csv(yol, index=False)
    return len(df)


def isle():
    """Yüklenen tüm dosyaları (tekrar çalıştırılabilir) data/ altına işler."""
    od, zg, kr, hv = [], [], [], []
    for y in sorted(glob.glob(os.path.join(SONUC_KLASOR, "*.csv"))):
        r = oku_sonuc_csv(y)
        if r: od += r[2]; zg += r[3]
        else: print("sonuç CSV okunamadı:", y)
    for y in sorted(glob.glob(os.path.join(KRON_KLASOR, "*.html"))):
        r = oku_kron(y)
        if r: kr += r[2]; hv += r[3]
        else: print("kron dosyası okunamadı:", y)
    n = (_yaz("odeme", pd.DataFrame(od), ["tarih", "hipodrom", "kosu", "tur", "seq", "kombo"]),
         _yaz("zengin", pd.DataFrame(zg), ["tarih", "hipodrom", "kosu", "no"]),
         _yaz("kron", pd.DataFrame(kr), ["tarih", "hipodrom", "kosu"]),
         _yaz("havuz", pd.DataFrame(hv), ["tarih", "hipodrom", "tur", "seq"]))
    if any(n): print("sonuç dosyaları işlendi: ödeme %d, zengin %d, kron %d, havuz %d" % n)
    return n
