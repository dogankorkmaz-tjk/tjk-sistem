"""Deney: ekipman kodlari (zengin.kod) ve degisimleri, walk-forward. python -m tjk.deney_kod"""
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
    d["tarih"] = d.tarih.astype(str)
    z = _oku("zengin")[O.K + ["no", "kod"]].copy()
    d = d.merge(z, on=O.K + ["no"], how="left")
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    d["rid"] = d.groupby(O.K).ngroup()
    toks = ["DB", "KG", "K", "SK", "SKG", "ÖG", "GKR", "YP", "SGKR"]
    kod = d.kod.fillna("")
    yeni = []
    for t in toks:
        d["k_" + t] = kod.apply(lambda s: float(t in s.split())).values
    g = d.groupby("at")
    for t in toks:
        d["p_" + t] = g["k_" + t].shift(1)
        dif = d["k_" + t] - d["p_" + t]
        d["f_ek_ekle_" + t] = dif.clip(lower=0).fillna(0.0)
        d["f_ek_cikar_" + t] = (-dif).clip(lower=0).fillna(0.0)
        d["f_ek_var_" + t] = d["k_" + t]
        yeni += ["f_ek_ekle_" + t, "f_ek_cikar_" + t, "f_ek_var_" + t]
    d["f_ek_degisim"] = sum(d["f_ek_ekle_" + t] + d["f_ek_cikar_" + t] for t in toks)
    d["f_ek_yok"] = kod.eq("").astype(float)
    yeni += ["f_ek_degisim", "f_ek_yok"]
    d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
    base = M["feat"] + EK + LPEK
    rows = []
    for k in [x for x in sorted(d.q.unique()) if x >= "2025Q3"]:
        te0 = d[d.q == k]
        tr = d[d.tarih < te0.tarih.min()]
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
        te["rid"] = te.groupby(O.K).ngroup()
        for ad, feat in (("J", base), ("JK", base + yeni)):
            th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
            te["p_" + ad] = skorla(te, feat, th, mu, sd)
        w = te[te.kazandi == 1]
        a = np.log(w.p_J) - np.log(w.p_piyasa); b = np.log(w.p_JK) - np.log(w.p_piyasa)
        rows.append(pd.DataFrame({"fold": k, "j": a.values, "jk": b.values}))
        print(k, len(w), round(a.mean(), 4), round(b.mean(), 4), flush=True)
    R = pd.concat(rows); dd = R.jk - R.j
    out = {"kosu": int(len(R)), "jason": float(R.j.mean()), "jason_kod": float(R.jk.mean()), "fark": float(dd.mean()), "fark_se": float(dd.std(ddof=1) / np.sqrt(len(dd)))}
    print(out)
    json.dump(out, open(os.path.join(KOK, "data", "analiz", "deney_kod.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
