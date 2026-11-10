"""T196: T195 PL gücü (EP) vs Elo kolu (E): GANYAN değer-bahsi ROI'si. Ön kayıt: hipotez_defteri T196. Actions: t196.yml."""
import os, sys, json
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(KOK, "data", "analiz", "t195.py")).read().split('if os.environ.get("T195_DEBUG")')[0]
exec(compile(src, "t195head", "exec"))                      # d (f_pl, f_elo ...), M, _fit, skorla, EK, LPEK, EL, np, pd
from tjk import komiser as KM
import glob
base = M["feat"] + EK + LPEK; E = base + EL.EXTRA_FEAT
kollar = {"E": E, "EP": E + ["f_pl"]}
G = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))]); G = G[G.tur == "GANYAN"]
ODE = {(r.tarih, r.hipodrom, int(r.kosu), str(r.kombo)): float(r.tutar) for r in G.itertuples()}
TR2A = {v: k for k, v in KM.ASCII.items()}
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str); rows = []
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q3"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
    for ad, feat in kollar.items():
        th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0)); te["p_" + ad] = skorla(te, feat, th, mu, sd)
    rows.append(te[["tarih", "hipodrom", "kosu", "no", "kazandi", "p_piyasa", "p_E", "p_EP"]]); print(kq, len(te), flush=True)
R = pd.concat(rows, ignore_index=True)
R["ode"] = [ODE.get((t, TR2A.get(h, h), int(k), str(n)), 0.0) if kz == 1 else 0.0 for t, h, k, n, kz in zip(R.tarih, R.hipodrom, R.kosu, R.no, R.kazandi)]
print("koşu ödemesi bulunamayan kazanan:", int(((R.kazandi == 1) & (R.ode == 0)).sum()), "/", int((R.kazandi == 1).sum()), flush=True)
rng = np.random.default_rng(1960); B = 5000
def gun_mat(sec):
    g = R[sec].assign(b=1.0).groupby("tarih").agg(b=("b", "sum"), o=("ode", "sum")); return g
def ozet(ad, esik, pmin=0.10):
    sec = ((R["p_" + ad] / R.p_piyasa) >= esik) & (R["p_" + ad] >= pmin); g = gun_mat(sec); return sec, g
def roi_ga(g, lo=2.5, hi=97.5):
    gun = g.index.values; M_ = g[["b", "o"]].values; n = len(M_); idx = rng.integers(0, n, (B, n)); S = M_[idx].sum(1)
    return M_[:, 1].sum() / M_[:, 0].sum() - 1, np.percentile(S[:, 1] / S[:, 0] - 1, [lo, hi]), int(M_[:, 0].sum()), int((R.loc[sec, "ode"] > 0).sum())
sonuc = {}
for esik in (1.15, 1.10, 1.25):
    for ad in ("E", "EP"):
        sec, g = ozet(ad, esik); r, ga, n, hit = roi_ga(g); sonuc[f"{ad}_{esik}"] = [r, list(ga), n, hit]
        print(f"esik {esik} {ad:3s} bahis {n:6d} isabet {hit:5d} ROI {r:+.1%} [{ga[0]:+.1%};{ga[1]:+.1%}]", flush=True)
# eşleştirilmiş fark (ANA, esik 1,15): gün-kümeli
a = ozet("E", 1.15)[1]; b = ozet("EP", 1.15)[1]; days = sorted(set(a.index) | set(b.index))
A = a.reindex(days, fill_value=0).values; Bm = b.reindex(days, fill_value=0).values; n = len(days); idx = rng.integers(0, n, (B, n))
SA = A[idx].sum(1); SB = Bm[idx].sum(1); fark = SB[:, 1] / SB[:, 0] - SA[:, 1] / SA[:, 0]
nokta = Bm[:, 1].sum() / Bm[:, 0].sum() - A[:, 1].sum() / A[:, 0].sum(); ga = np.percentile(fark, [2.5, 97.5])
print(f"ANA fark ROI(EP)−ROI(E): {nokta:+.2%} [{ga[0]:+.2%};{ga[1]:+.2%}]")
ADAY = nokta >= 0
print("KARAR:", "ADAY (G1-S v4, ileri kayıt)" if ADAY else "YOK")
sonuc["fark_ANA"] = [nokta, list(ga)]; json.dump(sonuc, open(os.path.join(KOK, "data", "analiz", "t196.json"), "w"), indent=1)
