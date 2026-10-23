"""Model yapısı deneyi 1: yalnız kazanan mı (K=1), yoksa tam sıralama (patlatılmış logit, ilk 3) mı ile eğitim?
Ve sonraki sıralar için Henery/Lo-Bacon-Shone benzeri üs (gamma2, gamma3) gerekli mi? Walk-forward 2025-01+.
Ölçütler (nats/koşu, düşük iyi): kazanan, sıralı ikili (1-2), sıralı üçlü (1-2-3). Çalıştırma: python3 data/analiz/model_yapisi_1.py"""
import os, sys, datetime as dt, random
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import g1
rows = list(g1._satirlar()); K = {}
for r in rows: K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
H, J, AJ = {}, {}, {}; R = []
for key in sorted(K):
    ok = [r for r in K[key] if r["kosmadi"] != "True" and g1._fl(r["ganyan"], 0) > 1 and g1._fl(r["sira"], 0) > 0]
    n = len(ok)
    if n < 4: continue
    ok.sort(key=lambda r: g1._fl(r["sira"]))
    if [g1._fl(r["sira"]) for r in ok[:3]] != [1.0, 2.0, 3.0]: continue
    inv = np.array([1 / g1._fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
    R.append(dict(ay=key[0][:7], gun=key[0], lm=np.log(pm), X=g1._oz(H, J, AJ, ok, pm, gun)))   # sıralı: 0,1,2 = ilk üç
    for i, r in enumerate(ok):
        pct = 1 - (g1._fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == 0 else 0.0
        H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
        j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
        a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
print("koşu", len(R)); M = max(len(r["lm"]) for r in R)
def pack(rl):
    N = len(rl); LM = np.full((N, M), -1e9); XX = np.zeros((N, M, 9))
    for k, r in enumerate(rl): n = len(r["lm"]); LM[k, :n] = r["lm"]; XX[k, :n] = r["X"]
    return LM, XX
def adimlar(th, LM, XX, steps, gam):
    """s = alfa*lm + X b ; adım j (0,1,2) logit: gam[j]*s üzerinden kalan atlar. Döner (nll listesi [adım], d gradyan parçaları)"""
    a, b = th[0], th[1:10]; s = a * LM + XX @ b; N = len(LM); idx = np.arange(N)
    mask = np.ones_like(s, bool); mask[LM < -1e8] = False; out = []; ds = np.zeros_like(s); dg = np.zeros(3)
    for j in range(steps):
        z = np.where(mask, gam[j] * s, -1e30); z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
        out.append(-np.log(p[idx, j] + 1e-12)); d = p.copy(); d[idx, j] -= 1
        ds += gam[j] * d; dg[j] = (d * np.where(mask, s, 0)).sum()
        mask[idx, j] = False
    return out, ds, dg
def fit(rl, steps, free, l2=30.0):
    LM, XX = pack(rl)
    def f(t):
        gam = np.array([1.0, t[10] if free else 1.0, t[11] if free else 1.0])
        out, ds, dg = adimlar(t, LM, XX, steps, gam)
        L = sum(o.sum() for o in out) + l2 * (t[1:10] @ t[1:10])
        g = np.zeros(12); g[0] = (ds * LM.clip(-50, 0)).sum(); g[1:10] = np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10]
        if free: g[10:12] = dg[1:3]
        return L, g
    t0 = np.zeros(12); t0[0] = 1; t0[10] = t0[11] = 1
    return minimize(f, t0, jac=True, method="L-BFGS-B").x
def ol(th, rl, free):
    LM, XX = pack(rl); gam = np.array([1.0, th[10] if free else 1.0, th[11] if free else 1.0])
    out, _, _ = adimlar(th, LM, XX, 3, gam); return np.array(out)    # 3×N adım nll
MOD = {"piyasa (Harville)": None, "K=1 kazanan": (1, False), "K=3 patlatılmış": (3, False), "K=3 + gamma": (3, True)}
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2025-01"]
res = {k: [] for k in MOD}; gun = []
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]; gun += [r["gun"] for r in te]
    for k, v in MOD.items():
        if v is None:
            th = np.zeros(12); th[0] = 1; th[10] = th[11] = 1; res[k].append(ol(th, te, False))
        else:
            th = fit(tr, *v); res[k].append(ol(th, te, v[1]))
        if a == test[-1] and v: print(k, "alfa %.3f" % th[0], "gamma2/3", np.round(th[10:], 3) if v[1] else "-")
gun = np.array(gun); ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}; random.seed(5)
base = np.concatenate(res["piyasa (Harville)"], axis=1)
print(f"test {base.shape[1]} koşu, {len(ug)} gün; ölçüt: kazanan | sıralı ikili | sıralı üçlü (nats/koşu; farklar piyasaya göre)")
for k in MOD:
    L = np.concatenate(res[k], axis=1); cum = [L[0], L[:2].sum(0), L.sum(0)]; bc = [base[0], base[:2].sum(0), base.sum(0)]
    s = f"{k:20s}"
    for c, b in zip(cum, bc):
        d = c - b; bs = [d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(600)]
        s += f" | {c.mean():.4f} ({d.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}])"
    print(s)
