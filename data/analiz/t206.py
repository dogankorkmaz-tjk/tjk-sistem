"""T206: kör ganyan getirisi oran dilimine göre. Ön kayıt: hipotez_defteri T206. Betimleyici."""
import os, sys, json
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
import numpy as np, pandas as pd
from tjk.golge import _oku
t = _oku("temiz"); t = t[t.kazandi.notna() & t.ganyan.notna()].copy(); t["tarih"] = t.tarih.astype(str)
t = t[(t.ganyan > 0) & (t.ganyan < 1000)]
t["ode"] = np.where(t.kazandi == 1, t.ganyan, 0.0)
B = [0, 1.5, 2, 3, 5, 8, 15, 30, 1e9]; L = ["<1,5", "1,5-2", "2-3", "3-5", "5-8", "8-15", "15-30", ">=30"]
t["dilim_"] = pd.cut(t.ganyan, B, labels=L, right=False)
t["yil"] = np.where(t.tarih < "2024", "2023H2", t.tarih.str[:4])
rng = np.random.default_rng(2060); BB = 5000
def roi(df):
    g = df.groupby("tarih").agg(n=("ode", "size"), o=("ode", "sum")).values
    m = len(g); idx = rng.integers(0, m, (BB, m)); T = g[idx].sum(1)
    return {"bahis": int(g[:, 0].sum()), "kazanma": float((df.ode > 0).mean()), "ROI": float(g[:, 1].sum() / g[:, 0].sum()), "GA95": [float(x) for x in np.percentile(T[:, 1] / T[:, 0], [2.5, 97.5])]}
res = {}
for nm, df in [("tum", t)] + [(y, t[t.yil == y]) for y in sorted(t.yil.unique())]:
    res[nm] = {}
    for l in L:
        s = df[df.dilim_ == l]
        if len(s) >= 200: res[nm][l] = roi(s)
        print(nm, l, json.dumps(res[nm].get(l), ensure_ascii=False) if l in res[nm] else f"n={len(s)} yetersiz", flush=True)
    res[nm]["TUM_ATLAR"] = roi(df); print(nm, "TÜM", json.dumps(res[nm]["TUM_ATLAR"]), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t206.json"), "w"), indent=1, ensure_ascii=False)
