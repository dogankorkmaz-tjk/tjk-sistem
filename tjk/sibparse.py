"""data/sib_ham/*.txt (tjk.org Sabit İhtimalli Yarış Programı sayfasından kopyalanıp yapıştırılan metin) -> data/sib_snap + data/sib.

Dosya adı: YYYY-MM-DD_HHMM[_ek].txt. Her ham dosya bir anlık görüntüdür (oranlar gün içinde değişir).
data/sib/<gün>-<hipodrom>.csv her zaman o hipodromun EN SON anlık görüntüsünden üretilir.
"""
import os, re, glob, csv

KOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HAM, SNAP, SIB = (os.path.join(KOK, d) for d in ("sib_ham", "sib_snap", "sib"))
T = [(1, 80), (1.02, 75), (1.10, 70), (1.19, 65), (1.30, 60), (1.45, 55), (1.60, 50), (1.75, 45), (2.0, 40),
     (2.2, 35), (2.6, 30), (3.0, 25), (3.6, 20), (4.5, 15), (6.0, 10), (9.0, 5), (18, 0)]


def kes(o):
    r = 0
    for t, k in T:
        if o >= t:
            r = k
    return r / 100


def sade(s):
    s = s.strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ç", "c")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


def sayi(x):
    try:
        return float(x.strip().replace(",", "."))
    except Exception:
        return None


def parse(metin):
    """-> (tarih, saat, satirlar). satirlar: dict(hipodrom,kosu,no,ad,oran,kosmaz)."""
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})\s+\S+\s*-\s*Sabit", metin)
    tarih = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
    s = re.search(r"Son g[üu]ncelleme\s*:\s*(\d{1,2}):(\d{2})", metin, re.I)
    saat = f"{int(s.group(1)):02d}{s.group(2)}" if s else None
    hip = kosu = None
    rows = []
    for ln in metin.splitlines():
        f = ln.split("\t")
        if len(f) >= 6 and f[0].strip().isdigit() and re.match(r"\d{1,2}[.:]\d{2}$", f[3].strip() if len(f) > 3 else ""):
            hip, kosu = f[1].strip(), int(f[2])
            continue
        if kosu and len(f) >= 10 and f[0].strip().isdigit():
            ham = f[-1].strip()
            oran = sayi(ham)
            kosmaz = int(bool(re.search(r"ko[sş]maz", ln, re.I)) or oran is None)
            rows.append(dict(hipodrom=sade(hip), kosu=kosu, no=int(f[0]), ad=f[1].strip(), oran=oran, kosmaz=kosmaz))
    return tarih, saat, rows


def isle():
    os.makedirs(SNAP, exist_ok=True); os.makedirs(SIB, exist_ok=True)
    son = {}                                            # (tarih,hip) -> (saat, ham dosya adı, satırlar)
    n = 0
    for yol in sorted(glob.glob(os.path.join(HAM, "*.txt"))):
        ad = os.path.basename(yol)
        if "_oyun_" in ad:
            continue
        metin = open(yol, encoding="utf-8", errors="replace").read()
        tarih, saat, rows = parse(metin)
        mm = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{4})", ad)
        tarih = tarih or (mm and mm.group(1)); saat = saat or (mm and mm.group(2))
        if not tarih or not rows:
            print("atlandı:", ad); continue
        for h in sorted({r["hipodrom"] for r in rows}):
            hr = [r for r in rows if r["hipodrom"] == h]
            for r in hr:
                r["kg"] = 0.0
            for k in {r["kosu"] for r in hr}:
                kg = round(sum(kes(r["oran"]) for r in hr if r["kosu"] == k and r["kosmaz"] and r["oran"]), 2)
                for r in hr:
                    if r["kosu"] == k:
                        r["kg"] = kg
            with open(os.path.join(SNAP, f"{tarih}_{saat}_{h}.csv"), "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh); w.writerow(["tarih", "saat", "hipodrom", "kosu", "no", "ad", "oran", "kosmaz", "kesinti_ganyan"])
                for r in hr:
                    w.writerow([tarih, saat, h, r["kosu"], r["no"], r["ad"], r["oran"] if r["oran"] is not None else "", r["kosmaz"], r["kg"]])
            key = (tarih, h)
            if key not in son or saat >= son[key][0]:
                son[key] = (saat, hr)
            n += 1
    for (tarih, h), (saat, hr) in son.items():
        with open(os.path.join(SIB, f"{tarih}-{h}.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["tarih", "hipodrom", "kosu", "no", "oran", "kosmaz", "kesinti_ganyan"])
            for r in hr:
                w.writerow([tarih, h, r["kosu"], r["no"], r["oran"] if r["oran"] is not None else "", r["kosmaz"], r["kg"]])
    print("SİB anlık görüntü işlendi:", n, "| en son görüntüden üretilen gün-hipodrom:", len(son))


OYUN = os.path.join(KOK, "sib_oyun")


def parse_oyun(metin):
    """Sabit İhtimalli Oyunlar sayfası (tek koşu) -> (tarih, saat, kosu, atlar, ikili, sirali).
    atlar: [{no,ad,ganyan,ilk2,ilk3,ilk4}], ikili/sirali: [(a,b,oran)]"""
    AY = {"ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6, "temmuz": 7, "ağustos": 8,
          "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12}
    m = re.search(r"(\d{1,2})\s+(\S+)\s+(\d{4})\s+\S+\s*\n?\s*>", metin)
    tarih = f"{m.group(3)}-{AY.get(m.group(2).lower(), 0):02d}-{int(m.group(1)):02d}" if m else None
    sg = re.search(r"Son G[üu]ncelleme\s*:\s*(\d{1,2}):(\d{2})", metin, re.I)
    saat = f"{int(sg.group(1)):02d}{sg.group(2)}" if sg else None
    k = re.search(r"^\s*(\d+)\s*-\s*\d{1,2}[:.]\d{2}\s*-", metin, re.M)
    kosu = int(k.group(1)) if k else None
    L = [x.strip() for x in metin.splitlines() if x.strip()]
    i = next((j for j, x in enumerate(L) if x.startswith("SABİT GANYAN")), None)
    if i is None:
        return tarih, saat, kosu, [], [], []
    L = L[i + 1:]
    secs, cur, j = [], [], 0
    while j + 2 < len(L) and re.fullmatch(r"\d+-", L[j]):
        no = int(L[j][:-1])
        if no == 1 and cur:
            secs.append(cur); cur = []
        cur.append((no, L[j + 1], sayi(L[j + 2])))
        j += 3
    if cur:
        secs.append(cur)
    n = len(secs[0]) if secs else 0
    # bölümler n atlıdır; son bölüm bir sonraki başlıktan önce biter
    secs = [x for x in secs if len(x) == n]
    atlar = []
    for no, ad, g in (secs[0] if secs else []):
        r = {"no": no, "ad": ad, "ganyan": g}
        for a, sec in zip(("ilk2", "ilk3", "ilk4"), secs[1:4]):
            r[a] = next((v for q, _, v in sec if q == no), None)
        atlar.append(r)
    pairs = []
    while j + 1 < len(L):
        mm = re.fullmatch(r"(\d+)-(\d+)", L[j])
        if mm:
            pairs.append((int(mm.group(1)), int(mm.group(2)), sayi(L[j + 1]))); j += 2
        else:
            j += 1
    k2 = n * (n - 1) // 2
    return tarih, saat, kosu, atlar, pairs[:k2], pairs[k2:]


def isle_oyun():
    os.makedirs(OYUN, exist_ok=True)
    c = 0
    for yol in sorted(glob.glob(os.path.join(HAM, "*_oyun_*.txt"))):
        ad = os.path.basename(yol)
        mm = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{4})_oyun_([a-z]+)_(\d+)\.txt", ad)
        if not mm:
            print("atlandı:", ad); continue
        tarih, saat, kosu, atlar, ik, sr = parse_oyun(open(yol, encoding="utf-8", errors="replace").read())
        t, hs, hip, k = mm.group(1), mm.group(2), mm.group(3), int(mm.group(4))
        if not atlar:
            print("ayrıştırılamadı:", ad); continue
        base = os.path.join(OYUN, f"{t}_{hs}_{hip}_{k}")
        with open(base + "_atlar.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["tarih", "saat", "hipodrom", "kosu", "no", "ad", "ganyan", "ilk2", "ilk3", "ilk4"])
            for r in atlar:
                w.writerow([t, hs, hip, k, r["no"], r["ad"]] + ["" if r.get(x) is None else r[x] for x in ("ganyan", "ilk2", "ilk3", "ilk4")])
        with open(base + "_ikili.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["tur", "a", "b", "oran"])
            for a, b, o in ik:
                w.writerow(["ikili", a, b, o])
            for a, b, o in sr:
                w.writerow(["sirali", a, b, o])
        c += 1
    print("Oyun sayfası işlendi:", c)


if __name__ == "__main__":
    isle()
    isle_oyun()
