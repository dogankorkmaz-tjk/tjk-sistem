"""AGF hareketi bilgilendirici mi, gruplar arası. Ön kayıt: hipotez_defteri 2026-10-24 21:15."""
import numpy as np, pandas as pd
from scipy.optimize import minimize
d = pd.read_csv("data/nalsesleri/gecmis.csv.gz")
d = d[(d.race_date >= "2024-01-01") & d.AGF1.notna() & d.AGF2.notna() & d.odds.notna() & d.result.notna() & (d.AGF1 > 0.3) & (d.AGF2 > 0.3) & (d.non_runner != 1) & (d.odds > 1)]
A = {"ELAZIG", "SANLIURFA", "DBAKIR", "DIYARBAKIR"}; B = {"ISTANBUL", "ANKARA", "IZMIR", "ADANA", "BURSA", "KOCAELI", "ANTALYA"}
d = d[d.hippodrome_id.isin(A | B)].copy(); d["g"] = d.hippodrome_id.isin(A).astype(int)
d["x1"] = np.log(1 / d.odds); d["x2"] = np.log(d.AGF2 / d.AGF1).clip(-1.5, 1.5); d["y"] = (d.result == 1).astype(int)
print("n", len(d), "A", d.g.sum(), "B", (1 - d.g).sum(), "kazanan oranı A %.3f B %.3f" % (d[d.g == 1].y.mean(), d[d.g == 0].y.mean()))
def fit(x):
    X = np.c_[np.ones(len(x)), x.x1, x.x2]; y = x.y.values
    def f(t):
        z = X @ t; p = 1 / (1 + np.exp(-z)); return -(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12)).sum(), X.T @ (p - y)
    return minimize(f, np.r_[-1.0, 0.0, 0.0], jac=True, method="L-BFGS-B").x
tA, tB = fit(d[d.g == 1]), fit(d[d.g == 0]); print("A: a %.3f b(log 1/oran) %.3f c(AGF hareketi) %.3f" % tuple(tA)); print("B: a %.3f b %.3f c %.3f" % tuple(tB))
gun = sorted(d.race_date.unique()); by = {g: d[d.race_date == g] for g in gun}; rng = np.random.default_rng(1); bs = []
for _ in range(300):
    S = pd.concat([by[g] for g in rng.choice(gun, len(gun))]); sa, sb = S[S.g == 1], S[S.g == 0]
    if len(sa) < 200 or len(sb) < 200: continue
    bs.append(fit(sa)[2] - fit(sb)[2])
print("c_A − c_B = %.3f, %%95 GA [%.3f, %.3f]" % (tA[2] - tB[2], *np.percentile(bs, [2.5, 97.5])))
cA, cB = [], []
for _ in range(300):
    S = pd.concat([by[g] for g in rng.choice(gun, len(gun))]); cA.append(fit(S[S.g == 1])[2]); cB.append(fit(S[S.g == 0])[2])
print("c_A %%95 GA [%.3f, %.3f] | c_B [%.3f, %.3f]" % (*np.percentile(cA, [2.5, 97.5]), *np.percentile(cB, [2.5, 97.5])))
