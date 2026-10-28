"""GitHub Release ile gelen dosyaları işler: Accurace PDF'leri ve TJK yarış videoları.
Kullanım:  python3 -m tjk.gelen <klasör> [hipodrom]
 - PDF adı  ...2024-03-02-istanbul-3.pdf  (tarih-hipodrom-koşu)  -> data/accurace/2024-03-02_istanbul_3.json
 - Video adı 26101055.mp4 (yyaagg + hipodrom kodu + koşu)        -> data/video_seyir/2026-10-10_ankara_5.json
   Video için hipodrom 2. argümandan (Release açıklamasının ilk kelimesi) gelir; verilmezse kod 5=ankara varsayılır.
Koşan at numaraları data/kosu_at (veya bugun.json - koşmaz) içinden alınır; bulunamazsa video atlanır ve hata yazılır.
"""
import os, re, sys, json, glob, gzip, csv, unicodedata
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOD = {"1": "adana", "2": "izmir", "3": "istanbul", "4": "bursa", "5": "ankara", "6": "sanliurfa", "7": "elazig", "8": "diyarbakir", "9": "kocaeli"}


def _ascii(s):
    s = unicodedata.normalize("NFKD", s.replace("İ", "I").replace("ı", "i")).encode("ascii", "ignore").decode()
    return s.lower().strip()


def _atlar(tarih, hip, kosu):
    """Koşan atlar: data/temiz (sonuç) içinde kosmadi olmayanlar."""
    f = os.path.join(KOK, "data", "temiz", tarih[:7] + ".csv.gz")
    if os.path.exists(f):
        d = pd.read_csv(f)
        d = d[(d.tarih == tarih) & (d.hipodrom.map(_ascii) == hip) & (d.kosu == kosu)]
        d = d[~d.kosmadi.fillna(False).astype(bool)]
        if len(d):
            return sorted(int(x) for x in d.no)
    # gün henüz kapanmadıysa: program (kosu_at) eksi koşmaz listesi
    f = os.path.join(KOK, "data", "kosu_at", tarih[:7] + ".csv.gz")
    if os.path.exists(f):
        d = pd.read_csv(f)
        d = d[(d.tarih == tarih) & (d.hipodrom.map(_ascii) == hip) & (d.kosu == kosu)]
        km = set()
        fk = os.path.join(KOK, "data", "kosmaz", tarih + ".csv")
        if os.path.exists(fk):
            z = pd.read_csv(fk)
            km = set(z[(z.hipodrom.map(_ascii) == hip) & (z.kosu == kosu)].no)
        n = sorted(int(x) for x in d.no if x not in km)
        if n:
            return n
    return None


def _sade(s):
    return re.sub(r"[^a-z0-9]", "", _ascii(str(s)))


_SONUC = {}


def _ad_eslestir(d, tarih, hip, kosu):
    """Accurace satırlarını resmi sonuçtaki at adıyla eşleştirip numarayı oradan yazar. Değişiklik varsa True."""
    import difflib
    ay = tarih[:7]
    if ay not in _SONUC:
        f = os.path.join(KOK, "data", "temiz", ay + ".csv.gz")
        _SONUC[ay] = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["tarih", "hipodrom", "kosu", "no", "at"])
    g = _SONUC[ay]
    g = g[(g.tarih == tarih) & (g.hipodrom.map(_ascii) == hip) & (g.kosu == kosu)]
    if g.empty:
        return False
    ad = {_sade(a): int(n) for a, n in zip(g["at"], g["no"])}
    degisti = False
    for r in d.get("atlar", []):
        x = difflib.get_close_matches(_sade(r.get("ad", "")), list(ad), n=1, cutoff=0.75)
        if x and r.get("no") != ad[x[0]]:
            if r.get("no") is not None and "no_ocr" not in r:
                r["no_ocr"] = r["no"]
            r["no"] = ad[x[0]]; r["no_kaynak"] = "ad"; degisti = True
    return degisti


def ozet_yaz():
    """data/accurace/*.json: tek eksik at numarasini doldur, durum ozetini docs/data/accurace_ozet.json'a yaz."""
    gun = {}
    for f in sorted(glob.glob(os.path.join(KOK, "data", "accurace", "*.json"))):
        ad = os.path.basename(f)[:-5]
        m = re.match(r"(\d{4}-\d\d-\d\d)_(.+)_(\d+)$", ad)
        if not m:
            continue
        t, hip, k = m.group(1), m.group(2), int(m.group(3))
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        atlar = d.get("atlar", [])
        bek = _atlar(t, hip, k)
        if _ad_eslestir(d, t, hip, k):                     # 15 Eki 2026: numara, resmi sonuçtaki at adından (OCR'dan daha güvenilir)
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)
        nolar = [a.get("no") for a in atlar]
        if bek and nolar.count(None) == 1:
            eksik = [n for n in bek if n not in nolar]
            if len(eksik) == 1:
                atlar[nolar.index(None)]["no"] = eksik[0]
                nolar = [a.get("no") for a in atlar]
                json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)
        dolu = [n for n in nolar if n is not None]
        sorun = []
        if bek is None:
            sorun.append("starter listesi yok")
        else:
            if len(atlar) != len(bek):
                sorun.append("at sayisi %d / beklenen %d" % (len(atlar), len(bek)))
            if len(set(dolu)) != len(dolu):
                sorun.append("tekrar eden numara")
            if None in nolar:
                sorun.append("okunamayan numara")
        g = gun.setdefault(t, {}).setdefault(hip, {"kosu": [], "sorunlu": []})
        g["kosu"].append(k)
        if sorun:
            g["sorunlu"].append({"kosu": k, "sorun": "; ".join(sorun)})
    cikis = {"uretim": pd.Timestamp.now(tz="Europe/Istanbul").strftime("%Y-%m-%d %H:%M"),
             "toplam": sum(len(h["kosu"]) for g in gun.values() for h in g.values()),
             "gunler": {t: {h: {"kosu": sorted(v["kosu"]), "sorunlu": v["sorunlu"]} for h, v in g.items()} for t, g in gun.items()}}
    os.makedirs(os.path.join(KOK, "docs", "data"), exist_ok=True)
    json.dump(cikis, open(os.path.join(KOK, "docs", "data", "accurace_ozet.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return cikis["toplam"]


def pdf_isle(yol, cikis):
    from tjk import accurace
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})-([a-z\-]+?)-(\d+)\.pdf$", os.path.basename(yol).lower())
    if not m:
        return f"PDF adı anlaşılmadı: {os.path.basename(yol)}"
    tarih, hip, kosu = f"{m[1]}-{m[2]}-{m[3]}", m[4], int(m[5])
    ad = f"{tarih}_{hip}_{kosu}"
    c = accurace.oku(yol)
    for r in c["atlar"]:
        r.pop("ham", None)
    c.update(tarih=tarih, hipodrom=hip, kosu=kosu)
    os.makedirs(os.path.join(KOK, "data", "accurace"), exist_ok=True)
    json.dump(c, open(os.path.join(KOK, "data", "accurace", ad + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    return f"PDF {ad}: {len(c['atlar'])} at"


def png_isle(yol):
    from tjk import accurace
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})_([a-z\-]+)_(\d+)\.png$", os.path.basename(yol).lower())
    if not m:
        return f"PNG adı anlaşılmadı: {os.path.basename(yol)}"
    tarih, hip, kosu = f"{m[1]}-{m[2]}-{m[3]}", m[4], int(m[5])
    c = accurace.oku(yol)
    for r in c["atlar"]:
        r.pop("ham", None)
    c.update(tarih=tarih, hipodrom=hip, kosu=kosu)
    os.makedirs(os.path.join(KOK, "data", "accurace"), exist_ok=True)
    json.dump(c, open(os.path.join(KOK, "data", "accurace", f"{tarih}_{hip}_{kosu}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return f"Accurace {tarih}_{hip}_{kosu}: {len(c['atlar'])} at"


def video_isle(yol, hip_arg):
    from tjk import video_seyir
    m = re.match(r"(\d{2})(\d{2})(\d{2})(\d)(\d{1,2})\.mp4$", os.path.basename(yol).lower())
    if not m:
        return f"Video adı anlaşılmadı: {os.path.basename(yol)}"
    tarih = f"20{m[1]}-{m[2]}-{m[3]}"
    hip = _ascii(hip_arg) if hip_arg else KOD.get(m[4])
    kosu = int(m[5])
    if not hip:
        return f"Hipodrom bilinmiyor (kod {m[4]}): {os.path.basename(yol)}"
    atlar = _atlar(tarih, hip, kosu)
    if not atlar:
        return f"Koşan atlar bulunamadı: {tarih} {hip} {kosu}"
    ad = f"{tarih}_{hip}_{kosu}"
    c = video_seyir.isle(yol, atlar, ad)
    return f"Video {ad}: geçerli kare {c['gecerli_kare']}/{c['kare']}, {len(atlar)} at"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    hip = sys.argv[2] if len(sys.argv) > 2 else None
    for f in sorted(glob.glob(os.path.join(sys.argv[1], "**", "*"), recursive=True)):
        if f.lower().endswith(".pdf"):
            try:
                print(pdf_isle(f, None), flush=True)
            except Exception as e:
                print("HATA", os.path.basename(f), e, flush=True)
        elif f.lower().endswith(".png"):
            try:
                print(png_isle(f), flush=True)
            except Exception as e:
                print("HATA", os.path.basename(f), e, flush=True)
        elif f.lower().endswith(".mp4"):
            try:
                print(video_isle(f, hip), flush=True)
            except Exception as e:
                print("HATA", os.path.basename(f), e, flush=True)
    print('ozet: %d kosu' % ozet_yaz(), flush=True)
