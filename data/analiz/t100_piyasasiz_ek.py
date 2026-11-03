"""T100 piyasasız model ek at geriye testi (ön kayıt: hipotez_defteri T100). python3 data/analiz/t100_piyasasiz_ek.py"""
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
    F = None
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
def fit1b(rl, l2):
    LM, XX, _ = pack(rl)
    def f(t):
        s = np.where(LM > -1e8, 0.0 * LM + XX @ t[1:10], -1e9); out, ds, dg = steps(s, np.r_[1.0, t[10:14]])
        g = np.r_[0.0, np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], dg]
        return sum(o.sum() for o in out) + l2 * (t[1:10] @ t[1:10]), g
    t0 = np.zeros(14); t0[10:] = 1
    return minimize(f, t0, jac=True, method="L-BFGS-B", bounds=[(0, 0)] + [(None, None)] * 13).x
def skor(rl, t):
    LM, XX, _ = pack(rl); return np.where(LM > -1e8, t[0] * LM + XX @ t[1:10], -1e9), LM
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]
rng = np.random.default_rng(5)
rows = []   # gun, k, hit_taban, hit_ek(B), hit_Y(A k+1), hit_rastgele, pm_kazanan_ek(B hit ise), ayrisma, A1 hit
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    tA = fit1(tr, 30.0); tB = fit1b(tr, 30.0)
    sA, LM = skor(te, tA); sB, _ = skor(te, tB)
    for q, r in enumerate(te):
        n = len(r["lm"]); oA = list(np.argsort(-sA[q, :n])); oB = list(np.argsort(-sB[q, :n]))
        for k in (2, 3, 4, 5):
            if n < k + 2: continue
            base = oA[:k]; X = next(i for i in oB if i not in base); Y = oA[k]
            rest = [i for i in range(n) if i not in base]; Z = int(rng.choice(rest))
            rows.append((r["gun"], k, int(0 in base), int(X == 0), int(Y == 0), int(Z == 0), float(np.exp(r["lm"][X])), int(oA[0] != oB[0]), int(oA[0] == 0)))
    print(a, len(te), "ok", flush=True)
import pandas as pd
D = pd.DataFrame(rows, columns=["gun", "k", "taban", "ek", "Y", "Z", "pmX", "ayr", "A1"])
ug = sorted(D.gun.unique()); out = []
def boot(df, f, B=5000):
    ix = df.groupby("gun").indices; ds = list(ix); r = np.random.default_rng(7); v = []
    for _ in range(B):
        s = r.choice(len(ds), len(ds)); idx = np.concatenate([ix[ds[j]] for j in s]); v.append(f(df.iloc[idx]))
    return np.percentile(v, [2.5, 97.5])
out.append(f"T100: test {D[D.k==3].shape[0]} koşu (k=3), {len(ug)} gün; test ayları {test[0]}..{test[-1]}")
for k in (3, 2, 4, 5):
    d = D[D.k == k]; f = lambda x: x.ek.mean() - x.Y.mean(); lo, hi = boot(d, f)
    fz = lambda x: x.ek.mean() - x.Z.mean(); zl, zh = boot(d, fz)
    out.append(f"{'BİRİNCİL' if k==3 else 'keşifsel'} k={k}: taban kazanan {d.taban.mean():.3f} | ek (piyasasız) {d.ek.mean():.4f} | Y (piyasalı {k+1}. at) {d.Y.mean():.4f} | rastgele ek {d.Z.mean():.4f} | ek−Y {f(d):+.4f} GA95 [{lo:+.4f},{hi:+.4f}] | ek−rastgele {fz(d):+.4f} [{zl:+.4f},{zh:+.4f}] | ek kazanırsa piyasa p(ek) ort {d[d.ek==1].pmX.mean():.3f} vs Y'de {'-'}")
d = D[D.k == 3]; out.append(f"ayrışma (A1≠B1) k=3: koşu {int(d.ayr.sum())} ({d.ayr.mean():.2%}); A'nın 1. atı kazanma ayrışmada {d[d.ayr==1].A1.mean():.3f} diğerlerinde {d[d.ayr==0].A1.mean():.3f}; ek at kazanma ayrışmada {d[d.ayr==1].ek.mean():.4f} diğerlerinde {d[d.ayr==0].ek.mean():.4f}")
open("data/analiz/t100_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
