"""T213: zayıf piyasa bölgesi (bölüm bazlı log-olabilirlik kazancı). Ön kayıt: hipotez_defteri T213. Actions: t213.yml. Betik sonuca bakılarak ayarlanmaz."""
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
HIPS = ["istanbul", "ankara", "izmir", "bursa", "adana", "kocaeli", "elazig", "sanliurfa", "diyarbakir"]
rng = np.random.default_rng(2130); BB = 10000
R["donem"] = np.where(R.tarih < "2026-04-01", "sec", "dog")
B = R[R.ok & ((R.p_E / R.p_piyasa) >= 1.15) & (R.p_E >= 0.10)].copy()
W = R[(R.kazandi == 1) & R.ok].copy(); W["dll"] = np.log(W.p_E.clip(lower=1e-9)) - np.log(W.p_piyasa.clip(lower=1e-9)); W = W.drop_duplicates(K3)
def roi(df): return float(df.ode.sum() / len(df) - 1) if len(df) else float("nan")
res = {"hip": {}}
for h in HIPS:
    for dn in ("sec", "dog"):
        b = B[(B.hipodrom == h) & (B.donem == dn)]; w = W[(W.hipodrom == h) & (W.donem == dn)]
        res["hip"].setdefault(h, {})[dn] = {"bahis": int(len(b)), "roi": roi(b), "dll": float(w.dll.mean()) if len(w) else None, "n_kosu": int(len(w))}
print(json.dumps(res["hip"]), flush=True)
ok = [h for h in HIPS if res["hip"][h]["sec"]["bahis"] >= 150 and res["hip"][h]["dog"]["bahis"] >= 150]; res["hipodrom_kullanilan"] = ok
from scipy.stats import spearmanr
def rho(vals): return spearmanr([vals[h][0] for h in ok], [vals[h][1] for h in ok])[0]
v = {h: (res["hip"][h]["sec"]["roi"], res["hip"][h]["dog"]["roi"]) for h in ok}; r0 = rho(v); cnt = 0
for _ in range(10000):
    perm = rng.permutation(len(ok)); vv = {h: (v[h][0], v[ok[perm[i]]][1]) for i, h in enumerate(ok)}; cnt += rho(vv) >= r0
res["A"] = {"spearman_roi": float(r0), "perm_p_tek_yon": float((cnt + 1) / 10001)}
vd = {h: (res["hip"][h]["sec"]["dll"], res["hip"][h]["dog"]["dll"]) for h in ok if res["hip"][h]["sec"]["dll"] is not None and res["hip"][h]["dog"]["dll"] is not None}
res["A"]["spearman_dll"] = float(spearmanr([x[0] for x in vd.values()], [x[1] for x in vd.values()])[0]) if len(vd) > 3 else None
ana = sorted(ok, key=lambda h: -res["hip"][h]["sec"]["roi"])[:3]; res["ana"] = ana
bd = B[B.donem == "dog"]; a = bd[bd.hipodrom.isin(ana)]; o = bd[~bd.hipodrom.isin(ana) & bd.hipodrom.isin(ok)]
def agg(df): return df.groupby("tarih").agg(n=("ode", "size"), s=("ode", "sum"))
ga, go = agg(a), agg(o); gun = sorted(set(ga.index) | set(go.index)); A_ = ga.reindex(gun).fillna(0).values; O_ = go.reindex(gun).fillna(0).values; n = len(gun); out = []
for _ in range(BB):
    i = rng.integers(0, n, n); sa = A_[i].sum(0); so = O_[i].sum(0)
    if sa[0] > 0 and so[0] > 0: out.append(sa[1] / sa[0] - so[1] / so[0])
res["B"] = {"ana": ana, "roi_ana_dog": roi(a), "bahis_ana": int(len(a)), "roi_diger_dog": roi(o), "bahis_diger": int(len(o)), "fark": roi(a) - roi(o), "GA95": [float(x) for x in np.percentile(out, [2.5, 97.5])]}
print(json.dumps(res["A"]), json.dumps(res["B"]), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t213.json"), "w"), indent=1, ensure_ascii=False)
