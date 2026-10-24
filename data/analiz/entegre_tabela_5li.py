"""Tabela + sıralı 5'li ROI. Ön kayıt: hipotez_defteri 2026-10-24 12:30."""
import os, sys, math, random, glob, itertools
from multiprocessing import Pool
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
from tjk import besli, tabela
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
def sm(s): e = np.exp(s - s.max()); return e / e.sum()
def is_(a):
    kind, p, gam = a; p = [float(x) for x in p]; G = [1.0] + list(gam)
    if kind == "t24": o = tabela.kupon(p, 24, G)
    elif kind == "t120": o = tabela.kupon(p, 120, G)
    elif kind == "tbox":
        sr = sorted(range(len(p)), key=lambda i: -p[i]); o = ([sr[:5]] * 4, 0) if len(p) >= 6 else None
    else: o = besli.kupon_g(p, int(kind[1:]), G=G)
    return None if o is None else o[0]
if __name__ == "__main__":
    O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/2026-*.csv.gz"))]); P = {}
    for q in O.itertuples():
        P.setdefault((q.tarih, q.hipodrom, int(q.kosu)), {}).setdefault(q.tur, []).append(float(q.tutar))
    aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]; T = []
    for a in test:
        tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
        tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
        for r in te:
            pr = P.get(r["key"])
            if pr: T.append((r, pr, {"piyasa": (sm(skor(r, tp)), tp[10:14]), "G1-S v2": (sm(skor(r, t1, bg)), t1[10:14])}))
    random.seed(5); res = {}
    for bahis, kinds, unit in (("TABELA", ("t24", "t120", "tbox"), 1.5), ("SIRALI 5'Lİ", ("b48", "b96", "b150"), 1.25)):
        sel = [t for t in T if (("TABELA BAHİS" in t[1] or "TABELA BAHİS SIRASIZ" in t[1]) if bahis == "TABELA" else ("SIRALI 5 Lİ BAHİS" in t[1] or "SIRALI 5 Lİ BAHİS DEVİR" in t[1]))]
        print(bahis, "havuz koşusu (modelde)", len(sel), flush=True)
        for kind in kinds:
            for m in ("piyasa", "G1-S v2"):
                with Pool(2) as pool: out = pool.map(is_, [(kind, t[2][m][0], t[2][m][1]) for t in sel], chunksize=8)
                L = []; hyp = 0
                for t, sets in zip(sel, out):
                    if sets is None: continue
                    nL = 4 if bahis == "TABELA" else 5
                    hit = all(k in sets[k] for k in range(nL))
                    if bahis == "TABELA":
                        v = sum(1 for x in itertools.product(*sets) if len(set(x)) == 4); npm = sum(1 for x in itertools.product(*sets) if len(set(x)) == 4 and set(x) == {0, 1, 2, 3})
                        sirali = max(t[1].get("TABELA BAHİS", [0.0])); sirasiz = max(t[1].get("TABELA BAHİS SIRASIZ", [0.0]))
                        kz = (sirali if hit else 0.0) + (npm - (1 if hit else 0)) * sirasiz
                    else:
                        v = besli.gecerli_say(sets); hit = hit and len(set(range(5))) == 5
                        kz = max(t[1].get("SIRALI 5 Lİ BAHİS", [0.0])) if hit else 0.0
                        if hit and "SIRALI 5 Lİ BAHİS" not in t[1]: hyp += 1
                    L.append((t[0]["gun"], v * unit, kz, hit))
                gun = sorted({x[0] for x in L}); gg = {g: [x for x in L if x[0] == g] for g in gun}
                def roi(G): b = sum(x[1] for g in G for x in gg[g]); return (sum(x[2] for g in G for x in gg[g]) - b) / b
                bsr = [roi([random.choice(gun) for _ in gun]) for _ in range(700)]
                res[(bahis, kind, m)] = L
                print(f"{bahis:10s} {kind:5s} {m:8s} n={len(L)} tutma {sum(x[3] for x in L)} ({np.mean([x[3] for x in L]):.1%}) ROI {roi(gun):+.1%} [{np.percentile(bsr,2.5):+.1%},{np.percentile(bsr,97.5):+.1%}] devir-varsayımsal {hyp}", flush=True)
