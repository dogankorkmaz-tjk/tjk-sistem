"""Deney: hız figürü (normalize derece) varyantları, Jason + yeni özellikler, walk-forward. Kullanım: python -m tjk.deney_hiz
Mevcut f_fig3 (rel_sure, gün/pist farkına göre düzeltilmiş, son 3 ortalama) zaten Jason'da. Burada eklenenler:
 - mutlak figür: derece / (hipodrom, mesafe, pist) ölçüt süresi (önceki günlerin ilk-yarı ortalaması), gün/pist varyantı düşülmüş
 - son koşu, son 5 en iyi, son 5 ortalama figür; alan içi göreli."""
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
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    d["rid"] = d.groupby(O.K).ngroup()
    t = d.derece_sn.astype(float)
    ok = t.notna() & (t > 20) & d.mesafe.notna()
    d["grp"] = d.hipodrom.astype(str) + "|" + d.mesafe.astype(str) + "|" + d.pist.astype(str)
    ust = ok & (d.pct <= 0.5)
    g = d[ust].assign(t=t[ust]).groupby(["grp", "tarih"]).agg(n=("t", "size"), s=("t", "sum")).reset_index().sort_values("tarih")
    g["cn"] = g.groupby("grp").n.cumsum() - g.n; g["cs"] = g.groupby("grp").s.cumsum() - g.s
    g["std"] = np.where(g.cn >= 8, g.cs / g.cn.clip(lower=1), np.nan)
    d = d.merge(g[["grp", "tarih", "std"]], on=["grp", "tarih"], how="left")
    raw = np.where(ok & d["std"].notna(), -(t / d["std"] - 1) * 100, np.nan)
    d["raw"] = raw
    k = d.tarih + "|" + d.hipodrom.astype(str) + "|" + d.pist.astype(str)
    sm = d.groupby(k).raw.transform("sum"); sc = d.groupby(k).raw.transform("count")
    d["fig"] = d.raw - (sm - d.raw.fillna(0)) / (sc - d.raw.notna()).clip(lower=1)
    d["fig"] = d.fig.clip(-6, 6)
    gg = d.groupby("at").fig
    d["fg_son"] = gg.shift(1)
    d["fg_ort5"] = gg.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    d["fg_en5"] = gg.transform(lambda s: s.shift(1).rolling(5, min_periods=1).max())
    yeni = []
    for c in ("fg_son", "fg_ort5", "fg_en5"):
        d["f_" + c + "_yok"] = d[c].isna().astype(float)
        mu = d[c].mean()
        d["f_" + c] = d[c].fillna(mu) - mu
        d["f_" + c] = d["f_" + c] - d.groupby("rid")["f_" + c].transform("mean")
        yeni += ["f_" + c, "f_" + c + "_yok"]
    print("figür kapsamı:", float(d.fg_son.notna().mean()), flush=True)
    base = M["feat"] + EK + LPEK
    d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
    rows = []
    for kq in [x for x in sorted(d.q.unique()) if x >= "2025Q3"]:
        te0 = d[d.q == kq]
        tr = d[d.tarih < te0.tarih.min()]
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
        te["rid"] = te.groupby(O.K).ngroup()
        for ad, feat in (("Jason", base), ("Jason_hiz", base + yeni)):
            th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
            te["p_" + ad] = skorla(te, feat, th, mu, sd)
        w = te[te.kazandi == 1]
        a = np.log(w.p_Jason) - np.log(w.p_piyasa); b = np.log(w.p_Jason_hiz) - np.log(w.p_piyasa)
        rows.append(pd.DataFrame({"fold": kq, "j": a.values, "jh": b.values}))
        print(kq, len(w), round(a.mean(), 4), round(b.mean(), 4), "fark", round((b - a).mean(), 4), flush=True)
    R = pd.concat(rows); dd = R.jh - R.j
    out = {"kosu": int(len(R)), "jason": float(R.j.mean()), "jason_hiz": float(R.jh.mean()),
           "fark": float(dd.mean()), "fark_se": float(dd.std(ddof=1) / np.sqrt(len(dd)))}
    print(out)
    json.dump(out, open(os.path.join(KOK, "data", "analiz", "deney_hiz.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
