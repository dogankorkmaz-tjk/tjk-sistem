"""T101: Jason z2, G1-S v2'ye bilgi ekliyor mu? (ön kayıt hipotez_defteri T101). python3 data/analiz/t101_z2_ekle.py"""
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
P = []   # (gun, ay, s, z2, gam)
eslesen = 0; toplam = 0
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
    LM, XX, FF = pack(te, True); S = np.where(LM > -1e8, t1[0] * LM + XX @ t1[1:10], -1e9)
    b, mu, sd = bg; S = S + ((FF - mu) / sd) @ b
    for q, r in enumerate(te):
        n = len(r["lm"]); z = []
        for no in r["nos"]:
            key = (r["key"][0], r["key"][1], int(r["key"][2]), int(no)); toplam += 1
            if key in Z2: eslesen += 1; z.append(Z2[key])
            else: z.append(0.0)
        P.append((r["gun"], r["ay"], S[q, :n].copy(), np.array(z), t1[10:14].copy()))
    print("v2", a, len(te), flush=True)
print(f"z2 eşleşme {eslesen}/{toplam} = {eslesen/toplam:.3f}", flush=True)
def ll(s, j=1, gam=None):
    s = s.copy(); out = 0.0; ch = []
    for q in range(j):
        g = 1.0 if q == 0 else gam[q - 1]; z = g * s; m = np.max(np.where(np.isin(np.arange(len(s)), ch), -1e30, z))
        e = np.exp(np.where(np.isin(np.arange(len(s)), ch), -1e30, z) - m); out += -(z[q] - m - np.log(e.sum())); ch.append(q)
    return out
def fitb(L):
    def f(b):
        t = 0.0
        for _, _, s, z, _g in L: x = s + b[0] * z; t += -(x[0] - np.max(x) - np.log(np.exp(x - np.max(x)).sum()))
        return t + 1.0 * b[0] ** 2
    return minimize(f, [0.0], method="L-BFGS-B").x[0]
rows = []; bler = {}
for a in test[1:]:
    L = [p for p in P if p[1] < a]; bb = fitb(L); bler[a] = bb
    for gun, ay, s, z, gam in [p for p in P if p[1] == a]:
        c = s + bb * z
        rows.append((gun, ay, ll(s, 1), ll(c, 1), ll(s, 3, gam), ll(c, 3, gam)))
D = pd.DataFrame(rows, columns=["gun", "ay", "v2k", "Ck", "v23", "C3"])
ix = D.groupby("gun").indices; ds = list(ix); rr = np.random.default_rng(11)
def boot(col):
    v = []
    for _ in range(5000):
        s = rr.choice(len(ds), len(ds)); idx = np.concatenate([ix[ds[j]] for j in s]); v.append((D[col[0]].values[idx] - D[col[1]].values[idx]).mean())
    return np.percentile(v, [2.5, 97.5])
out = [f"T101: değerlendirme {len(D)} koşu, {len(ds)} gün ({test[1]}..{test[-1]}); z2 eşleşme {eslesen/toplam:.3f}"]
for ad, col in (("BİRİNCİL kazanan", ("v2k", "Ck")), ("keşifsel ilk-3", ("v23", "C3"))):
    lo, hi = boot(col); out.append(f"{ad}: v2 {D[col[0]].mean():.4f}  C {D[col[1]].mean():.4f}  v2−C {(D[col[0]]-D[col[1]]).mean():+.5f} nats/koşu GA95 [{lo:+.5f},{hi:+.5f}]")
out.append("b (ay: değer): " + ", ".join(f"{a}: {v:+.3f}" for a, v in bler.items()))
cs = [];
for p in P:
    s = p[2] - p[2].mean(); z = p[3] - p[3].mean()
    if s.std() > 0 and z.std() > 0: cs.append(np.corrcoef(s, z)[0, 1])
out.append(f"ort. koşu-içi korelasyon (s_v2, z2): {np.mean(cs):.3f}")
open("data/analiz/t101_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
