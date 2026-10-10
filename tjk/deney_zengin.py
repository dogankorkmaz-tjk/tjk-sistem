"""Deney: Jason + zengin (at basina fark/ekipman) ozellikleri, walk-forward. Kullanim: python -m tjk.deney_zengin"""
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
    z = _oku("zengin")[O.K + ["no", "sira", "fark_boy"]].copy()
    z = z.sort_values(O.K + ["sira"])
    z["fark_boy"] = z.fark_boy.fillna(0.0)
    z["bl"] = z.groupby(O.K).fark_boy.cumsum()           # kazanana kac boy geride
    d = d.merge(z[O.K + ["no", "bl"]], on=O.K + ["no"], how="left")
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    d["rid"] = d.groupby(O.K).ngroup()
    d["blc"] = np.log1p(d.bl.clip(upper=25))
    g = d.groupby("at")
    d["bl_son"] = g.blc.shift(1)
    d["bl_3"] = g.blc.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    d["f_bl_yok"] = d.bl_son.isna().astype(float)
    d["f_bl_son"] = d.bl_son.fillna(d.bl_son.mean()) - d.bl_son.mean()
    d["f_bl_3"] = d.bl_3.fillna(d.bl_3.mean()) - d.bl_3.mean()
    # aynı koşudaki rakiplere göre göreli (alan ortalamasından)
    for c in ("f_bl_son", "f_bl_3"):
        d[c] = d[c] - d.groupby("rid")[c].transform("mean")
    base = M["feat"] + EK + LPEK
    yeni = ["f_bl_son", "f_bl_3", "f_bl_yok"]
    d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
    rows = []
    for k in [x for x in sorted(d.q.unique()) if x >= "2025Q3"]:
        te0 = d[d.q == k]
        tr = d[d.tarih < te0.tarih.min()]
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
        te["rid"] = te.groupby(O.K).ngroup()
        for ad, feat in (("Jason", base), ("Jason_zengin", base + yeni)):
            th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
            te["p_" + ad] = skorla(te, feat, th, mu, sd)
        w = te[te.kazandi == 1]
        a = np.log(w.p_Jason) - np.log(w.p_piyasa); b = np.log(w.p_Jason_zengin) - np.log(w.p_piyasa)
        rows.append(pd.DataFrame({"fold": k, "j": a.values, "jz": b.values}))
        print(k, len(w), round(a.mean(), 4), round(b.mean(), 4), "fark", round((b - a).mean(), 4), flush=True)
    R = pd.concat(rows)
    dd = R.jz - R.j
    out = {"kosu": int(len(R)), "jason": float(R.j.mean()), "jason_zengin": float(R.jz.mean()),
           "fark": float(dd.mean()), "fark_se": float(dd.std(ddof=1) / np.sqrt(len(dd)))}
    print(out)
    json.dump(out, open(os.path.join(KOK, "data", "analiz", "deney_zengin.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
