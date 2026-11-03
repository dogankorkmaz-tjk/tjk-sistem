"""T102: z2'li Benter egzotik ROI geriye testi (ön kayıt hipotez_defteri T102). python3 data/analiz/t102_z2_roi.py"""
import os, sys, random, datetime as dt
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import g1
K = {}
for r in g1._satirlar(): K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
H, J, AJ = {}, {}, {}; R = []
for key in sorted(K):
    ok = [r for r in K[key] if r["kosmadi"] != "True" and g1._fl(r["ganyan"], 0) > 1 and g1._fl(r["sira"], 0) > 0]
    if len(ok) < 6: continue
    ok.sort(key=lambda r: g1._fl(r["sira"]))
    if [g1._fl(r["sira"]) for r in ok[:5]] != [1., 2., 3., 4., 5.]: continue
    n = len(ok); inv = np.array([1 / g1._fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
    X = g1._oz(H, J, AJ, ok, pm, gun)
    F = np.array([g1.galop_f(r["at"], dt.date.fromisoformat(key[0])) for r in ok]) if key[0] >= "2026-02-01" else None
    R.append(dict(key=key, nos=[int(g1._fl(r['no'],0)) for r in ok], gun=key[0], ay=key[0][:7], lm=np.log(pm), X=X, F=F))
    for i, r in enumerate(ok):
        pct = 1 - (g1._fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == 0 else 0.0
        H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
        j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
        a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
print("koşu", len(R)); M = max(len(r["lm"]) for r in R)
def pack(rl, F=False):
    N = len(rl); LM = np.full((N, M), -1e9); XX = np.zeros((N, M, 9)); FF = np.zeros((N, M, 7))
    for k, r in enumerate(rl):
        n = len(r["lm"]); LM[k, :n] = r["lm"]; XX[k, :n] = r["X"]
        if F and r["F"] is not None: FF[k, :n] = r["F"]
    return LM, XX, FF
def steps(s, gam, nstep=5):
    N = len(s); idx = np.arange(N); mask = s > -1e8; out = []; ds = np.zeros_like(s); dg = np.zeros(nstep - 1)
    for j in range(nstep):
        z = np.where(mask, gam[j] * s, -1e30); z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
        out.append(-np.log(p[idx, j] + 1e-12)); d = p.copy(); d[idx, j] -= 1; ds += gam[j] * d
        if j: dg[j - 1] = (d * np.where(mask, s, 0)).sum()
        mask[idx, j] = False
    return out, ds, dg
def fit1(rl, l2):
    LM, XX, _ = pack(rl)
    def f(t):
        s = np.where(LM > -1e8, t[0] * LM + XX @ t[1:10], -1e9); out, ds, dg = steps(s, np.r_[1.0, t[10:14]])
        g = np.r_[(ds * LM.clip(-50, 0)).sum(), np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], dg]
        return sum(o.sum() for o in out) + l2 * (t[1:10] @ t[1:10]), g
    t0 = np.zeros(14); t0[0] = 1; t0[10:] = 1
    return minimize(f, t0, jac=True, method="L-BFGS-B").x
def fit2(rl, t1, l2=20.0):
    LM, XX, FF = pack(rl, True); S0 = np.where(LM > -1e8, t1[0] * LM + XX @ t1[1:10], -1e9); msk = S0 > -1e8
    mu = FF[msk].mean(0); sd = FF[msk].std(0) + 1e-9; Z = (FF - mu) / sd; N = len(rl); idx = np.arange(N)
    def f(b):
        s = S0 + Z @ b; s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True); d = p.copy(); d[idx, 0] -= 1
        return -np.log(p[idx, 0] + 1e-12).sum() + l2 * (b @ b), np.einsum("nm,nmk->k", d, Z) + 2 * l2 * b
    return minimize(f, np.zeros(7), jac=True, method="L-BFGS-B").x, mu, sd
def evalm(rl, t1, bg=None):
    LM, XX, FF = pack(rl, True); s = np.where(LM > -1e8, t1[0] * LM + XX @ t1[1:10], -1e9)
    if bg is not None: b, mu, sd = bg; s = s + ((FF - mu) / sd) @ b
    out, _, _ = steps(s, np.r_[1.0, t1[10:14]]); return np.array(out)
import pandas as pd
from tjk import ortak as O, mesafe as MS
from tjk.ozellik import hazirla
from tjk.golge import _fit, _oku, EK
from tjk.calistir import yukle_model
MJ = yukle_model()
dj = MS.ekle(hazirla(_oku("temiz"), _oku("program"), MJ)); dj["f_lp2"] = np.log(dj.p_piyasa.clip(lower=1e-6)) ** 2
dj = dj[dj.temiz & dj.kazandi.notna() & dj.lp.notna()].copy(); dj["tarih"] = dj.tarih.astype(str)
feat = MJ["feat"] + EK; cols = feat + ["f_lp2"]; nf = len(feat)
print("Jason verisi", dj.shape, flush=True)
Z2 = {}
for m in sorted({t[:7] for t in dj.tarih if t >= "2025-10"}):
    tr = dj[dj.tarih < m + "-01"]; te = dj[dj.tarih.str[:7] == m]
    if len(te) == 0: continue
    th, mu, sd, _ = _fit(tr, cols)
    X = np.nan_to_num(((te[cols] - mu) / sd).values); z = X[:, :nf] @ th[1:1 + nf]
    for t, h, k, n, v in zip(te.tarih, te.hipodrom, te.kosu, te.no, z): Z2[(t, h, int(k), int(n))] = float(v)
    print("z2", m, len(te), flush=True)
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]

import itertools, random, glob
from tjk import egzotik as E
OD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/2026-*.csv.gz"))])
OD = OD[OD.tur.isin(list(E.K))]; PAY = {}
for q in OD.itertuples():
    kk = tuple(int(z) for z in str(q.kombo).split("/")); kk = tuple(sorted(kk)) if q.tur == "İKİLİ" else kk
    PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu), q.tur), {})[kk] = PAY.get((q.tarih, q.hipodrom, int(q.kosu), q.tur), {}).get(kk, 0) + float(q.tutar)
def combos(s, gam, k):
    out = {}; n = len(s)
    for c in itertools.permutations(range(n), k):
        pr = 1.0; used = []
        for j, i in enumerate(c):
            z = np.exp(gam[j] * (s - s.max())); m = np.ones(n, bool); m[used] = False
            pr *= z[i] / z[m].sum(); used.append(i)
        out[c] = pr
    return out
def fitb(L):
    def f(b):
        t = 0.0
        for s, z in L: x = s + b[0] * z; t += -(x[0] - np.max(x) - np.log(np.exp(x - np.max(x)).sum()))
        return t + 1.0 * b[0] ** 2
    return minimize(f, [0.0], method="L-BFGS-B").x[0]
ORANLAR = [1.15, 1.30, 1.50]; ST = {}; HIST = []; bler = {}
for ai, a in enumerate(test):
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1); bb = fitb(HIST) if HIST else None; bler[a] = bb
    cur = []
    for r in te:
        s2 = t1[0] * r["lm"] + r["X"] @ t1[1:10]
        if r["F"] is not None: s2 = s2 + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
        z = np.array([Z2.get((r["key"][0], r["key"][1], int(r["key"][2]), int(no)), 0.0) for no in r["nos"]])
        cur.append((s2, z))
        if bb is None: continue
        h, ko = r["key"][1], int(r["key"][2]); nos = r["nos"]; pk = np.exp(r["lm"])
        for tur, k in E.K.items():
            pay = PAY.get((r["key"][0], h, ko, tur))
            if pay is None: continue
            A = E._kombolar(dict(enumerate(pk)), k)
            if tur == "İKİLİ":
                A2 = {}
                for c, v in A.items(): A2[tuple(sorted(c))] = A2.get(tuple(sorted(c)), 0) + v
                A = A2
            for ad, s in (("v2", s2), ("v2+z2", s2 + bb * z)):
                B = combos(s, np.r_[1.0, t1[10:14]], k)
                if tur == "İKİLİ":
                    B2 = {}
                    for c, v in B.items(): B2[tuple(sorted(c))] = B2.get(tuple(sorted(c)), 0) + v
                    B = B2
                for orn in ORANLAR:
                    sec = [c for c in A if A[c] >= E.ESIK[tur] and B[c] / A[c] >= orn]
                    if not sec: continue
                    ka = sum(pay.get(tuple(nos[i] for i in c), 0.0) for c in sec)
                    ST.setdefault((ad, tur, orn), []).append((r["gun"], len(sec) * E.BIRIM[tur], ka))
    HIST += cur; print("roi", a, flush=True)
def gunlu(L):
    d = {}
    for g, b, k in L: x = d.setdefault(g, [0.0, 0.0]); x[0] += b; x[1] += k
    return d
def roi(d): B = sum(x[0] for x in d.values()); K_ = sum(x[1] for x in d.values()); return (K_ - B) / B if B else float("nan")
rr = np.random.default_rng(13)
def boots(tur, orn, B=3000):
    d1 = gunlu(ST.get(("v2", tur, orn), [])); d2 = gunlu(ST.get(("v2+z2", tur, orn), [])); ug = sorted(set(d1) | set(d2)); f = []; g1 = []; g2 = []
    for _ in range(B):
        sm = rr.choice(len(ug), len(ug)); a1 = {}; a2 = {}
        for j, i in enumerate(sm):
            for dd, aa in ((d1, a1), (d2, a2)):
                if ug[i] in dd: aa[j] = dd[ug[i]]
        x, y = roi(a1), roi(a2); g1.append(x); g2.append(y); f.append(y - x)
    return roi(d1), np.percentile(g1, [2.5, 97.5]), roi(d2), np.percentile(g2, [2.5, 97.5]), roi(d2) - roi(d1), np.percentile(f, [2.5, 97.5]), sum(x[0] for x in d1.values()), sum(x[0] for x in d2.values())
out = [f"T102: değerlendirme {test[1]}..{test[-1]}; b: " + ", ".join(f"{a} {v:+.3f}" for a, v in bler.items() if v is not None), "tür | oran | ROI v2 [GA] (bedel) | ROI v2+z2 [GA] (bedel) | fark [GA]"]
for tur in E.K:
    for orn in ORANLAR:
        if not ST.get(("v2", tur, orn)) and not ST.get(("v2+z2", tur, orn)): continue
        r1, c1, r2, c2, df, cf, b1, b2 = boots(tur, orn)
        out.append(f"{'BİRİNCİL ' if (tur=='SIRALI İKİLİ' and orn==1.15) else ''}{tur:13s} {orn:.2f} | v2 {r1:+.1%} [{c1[0]:+.1%},{c1[1]:+.1%}] ({b1:.0f}) | C {r2:+.1%} [{c2[0]:+.1%},{c2[1]:+.1%}] ({b2:.0f}) | fark {df:+.1%} [{cf[0]:+.1%},{cf[1]:+.1%}]")
open("data/analiz/t102_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
