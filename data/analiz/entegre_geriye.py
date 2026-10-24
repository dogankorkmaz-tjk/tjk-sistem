"""Entegre model (G1-S v2) ileri-yürüyüş testi. Ön kayıt: hipotez_defteri 2026-10-24 11:35. Çalıştırma: python3 data/analiz/entegre_geriye.py"""
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
    R.append(dict(gun=key[0], ay=key[0][:7], lm=np.log(pm), X=X, F=F))
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
def piyasa_gamma(rl):                                    # özellik yok: yalnız alfa + gamma (b≈0)
    return fit1(rl, 1e9)
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]
res = {"piyasa+gamma": [], "G1-S": [], "G1-S v2": []}; gun = []
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
    res["piyasa+gamma"].append(evalm(te, tp)); res["G1-S"].append(evalm(te, t1)); res["G1-S v2"].append(evalm(te, t1, bg)); gun += [r["gun"] for r in te]
    print(a, len(te), "ok", flush=True)
gun = np.array(gun); ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}; random.seed(4)
C = {k: np.cumsum(np.concatenate(v, axis=1), axis=0) for k, v in res.items()}      # kümülatif adım: 1, 1-2, ..., 1-5
AD = ["kazanan", "sıralı ikili", "sıralı üçlü", "ilk 4 (tabela)", "ilk 5 (sıralı 5'li)"]
print(f"test {len(gun)} koşu, {len(ug)} gün; log-kayıp nats/koşu (ortalama) ve farklar [GA]")
def fark(a, b, j):
    d = C[a][j] - C[b][j]; bs = [d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(800)]
    return f"{d.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]"
for j, ad in enumerate(AD):
    print(f"{ad:20s} piyasa+gamma {C['piyasa+gamma'][j].mean():.4f} | G1-S {C['G1-S'][j].mean():.4f} | v2 {C['G1-S v2'][j].mean():.4f} || G1-S−pg {fark('G1-S','piyasa+gamma',j)} || v2−G1-S {fark('G1-S v2','G1-S',j)} || v2−pg {fark('G1-S v2','piyasa+gamma',j)}")
