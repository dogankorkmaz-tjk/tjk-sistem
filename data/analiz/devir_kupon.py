"""Devirli sıralı 5'li havuzlarda model-seçimli kupon ROI'si. Ön kayıt: hipotez_defteri 2026-10-24 19:30."""
import os, sys, glob, random, math
from multiprocessing import Pool
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
from tjk import besli
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
def sm(s): e = np.exp(s - s.max()); return e / e.sum()
def is_(a):
    B, p, gam, pm, gm = a; G = [1.0] + list(gam)
    o = besli.kupon_g([float(x) for x in p], B, G=G)
    if o is None: return None
    sets, pr = o
    W, T = besli._W([float(x) for x in pm], [1.0] + list(gm)); prm = besli._prob(W, T, sets)
    return sets, pr, prm
if __name__ == "__main__":
    O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/*.csv.gz"))]); O = O[O.tur.isin(["SIRALI 5 Lİ BAHİS", "SIRALI 5 Lİ BAHİS DEVİR"])]
    pool = {}
    for q in O.itertuples(): pool.setdefault((q.tarih, q.hipodrom, int(q.kosu)), []).append(q)
    din = {}
    for hip in {k[1] for k in pool}:
        prev = None
        for k in sorted([k for k in pool if k[1] == hip], key=lambda k: (k[0], k[2])):
            din[k] = bool(prev is not None and (pd.Timestamp(k[0]) - pd.Timestamp(prev)).days <= 3)
            prev = k[0] if any(q.tur.endswith("DEVİR") for q in pool[k]) else None
    RK = {r["key"]: r for r in R}; aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2025-03"]; T = []
    for a in test:
        tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a and r["key"] in pool]
        if not te: continue
        tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1) if a >= "2026-04" else None
        for r in te: T.append((r, sm(skor(r, tp)), tp[10:14], sm(skor(r, t1, bg)), t1[10:14]))
        print(a, len(te), flush=True)
    random.seed(5); res = {}
    for B in (48, 96, 150):
        for m, ix in (("piyasa", 1), ("G1-S", 3)):
            with Pool(4) as pl: out = pl.map(is_, [(B, t[ix], t[ix + 1], t[1], t[2]) for t in T], chunksize=8)
            L = []
            for t, o in zip(T, out):
                if o is None: continue
                sets, pr, prm = o; r = t[0]; rs = pool[r["key"]]; kz = 0.0; hit = False
                for q in rs:
                    if q.tur.endswith("DEVİR"): continue
                    try: order = [r["nos"].index(int(x)) for x in str(q.kombo).split("/")]
                    except Exception: continue
                    if all(order[k] in sets[k] for k in range(5)): kz += q.tutar; hit = True
                L.append((r["gun"], besli.gecerli_say(sets) * 1.25, kz, hit, din[r["key"]], pr, prm))
            res[(B, m)] = L
            for etiket, f in (("devirli", lambda x: x[4]), ("devirsiz", lambda x: not x[4])):
                S = [x for x in L if f(x)]
                if not S: continue
                gun = sorted({x[0] for x in S}); gg = {g: [x for x in S if x[0] == g] for g in gun}
                def roi(G): b = sum(x[1] for g in G for x in gg[g]); return (sum(x[2] for g in G for x in gg[g]) - b) / b
                bs = [roi([random.choice(gun) for _ in gun]) for _ in range(700)]
                eh = sum(x[5] for x in S); oran = np.mean([x[5] / x[6] for x in S if x[6] > 0])
                print(f"b{B:3d} {m:7s} {etiket:8s} n={len(S):4d} vuruş {sum(x[3] for x in S):2d} (beklenen model {eh:.1f}) ROI {roi(gun):+.1%} [{np.percentile(bs,2.5):+.1%},{np.percentile(bs,97.5):+.1%}] ort.oran {oran:.3f}", flush=True)
