"""T214: zayıf piyasa bölgesi (bölüm bazlı log-olabilirlik kazancı). Ön kayıt: hipotez_defteri T214. Actions: t214.yml. Betik sonuca bakılarak ayarlanmaz."""
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
    rows.append(te[["tarih", "hipodrom", "kosu", "no", "kazandi", "p_piyasa", "p_E", "n_at", "sira"] + [c for c in ("mesafe", "pist") if c in te.columns]]); print(kq, len(te), flush=True)
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
from tjk import besli as BS
rng = np.random.default_rng(2140); BB = 10000
R["donem"] = np.where(R.tarih < "2026-04-01", 1, 2)
G0 = [1.0, 0.8018, 0.6804, 0.5958, 0.5307]
W1 = R[(R.kazandi == 1) & R.ok].drop_duplicates(K3).copy(); W1["dll"] = np.log(W1.p_E.clip(lower=1e-9)) - np.log(W1.p_piyasa.clip(lower=1e-9))
Bv = R[R.ok & ((R.p_E / R.p_piyasa) >= 1.15) & (R.p_E >= 0.10)]
# 2.-5. sıra kazancı ve 5'li tutma
cell = []
for k, g in R[R.ok].groupby(K3):
    s = pd.to_numeric(g.sira, errors="coerce").values; pos = []
    for r in range(1, 6):
        w = np.where(s == r)[0]
        if len(w) != 1: pos = None; break
        pos.append(int(w[0]))
    if pos is None or len(g) < 5: continue
    pe = g.p_E.values; pm = g.p_piyasa.values / g.p_piyasa.values.sum()
    def ll(p):
        t = 0.0
        for r in range(2, 6):
            w = np.power(np.maximum(p, 1e-9), G0[r - 1]); w = w.copy(); w[pos[:r - 1]] = 0; t += np.log(max(w[pos[r - 1]] / w.sum(), 1e-12))
        return t
    row = dict(tarih=k[0], hipodrom=k[1], kosu=k[2], donem=1 if k[0] < "2026-04-01" else 2, g25=ll(pe) - ll(pm), n=len(g), hit=np.nan, exp=np.nan)
    if len(g) >= 12:
        kp = BS.kupon_g(list(pe), 96, G0)
        if kp: sets, pr = kp; row["hit"] = float(all(pos[j] in sets[j] for j in range(5))); row["exp"] = float(pr)
    cell.append(row)
C = pd.DataFrame(cell); print("g25 koşu", len(C), "5li", int(C.hit.notna().sum()), flush=True)
ROI = {}
for h in HIPS: ROI[h] = Bv[Bv.hipodrom == h]
def stat(df, kind):
    if kind == "dll": return df.dll.mean()
    if kind == "g25": return df.g25.mean()
    if kind == "oran5": d2 = df[df.hit.notna()]; return d2.hit.sum() / d2.exp.sum() if len(d2) and d2.exp.sum() > 0 else np.nan
def boot(df, kind, nb=BB):
    u, inv = np.unique(df.tarih.values, return_inverse=True); nd = len(u); gi = [np.where(inv == i)[0] for i in range(nd)]
    if kind == "dll": a = df.dll.values; S = np.array([[a[ix].sum(), len(ix)] for ix in gi])
    elif kind == "g25": a = df.g25.values; S = np.array([[a[ix].sum(), len(ix)] for ix in gi])
    else:
        hh = df.hit.fillna(0).values; ee = df.exp.fillna(0).values; S = np.array([[hh[ix].sum(), ee[ix].sum()] for ix in gi])
    idx = rng.integers(0, nd, (nb, nd)); T = S[idx].sum(1); return T[:, 0] / np.maximum(T[:, 1], 1e-12)
res = {"hip": {}}
srcs = {"dll": W1, "g25": C, "oran5": C}
for h in HIPS:
    res["hip"][h] = {}
    for kind, df in srcs.items():
        sub = df[df.hipodrom == h]
        if kind == "oran5": sub = sub[sub.hit.notna()]
        if len(sub) < 100: res["hip"][h][kind] = {"n": int(len(sub)), "karar": "yetersiz"}; continue
        b = boot(sub, kind); lo, hi = np.percentile(b, [0.07, 99.93]); nok = stat(sub, kind); ref = 1.0 if kind == "oran5" else 0.0
        y1 = stat(sub[sub.donem == 1], kind); y2 = stat(sub[sub.donem == 2], kind); same = (y1 - ref) * (y2 - ref) > 0
        res["hip"][h][kind] = {"n": int(len(sub)), "deger": float(nok), "GA_bonf": [float(lo), float(hi)], "yari1": float(y1) if y1 == y1 else None, "yari2": float(y2) if y2 == y2 else None, "ayni_isaret": bool(same)}
    sub = ROI[h]; res["hip"][h]["roi_bilgi"] = {"bahis": int(len(sub)), "roi": float(sub.ode.sum() / len(sub) - 1) if len(sub) else None}
    print(h, json.dumps(res["hip"][h]), flush=True)
# hiyerarşik/büzmeli (dll)
def tau(df):
    g = df.groupby("hipodrom").dll.agg(["mean", "var", "count"]); g = g[g["count"] >= 100]; mu = df.dll.mean()
    t2 = max(0.0, g["mean"].var(ddof=1) - (g["var"] / g["count"]).mean()); return t2, g, mu
t2, g, mu = tau(W1); sh = {h: float(t2 / (t2 + r["var"] / r["count"]) * (r["mean"] - mu)) if t2 > 0 else 0.0 for h, r in g.iterrows()}
u, inv = np.unique(W1.tarih.values, return_inverse=True); nd = len(u); gi = [np.where(inv == i)[0] for i in range(nd)]; tb = []
for _ in range(2000):
    ix = np.concatenate([gi[j] for j in rng.integers(0, nd, nd)]); tb.append(tau(W1.iloc[ix])[0])
res["hiyerarsik_dll"] = {"mu": float(mu), "tau2": float(t2), "tau2_GA95": [float(x) for x in np.percentile(tb, [2.5, 97.5])], "tau": float(np.sqrt(t2)), "u_buzmeli": sh}
print(json.dumps(res["hiyerarsik_dll"]), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t214.json"), "w"), indent=1, ensure_ascii=False)
