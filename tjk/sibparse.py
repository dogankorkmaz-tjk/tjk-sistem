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


if __name__ == "__main__":
    isle()
