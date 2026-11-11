"""T203: zayıf piyasa bölgesi (bölüm bazlı log-olabilirlik kazancı). Ön kayıt: hipotez_defteri T203. Actions: t203.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json, glob
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d, M, O, _fit, skorla, EK, LPEK, np, pd = [_ns[k] for k in ("d", "M", "O", "_fit", "skorla", "EK", "LPEK", "np", "pd")]
from tjk import elo as EL
from tjk import komiser as KM
d = EL.ekle(d); d["rid"] = d.groupby(O.K).ngroup()
E = M["feat"] + EK + LPEK + EL.EXTRA_FEAT
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str); rows = []
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q3"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
    th, mu, sd, nk = _fit(tr, E, M.get("lam", 100.0)); te["p_E"] = skorla(te, E, th, mu, sd)
    rows.append(te[["tarih", "hipodrom", "kosu", "no", "kazandi", "p_piyasa", "p_E", "n_at"] + [c for c in ("mesafe", "pist") if c in te.columns]]); print(kq, len(te), flush=True)
R = pd.concat(rows, ignore_index=True)
ik = pd.concat([pd.read_csv(f)[["tarih", "hipodrom", "kosu", "ik"]] for f in sorted(glob.glob(os.path.join(KOK, "data", "yillik", "eslesme_*.csv.gz")))]).drop_duplicates(["tarih", "hipodrom", "kosu"], keep="last")
R = R.merge(ik, on=["tarih", "hipodrom", "kosu"], how="left")
G = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))]); G = G[G.tur == "GANYAN"]
ODE = {(r.tarih, r.hipodrom, int(r.kosu), str(r.kombo)): float(r.tutar) for r in G.itertuples()}
TR2A = {v: k for k, v in KM.ASCII.items()}
R["ode"] = [ODE.get((t, TR2A.get(h, h), int(k), str(n)), 0.0) if kz == 1 else 0.0 for t, h, k, n, kz in zip(R.tarih, R.hipodrom, R.kosu, R.no, R.kazandi)]
R["p_E"] = R.p_E / R.groupby(["tarih", "hipodrom", "kosu"]).p_E.transform("sum")
R["ok"] = R.p_piyasa > 0
K3 = ["tarih", "hipodrom", "kosu"]
W = R[(R.kazandi == 1) & R.ok].copy()
W["dll"] = np.log(W.p_E.clip(lower=1e-9)) - np.log(W.p_piyasa.clip(lower=1e-9))
Rk = R.drop_duplicates(K3)[K3 + ["mesafe", "pist", "n_at", "ik"]]
W = W.drop(columns=[c for c in ("mesafe", "pist", "n_at", "ik") if c in W.columns]).merge(Rk, on=K3, how="left").drop_duplicates(K3)
W["yari"] = np.where(W.tarih < "2026-04-01", 1, 2)
print("kazananlı koşu:", len(W), "ort. kazanç (nats/koşu):", round(float(W.dll.mean()), 4), flush=True)
pistler = W.pist.astype(str).value_counts().index[:3].tolist()
ik_q = W.ik.quantile([1 / 3, 2 / 3]).values
SEG = {}
for h in ["istanbul", "ankara", "izmir", "bursa", "adana", "kocaeli", "elazig", "sanliurfa", "diyarbakir"]: SEG["hip:" + h] = W.hipodrom == h
SEG["mesafe:<=1300"] = W.mesafe <= 1300; SEG["mesafe:1301-1700"] = (W.mesafe > 1300) & (W.mesafe <= 1700); SEG["mesafe:>1700"] = W.mesafe > 1700
for p in pistler: SEG["pist:" + p] = W.pist.astype(str) == p
SEG["alan:<=8"] = W.n_at <= 8; SEG["alan:9-11"] = (W.n_at >= 9) & (W.n_at <= 11); SEG["alan:>=12"] = W.n_at >= 12
SEG["ik:alt"] = W.ik <= ik_q[0]; SEG["ik:orta"] = (W.ik > ik_q[0]) & (W.ik <= ik_q[1]); SEG["ik:ust"] = W.ik > ik_q[1]
NSEG = 21
rng = np.random.default_rng(2030); BB = 10000
def boot(df):
    g = df.groupby("tarih").dll.agg(["sum", "count"]).values; n = len(g); idx = rng.integers(0, n, (BB, n)); S = g[idx].sum(1)
    m = S[:, 0] / S[:, 1]; return g[:, 0].sum() / g[:, 1].sum(), np.percentile(m, [2.5, 97.5]), np.percentile(m, [100 * 0.025 / NSEG, 100 - 100 * 0.025 / NSEG])
def roi_info(sec_races):
    S = R.merge(sec_races[K3], on=K3, how="inner"); b = S[((S.p_E / S.p_piyasa) >= 1.15) & (S.p_E >= 0.10)]
    if len(b) == 0: return None
    g = b.groupby("tarih").agg(n=("ode", "size"), o=("ode", "sum")).values; m = len(g); idx = rng.integers(0, m, (3000, m)); S2 = g[idx].sum(1)
    return {"bahis": int(g[:, 0].sum()), "ROI": float(g[:, 1].sum() / g[:, 0].sum() - 1), "GA95": [float(x) for x in np.percentile(S2[:, 1] / S2[:, 0] - 1, [2.5, 97.5])]}
res = {"genel_kazanc": float(W.dll.mean()), "n_kosu": len(W), "segmentler": {}}
for ad, m in SEG.items():
    sub = W[m.fillna(False)]
    if len(sub) < 150: res["segmentler"][ad] = {"n": len(sub), "karar": "yetersiz"}; print(ad, len(sub), "yetersiz", flush=True); continue
    nok, ga95, gab = boot(sub); y1 = float(sub[sub.yari == 1].dll.mean()); y2 = float(sub[sub.yari == 2].dll.mean())
    rest = float(W[~m.fillna(False)].dll.mean())
    karar = "ZAYIF PIYASA ADAYI" if (gab[0] > 0 and y1 > 0 and y2 > 0) else ("isaret" if (ga95[0] > 0 and y1 > 0 and y2 > 0) else "yok")
    res["segmentler"][ad] = {"n": len(sub), "kazanc": float(nok), "GA95": [float(x) for x in ga95], "GA_bonf": [float(x) for x in gab], "yari1": y1, "yari2": y2, "disi": rest, "roi_bilgi": roi_info(sub), "karar": karar}
    print(f"{ad:22s} n={len(sub):5d} kazanç {nok:+.4f} GA95[{ga95[0]:+.4f};{ga95[1]:+.4f}] Bonf[{gab[0]:+.4f};{gab[1]:+.4f}] yarı {y1:+.4f}/{y2:+.4f} dışı {rest:+.4f} -> {karar}", flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t203.json"), "w"), indent=1, ensure_ascii=False)
print("KARARLAR:", {k: v["karar"] for k, v in res["segmentler"].items() if v["karar"] not in ("yok", "yetersiz")})
