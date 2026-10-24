"""Sıralı 5'li tutma + 3'lü ganyan ROI. Ön kayıt: hipotez_defteri 2026-10-24 12:15."""
import os, sys, math, random, glob
from multiprocessing import Pool
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
from tjk import besli, kupon as KP
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
def sm(s): e = np.exp(s - s.max()); return e / e.sum()
def kup5(a):
    p, gam, nos = a
    o = besli.kupon_g([float(x) for x in p], 96, G=[1.0] + list(gam))
    return None if o is None else o[0]
if __name__ == "__main__":
    aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]
    T = []                                              # (r, {model: (p, gam)})
    for a in test:
        tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
        tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
        for r in te:
            T.append((r, {"piyasa": (sm(skor(r, tp)), tp[10:14]), "G1-S": (sm(skor(r, t1)), t1[10:14]), "G1-S v2": (sm(skor(r, t1, bg)), t1[10:14])}))
    print("test koşu", len(T), flush=True)
    random.seed(11)
    # ---- (a) sıralı 5'li tutma
    jobs = [(m, i) for i in range(len(T)) for m in ("piyasa", "G1-S v2")]
    with Pool(os.cpu_count()) as P:
        out = P.map(kup5, [(T[i][1][m][0], T[i][1][m][1], None) for m, i in jobs], chunksize=8)
    H = {"piyasa": np.zeros(len(T)), "G1-S v2": np.zeros(len(T))}
    for (m, i), sets in zip(jobs, out):
        if sets is None: continue
        o = np.argsort(-1)  # placeholder
        # gerçek sıra: R'de ok sıralı (sira 1..5) → indeks 0..4 ilk beş
        ok = all(i_ in sets[k] for k, i_ in enumerate(range(5))) and len({0, 1, 2, 3, 4}) == 5
        H[m][i] = 1.0 if ok else 0.0
    gun = np.array([T[i][0]["gun"] for i in range(len(T))]); ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}
    def bs(d): return np.percentile([d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(800)], [2.5, 97.5])
    print(f"SIRALI 5'Lİ B=96: tutma piyasa {H['piyasa'].sum():.0f}/{len(T)} ({H['piyasa'].mean():.2%}) | v2 {H['G1-S v2'].sum():.0f} ({H['G1-S v2'].mean():.2%})")
    d = H["G1-S v2"] - H["piyasa"]; lo, hi = bs(d); print(f"  fark (v2−piyasa) {d.mean():+.2%} [{lo:+.2%},{hi:+.2%}]  | kâr için gereken ort. ödeme ≈ {96*1.25/max(H['G1-S v2'].mean(),1e-9):,.0f} TL")
    # ---- (b) 3'lü ganyan
    O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/2026-*.csv.gz"))]); O = O[O.tur == "3'LÜ GANYAN"]
    IDX = {(r["key"][0], r["key"][1], int(r["key"][2])): (i, r) for i, (r, _) in enumerate(T)}
    SON = {}
    for q in O.itertuples():
        ks = [IDX.get((q.tarih, q.hipodrom, int(q.kosu) - 2 + j)) for j in range(3)]
        if any(k is None for k in ks): continue
        kz = [set(int(z) for z in s.split(",")) for s in str(q.kombo).split("/")]
        ay_m, ay_p = [], []
        for (i, r) in ks:
            pk = np.exp(r["lm"]); pv = T[i][1]["G1-S v2"][0]
            ay_m.append(({n: (pv[j], pk[j]) for j, n in enumerate(r["nos"])}, {n: (pk[j], pk[j]) for j, n in enumerate(r["nos"])}))
        for B in (8, 16, 32):
            for ad, mod, idx in (("piyasa favori", "favori", 1), ("v2 favori", "favori", 0), ("v2 deger", "deger", 0)):
                ay = [a[idx] for a in ay_m]; sec = KP.kur(ay, B, mod); n = math.prod(len(s) for s in sec)
                hit = all(any(w in sec[l] for w in kz[l]) for l in range(3))
                SON.setdefault((B, ad), []).append((q.tarih, n, float(q.tutar) if hit else 0.0, hit))
    for k in sorted(SON):
        L = SON[k]; g_ = sorted({x[0] for x in L}); gg = {g: [x for x in L if x[0] == g] for g in g_}
        def roi(unit, G): return (sum(x[2] for g in G for x in gg[g]) - unit * sum(x[1] for g in G for x in gg[g])) / (unit * sum(x[1] for g in G for x in gg[g]))
        bsr = [roi(1.0, [random.choice(g_) for _ in g_]) for _ in range(600)]
        print(f"3'LÜ B={k[0]:2d} {k[1]:14s} n={len(L)} tutma {np.mean([x[3] for x in L]):.1%} ROI(1TL) {roi(1.0,g_):+.1%} [{np.percentile(bsr,2.5):+.1%},{np.percentile(bsr,97.5):+.1%}] ROI(1,25TL) {roi(1.25,g_):+.1%}")
