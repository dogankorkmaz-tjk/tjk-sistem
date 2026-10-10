"""Deney: antrenor/sahip/baba artik ozellikleri (2) ve hipodrom/alan buyuklugu/mesafe-piyasa etkilesimleri (3), walk-forward.
python -m tjk.deney_ozellik2  -> data/analiz/deney_ozellik2.json"""
import os, json
import numpy as np, pandas as pd
from . import ortak as O
from .ozellik import hazirla
from . import mesafe as MS
from .golge import _fit, _oku, EK, LPEK
from .calistir import yukle_model
from .walkforward import skorla

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def artik(d, anahtar, M, ad):
    """anahtar grubunun ONCEKI GUNLERDEKI kumulatif (kazandi - p_piyasa) artigi, M ile kuculterek."""
    d = d.copy(); d["_r"] = d.kazandi - d.p_piyasa
    key = anahtar if isinstance(anahtar, list) else [anahtar]
    g = d.groupby(key + ["tarih"]).agg(n=("_r", "size"), r=("_r", "sum")).reset_index().sort_values("tarih")
    g["cn"] = g.groupby(key).n.cumsum() - g.n; g["cr"] = g.groupby(key).r.cumsum() - g.r
    g[ad] = g.cr / (g.cn + M)
    return d[key + ["tarih"]].merge(g[key + ["tarih", ad]], on=key + ["tarih"], how="left")[ad].fillna(0.0).values


def main():
    M = yukle_model()
    d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    d = d[d.temiz & d.kazandi.notna() & d.lp.notna()].copy()
    d["tarih"] = d.tarih.astype(str)
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    d["rid"] = d.groupby(O.K).ngroup()
    for c in ("antrenor", "sahip", "baba", "jokey"):
        d[c] = d[c].fillna("?")
    A = []
    for ad, key, m in (("f_ant", "antrenor", 100), ("f_sahip", "sahip", 100), ("f_baba", "baba", 150),
                       ("f_jant", ["jokey", "antrenor"], 60), ("f_anthip", ["antrenor", "hipodrom"], 80), ("f_jhip", ["jokey", "hipodrom"], 80)):
        d[ad] = artik(d, key, m, ad); A.append(ad)
    # (3) piyasa etkilesimleri
    lp = d.lp
    top = d.hipodrom.value_counts().index[:6]
    I = []
    for h in top:
        d["f_lpx_" + h] = lp * (d.hipodrom == h); I.append("f_lpx_" + h)
    d["f_lpx_n"] = lp * np.log(d.n_at); I.append("f_lpx_n")
    if "mesafe" in d:
        d["f_lpx_mes"] = lp * ((d.mesafe.fillna(1400) - 1400) / 600.0); I.append("f_lpx_mes")
    d["f_lpx_apr"] = lp * d.apranti.astype(float); I.append("f_lpx_apr")
    d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
    base = M["feat"] + EK + LPEK
    setler = {"J": base, "J+artik": base + A, "J+etkilesim": base + I, "J+hepsi": base + A + I}
    for a in A:
        setler["J+" + a] = base + [a]
    R = {k: [] for k in setler}; PM = []
    for k in [x for x in sorted(d.q.unique()) if x >= "2025Q1"]:
        te0 = d[d.q == k]; tr = d[d.tarih < te0.tarih.min()]
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup()
        for ad, feat in setler.items():
            th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
            te["p"] = skorla(te, feat, th, mu, sd)
            w = te[te.kazandi == 1]
            R[ad].append((np.log(w.p) - np.log(w.p_piyasa)).values)
        print(k, flush=True)
    base_v = np.concatenate(R["J"]); out = {}
    for ad in setler:
        v = np.concatenate(R[ad]); dd = v - base_v
        out[ad] = {"ort": float(v.mean()), "fark": float(dd.mean()), "fark_se": float(dd.std(ddof=1) / np.sqrt(len(dd))) if ad != "J" else None}
        print(ad, {k: (round(x, 5) if x is not None else None) for k, x in out[ad].items()})
    json.dump(out, open(os.path.join(KOK, "data", "analiz", "deney_ozellik2.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
