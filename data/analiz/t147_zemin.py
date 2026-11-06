"""T147 at bazında zemin (ıslak/ağır pist) tercihi. ÜRETİM DOSYALARINA YAZMAZ."""
import sys, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(147)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl"); G = pd.read_pickle("/tmp/claude-0/ay_gun.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy()
G["yz"] = G.yuzey.astype(str).str.lower().map(lambda s: "c" if "çim" in s or "cim" in s else ("k" if "kum" in s else None))
G["agirlik"] = pd.to_numeric(G.agirlik, errors="coerce"); G["sicaklik"] = pd.to_numeric(G.sicaklik, errors="coerce"); G["nem"] = pd.to_numeric(G.nem, errors="coerce")
G = G.dropna(subset=["yz"]).drop_duplicates(["tarih", "hipodrom", "yz"])
d["yz"] = np.where(d.pist.astype(str).str.lower().str.contains("çim|cim"), "c", "k")
d = d.merge(G[["tarih", "hipodrom", "yz", "agirlik"]], on=["tarih", "hipodrom", "yz"], how="left")
d["wet"] = (d.agirlik >= 1.0).astype(float); d.loc[d.agirlik.isna(), "wet"] = np.nan
log("gün-pist eşleşme: %.3f; ıslak payı (eşleşenler): %.3f; test döneminde ıslak koşu payı: %.3f" % (d.agirlik.notna().mean(), d.wet.mean(), d[d.tarih >= "2025-10-01"].wet.mean()))
d = d.sort_values(["at", "tarih", "kosu"]).reset_index(drop=True)
w = d.wet.fillna(0.0).values; known = d.wet.notna().values; pct = d.pct.values
gk = d.groupby("at", sort=False).ngroup().values
fw = np.zeros(len(d)); nw = np.zeros(len(d)); nd = np.zeros(len(d))
cw = cd = sw = sd_ = 0.0; last = -1
for i in range(len(d)):
    if gk[i] != last: cw = cd = sw = sd_ = 0.0; last = gk[i]
    nw[i] = cw; nd[i] = cd
    mw = sw / cw if cw > 0 else np.nan; md = sd_ / cd if cd > 0 else np.nan
    fw[i] = (-(mw - md) * (cw / (cw + 3.0))) if (cw > 0 and cd > 0) else 0.0
    if known[i] and not np.isnan(pct[i]):
        if w[i] >= 1: cw += 1; sw += pct[i]
        else: cd += 1; sd_ += pct[i]
d["f_gp"] = fw * np.where(d.wet == 1.0, 1.0, 0.0)   # yalnız bugünün pisti ıslaksa etkin
d["f_gp_n"] = np.where(d.wet == 1.0, np.minimum(nw, 3) / 3.0, 0.0)
d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
key = [d.tarih, d.hipodrom, d.kosu]; S = ["f_gp", "f_gp_n"]
for c in S: d[c] = d[c] - d.groupby(key)[c].transform("mean")
log("f_gp sıfır olmayan oran: %.3f (test dönemi ıslak koşu sayısı: %d)" % ((d.f_gp.abs() > 1e-9).mean(), int(d[(d.tarih >= "2025-10-01") & (d.wet == 1.0)].groupby(["tarih", "hipodrom", "kosu"]).ngroups)))
base = M["feat"] + GL.EK
def fit(tr, feat, sifir):
    z = tr.copy()
    if sifir: z["lp"] = 0.0
    th, mu, sd, nk = GL._fit(z, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th]}
def sk(te, A_, p):
    z = GL.z2(te, A_)
    if not p: return z
    return A_["w"][0] * te.lp.values + float(A_["w"][1 + A_["feat"].index("f_lp2")] / A_["sd"]["f_lp2"]) * te.lp.values ** 2 + z
def raceLL(te, s):
    q = te[["tarih", "hipodrom", "kosu", "kazandi"]].copy(); q["s"] = np.asarray(s)
    k_ = [q.tarih, q.hipodrom, q.kosu]; m = q.groupby(k_, sort=False).s.transform("max"); q["e"] = np.exp(q.s - m)
    Z = q.groupby(k_, sort=False).e.transform("sum"); q["lp_"] = q.s - m - np.log(Z); w_ = q[q.kazandi == 1]
    return w_.groupby(["tarih", "hipodrom", "kosu"]).lp_.sum()
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
R = []
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay]
    if te.empty: continue
    Jm = fit(tr, base + GL.LPEK, False); JG = fit(tr, base + S + GL.LPEK, False); Zm = fit(tr, base, True); ZG = fit(tr, base + S, True)
    df = pd.concat({"J": raceLL(te, sk(te, Jm, True)), "JG": raceLL(te, sk(te, JG, True)), "Z": raceLL(te, sk(te, Zm, False)), "ZG": raceLL(te, sk(te, ZG, False))}, axis=1).dropna()
    wetr = te.groupby(["tarih", "hipodrom", "kosu"]).wet.max(); df["wet"] = wetr.reindex(df.index)
    for (a_, b_, c_), r in df.iterrows(): R.append((ay, a_, r.J, r.JG, r.Z, r.ZG, r.wet))
    log(ay, "n", len(df), "J %.4f JG %.4f Z %.4f ZG %.4f" % tuple(df[c].mean() for c in ["J", "JG", "Z", "ZG"]), "%d sn" % (time.time() - t0))
D = pd.DataFrame(R, columns=["ay", "gun", "J", "JG", "Z", "ZG", "wet"])
def ci(x, gun, boot=1000):
    x = np.asarray(x); ud, inv = np.unique(gun, return_inverse=True); N = np.bincount(inv); S_ = np.bincount(inv, weights=x); bs = []
    for _ in range(boot):
        k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S_).sum() / (k * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T147 koşu", len(D), "ıslak koşu", int((D.wet == 1).sum()))
for nm, m in (("TÜMÜ", D.ay.notna()), ("yalnız ıslak koşular", D.wet == 1)):
    x = D[m]
    for a, b, ad in (("ZG", "Z", "piyasasız ZG−Z"), ("JG", "J", "piyasalı JG−J")):
        mm, lo, hi = ci((x[a] - x[b]).values, x.gun.values); log("  %-22s %-16s n=%5d %+.5f [%+.5f, %+.5f]" % (nm, ad, len(x), mm, lo, hi), "-> ADAY" if (nm == "TÜMÜ" and a == "ZG" and lo > 0) else "")
log("bitti")
