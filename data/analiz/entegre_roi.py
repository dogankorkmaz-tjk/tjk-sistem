"""Egzotik ROI geriye testi. Ön kayıt: hipotez_defteri 2026-10-24 12:00."""
import os, sys, itertools, random
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
from tjk import egzotik as E
OD = pd.concat([pd.read_csv(f) for f in sorted(__import__("glob").glob("data/odeme/2026-*.csv.gz"))])
OD = OD[OD.tur.isin(list(E.K))]; PAY = {}
for q in OD.itertuples():
    kk = tuple(int(z) for z in str(q.kombo).split("/")); kk = tuple(sorted(kk)) if q.tur == "İKİLİ" else kk
    PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu), q.tur), {})[kk] = PAY.get((q.tarih, q.hipodrom, int(q.kosu), q.tur), {}).get(kk, 0) + float(q.tutar)
def combos(s, gam, k):                                   # exploded-logit kombinasyon olasılıkları
    out = {}; n = len(s)
    for c in itertools.permutations(range(n), k):
        pr = 1.0; used = []
        for j, i in enumerate(c):
            z = np.exp(gam[j] * (s - s.max())); m = np.ones(n, bool); m[used] = False
            pr *= z[i] / z[m].sum(); used.append(i)
        out[c] = pr
    return out
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
ORANLAR = [1.15, 1.30, 1.50]; ST = {}
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
    for r in te:
        h, ko = r["key"][1], int(r["key"][2]); nos = r["nos"]; pk = np.exp(r["lm"])
        for tur, k in E.K.items():
            pay = PAY.get((r["key"][0], h, ko, tur))
            if pay is None: continue
            A = E._kombolar(dict(enumerate(pk)), k)
            if tur == "İKİLİ":
                A2 = {}
                for c, v in A.items(): A2[tuple(sorted(c))] = A2.get(tuple(sorted(c)), 0) + v
                A = A2
            for ad, s, gam in (("piyasa+gamma", skor(r, tp), tp[10:14]), ("G1-S", skor(r, t1), t1[10:14]), ("G1-S v2", skor(r, t1, bg), t1[10:14])):
                B = combos(s, np.r_[1.0, gam], k)
                if tur == "İKİLİ":
                    B2 = {}
                    for c, v in B.items(): B2[tuple(sorted(c))] = B2.get(tuple(sorted(c)), 0) + v
                    B = B2
                for orn in ORANLAR + ([1.0] if ad == "piyasa+gamma" else []):
                    sec = [c for c in A if A[c] >= E.ESIK[tur] and B[c] / A[c] >= orn]
                    if not sec: continue
                    ka = sum(pay.get(tuple(nos[i] for i in c), 0.0) for c in sec)
                    ST.setdefault((ad, tur, orn), []).append((r["gun"], len(sec) * E.BIRIM[tur], ka))
random.seed(7)
def ozet(L):
    gun = sorted({g for g, _, _ in L}); gi = {g: [(b, k) for gg, b, k in L if gg == g] for g in gun}
    B = sum(b for _, b, _ in L); K_ = sum(k for _, _, k in L); bs = []
    for _ in range(600):
        bb = kk = 0
        for g in [random.choice(gun) for _ in gun]:
            for b, k in gi[g]: bb += b; kk += k
        bs.append((kk - bb) / bb)
    return len(L), B, (K_ - B) / B, np.percentile(bs, 2.5), np.percentile(bs, 97.5)
print("model | tür | oran | koşuda-seçim | bedel | ROI [GA]")
for key in sorted(ST, key=lambda x: (x[1], x[2], x[0])):
    n, B, roi, lo, hi = ozet(ST[key]); print(f"{key[0]:13s} {key[1]:12s} {key[2]:.2f} {n:5d} {B:9.0f} {roi:+7.1%} [{lo:+.1%},{hi:+.1%}]")
