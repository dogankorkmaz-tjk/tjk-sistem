"""Deney: Jason icin L2 duzenleme (lam) taramasi, walk-forward. python -m tjk.deney_lam"""
import os, json
import numpy as np, pandas as pd
from . import ortak as O
from .ozellik import hazirla
from . import mesafe as MS
from .golge import _fit, _oku, EK, LPEK
from .calistir import yukle_model
from .walkforward import skorla

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    M = yukle_model()
    d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    d = d[d.temiz & d.kazandi.notna() & d.lp.notna()].copy()
    d["tarih"] = d.tarih.astype(str); d["rid"] = d.groupby(O.K).ngroup()
    d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
    feat = M["feat"] + EK + LPEK
    lams = [10.0, 30.0, 100.0, 300.0, 1000.0]
    R = {l: [] for l in lams}
    for k in [x for x in sorted(d.q.unique()) if x >= "2025Q1"]:
        te0 = d[d.q == k]; tr = d[d.tarih < te0.tarih.min()]
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup()
        for l in lams:
            th, mu, sd, nk = _fit(tr, feat, l)
            p = skorla(te, feat, th, mu, sd); te["p"] = p
            w = te[te.kazandi == 1]
            R[l].append((np.log(w.p) - np.log(w.p_piyasa)).values)
    out = {}
    for l in lams:
        a = np.concatenate(R[l]); out[str(l)] = {"ort": float(a.mean()), "se": float(a.std(ddof=1) / np.sqrt(len(a))), "n": int(len(a))}
        print(l, out[str(l)])
    json.dump(out, open(os.path.join(KOK, "data", "analiz", "deney_lam.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
