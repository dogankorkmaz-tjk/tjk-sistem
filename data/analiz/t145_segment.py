"""T145 segment haritası. ÜRETİM DOSYALARINA YAZMAZ. Ayrıca T148 için at düzeyi OOS olasılıklarını /tmp/claude-0/t145_oos.pkl'e yazar."""
import sys, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(145)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy().reset_index(drop=True)
base = M["feat"] + GL.EK
def fit(tr, feat, sifir):
    z = tr.copy()
    if sifir: z["lp"] = 0.0
    th, mu, sd, nk = GL._fit(z, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th]}
def sk(te, A, p):
    z = GL.z2(te, A)
    if not p: return z
    return A["w"][0] * te.lp.values + float(A["w"][1 + A["feat"].index("f_lp2")] / A["sd"]["f_lp2"]) * te.lp.values ** 2 + z
def probs(te, s):
    q = te[["tarih", "hipodrom", "kosu"]].copy(); q["s"] = np.asarray(s); k = [q.tarih, q.hipodrom, q.kosu]
    m = q.groupby(k, sort=False).s.transform("max"); e = np.exp(q.s - m); return (e / e.groupby(k, sort=False).transform("sum")).values
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
OUT = []
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay].copy()
    if te.empty: continue
    Pk = fit(tr, ["f_lp2"], False); J = fit(tr, base + GL.LPEK, False); Z = fit(tr, base, True)
    te["pP"] = probs(te, te.lp.values); te["pPk"] = probs(te, sk(te, Pk, True)); te["pJ"] = probs(te, sk(te, J, True)); te["pZ"] = probs(te, sk(te, Z, False))
    OUT.append(te[["tarih", "hipodrom", "kosu", "no", "at", "kazandi", "p_piyasa", "pP", "pPk", "pJ", "pZ", "h_n", "yas", "mesafe", "pist", "n_at"]]); log(ay, "%d sn" % (time.time() - t0))
O = pd.concat(OUT); O.to_pickle("/tmp/claude-0/t145_oos.pkl")
K = ["tarih", "hipodrom", "kosu"]
W = O[O.kazandi == 1].copy()
for c in ("pP", "pPk", "pJ", "pZ"): W["l" + c[1:]] = np.log(W[c].clip(lower=1e-12))
W = W.groupby(K).agg(lP=("lP", "sum"), lPk=("lPk", "sum"), lJ=("lJ", "sum"), lZ=("lZ", "sum"), n_at=("n_at", "first"), mesafe=("mesafe", "first"), pist=("pist", "first"), hip=("hipodrom", "first")).reset_index()
W["null"] = -np.log(W.n_at.clip(lower=2))
g = O.groupby(K).agg(ilk=("h_n", lambda s: (s <= 1).mean()), yas=("yas", "mean")).reset_index(); W = W.merge(g, on=K)
mes = pd.to_numeric(W.mesafe, errors="coerce"); cim = W.pist.astype(str).str.lower().str.contains("çim|cim")
top = W.hip.value_counts().index[:6].tolist()
SEG = {"alan ≤8": W.n_at <= 8, "alan 9–11": (W.n_at >= 9) & (W.n_at <= 11), "alan ≥12": W.n_at >= 12,
       "mesafe <1400": mes < 1400, "mesafe 1400–1799": (mes >= 1400) & (mes < 1800), "mesafe ≥1800": mes >= 1800,
       "çim": cim, "kum": ~cim, "ilk-oranı <%10": W.ilk < .10, "ilk-oranı %10–30": (W.ilk >= .10) & (W.ilk < .30), "ilk-oranı ≥%30": W.ilk >= .30,
       "alan yaşı ≤3": W.yas <= 3, "alan yaşı >3": W.yas > 3}
for h in top: SEG["hip " + h] = W.hip == h
SEG["hip diğer"] = ~W.hip.isin(top); SEG["TÜMÜ"] = W.n_at > 0
ud, inv = np.unique(W.tarih, return_inverse=True)
def rho(mask, boot=500):
    m = mask.values; x = W[m]; 
    if len(x) < 150: return None
    def stat(idx):
        a = x.iloc[idx]; nn = a["null"].mean(); return (nn - a.lZ.mean()) / (nn - a.lP.mean()) if (nn - a.lP.mean()) != 0 else np.nan
    base_ = stat(np.arange(len(x)))
    days = x.tarih.values; ug = np.unique(days); idxs = {g_: np.where(days == g_)[0] for g_ in ug}; bs = []
    for _ in range(boot):
        pick = rng.choice(ug, len(ug)); bs.append(stat(np.concatenate([idxs[p] for p in pick])))
    return len(x), base_, np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5), (x.lZ - x.lP).mean(), (x.lJ - x.lPk).mean()
log("=== T145 segment haritası (Ρ = piyasasız modelin piyasaya oranı; Z−P, J−Pk nat/koşu)")
for k, m in SEG.items():
    r = rho(m)
    log("  %-18s %s" % (k, "n<150" if r is None else "n=%5d  Ρ %.2f [%.2f, %.2f]  Z−P %+.3f  J−Pk %+.4f" % r))
log("bitti")
