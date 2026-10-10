"""Deney: jokey-at uyumu (cift artigi, jokey degisimi, jokey yukselisi). python -m tjk.deney_jokey_at"""
import os, json
import numpy as np, pandas as pd
from . import ortak as O
from .ozellik import hazirla
from . import mesafe as MS
from .golge import _fit, _oku, EK, LPEK
from .calistir import yukle_model
from .walkforward import skorla
from .deney_ozellik2 import artik

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    M = yukle_model()
    d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    d = d[d.temiz & d.kazandi.notna() & d.lp.notna()].copy()
    d["tarih"] = d.tarih.astype(str)
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    d["rid"] = d.groupby(O.K).ngroup(); d["jokey"] = d.jokey.fillna("?")
    d["f_jat"] = artik(d, ["jokey", "at"], 10, "f_jat")                     # bu jokeyin bu ata onceki binislerinde piyasa artigi
    gk = d.groupby("at")
    onc = gk.jokey.shift(1)
    d["f_jdeg"] = ((onc.notna()) & (onc != d.jokey)).astype(float)         # jokey degisti
    d["f_jyuk"] = (d.f_jgen100 - gk.f_jgen100.shift(1)).fillna(0.0)         # jokey kalitesi son kosuya gore degisimi
    d["f_jat_n"] = np.log1p(d.groupby(["jokey", "at"]).cumcount())          # birlikte kosu sayisi (deneyim)
    yeni = ["f_jat", "f_jdeg", "f_jyuk", "f_jat_n"]
    d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
    base = M["feat"] + EK + LPEK
    setler = {"J": base, "J+hepsi": base + yeni}
    for a in yeni: setler["J+" + a] = base + [a]
    R = {k: [] for k in setler}
    for k in [x for x in sorted(d.q.unique()) if x >= "2025Q1"]:
        te0 = d[d.q == k]; tr = d[d.tarih < te0.tarih.min()]
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup()
        for ad, feat in setler.items():
            th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
            te["p"] = skorla(te, feat, th, mu, sd); w = te[te.kazandi == 1]
            R[ad].append((np.log(w.p) - np.log(w.p_piyasa)).values)
    b = np.concatenate(R["J"]); out = {}
    for ad in setler:
        v = np.concatenate(R[ad]); dd = v - b
        out[ad] = {"ort": float(v.mean()), "fark": float(dd.mean()), "se": float(dd.std(ddof=1) / np.sqrt(len(dd)))}
        print(ad, {k: round(x, 5) for k, x in out[ad].items()}, flush=True)
    json.dump(out, open(os.path.join(KOK, "data", "analiz", "deney_jokey_at.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
