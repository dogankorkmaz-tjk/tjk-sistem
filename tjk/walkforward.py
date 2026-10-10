"""Walk-forward test: Bolton ve Jason ozellikleri her ceyrekte yalnizca ONCEKI veriyle yeniden egitilir, sonraki ceyrekte piyasaya karsi sinanir.
Kullanim: python -m tjk.walkforward  -> data/analiz/walkforward.json
Not: dondurulmus model_v1 agirliklari kullanilmaz (7 Ekim'e kadar tum veriyi gordu); yalnizca ozellik kumeleri ayni, agirliklar her kat icin yeniden fit edilir."""
import os, json, sys
import numpy as np, pandas as pd
from . import ortak as O
from .ozellik import hazirla
from . import mesafe as MS
from .golge import _fit, _oku, EK, LPEK
from .calistir import yukle_model

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def skorla(te, feat, th, mu, sd):
    X = ((te[feat] - mu) / sd).values
    s = th[0] * te.lp.values + X @ th[1:]
    te = te.assign(s=s)
    e = np.exp(s - te.groupby("rid").s.transform("max").values)
    return e / pd.Series(e, index=te.index).groupby(te.rid).transform("sum").values


def main():
    M = yukle_model()
    d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    d = d[d.temiz & d.kazandi.notna() & d.lp.notna()].copy()
    d["tarih"] = d.tarih.astype(str)
    d["rid"] = d.groupby(O.K).ngroup()
    d["ganyan_son"] = 1.0 / d.p_ham  # son muhtemel ganyan
    feats = {"Bolton": M["feat"], "Jason": M["feat"] + EK + LPEK}
    q = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q")
    d["q"] = q.astype(str)
    kats = [x for x in sorted(d.q.unique()) if x >= "2024Q2"]
    out = {"kat": [], "yontem": "ceyreklik expanding window; test: kazanan log-olasiligi (model - piyasa), EV>esik ROI (son muhtemel ganyanla)"}
    rows = []
    for k in kats:
        te0 = d[d.q == k]
        tr = d[d.tarih < te0.tarih.min()]
        if tr.rid.nunique() < 5000:
            continue
        te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
        te["rid"] = te.groupby(O.K).ngroup()
        for ad, feat in feats.items():
            th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
            te["p_" + ad] = skorla(te, feat, th, mu, sd)
        te["fold"] = k
        rows.append(te[["fold", "tarih", "hipodrom", "kosu", "no", "kazandi", "p_piyasa", "p_Bolton", "p_Jason", "ganyan_son"]])
        w = te[te.kazandi == 1]
        r = {"fold": k, "kosu": int(len(w))}
        for ad in ("Bolton", "Jason"):
            diff = np.log(w["p_" + ad]) - np.log(w.p_piyasa)
            r[ad + "_kazanc"] = float(diff.mean()); r[ad + "_se"] = float(diff.std(ddof=1) / np.sqrt(len(diff)))
        out["kat"].append(r)
        print(r, flush=True)
    R = pd.concat(rows, ignore_index=True)
    w = R[R.kazandi == 1]
    out["toplam"] = {"kosu": int(len(w))}
    for ad in ("Bolton", "Jason"):
        diff = np.log(w["p_" + ad]) - np.log(w.p_piyasa)
        out["toplam"][ad] = {"ll_kazanc_ort": float(diff.mean()), "se": float(diff.std(ddof=1) / np.sqrt(len(diff))),
                             "kosu_pozitif_orani": float((diff > 0).mean())}
        ev = R["p_" + ad] * R.ganyan_son
        roi = []
        for esik in (1.0, 1.1, 1.2, 1.3, 1.5):
            m = ev > esik
            ret = R[m].kazandi * R[m].ganyan_son - 1
            roi.append({"esik": esik, "bahis": int(m.sum()), "roi": float(ret.mean()) if m.sum() else None,
                        "se": float(ret.std(ddof=1) / np.sqrt(m.sum())) if m.sum() > 1 else None})
        out["toplam"][ad]["ev_roi"] = roi
    yol = os.path.join(KOK, "data", "analiz", "walkforward.json")
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    json.dump(out, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["toplam"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
