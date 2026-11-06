"""T146 soy/yetiştirici/sahip/tam yaş/satış. ÜRETİM DOSYALARINA YAZMAZ."""
import sys, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(146)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl"); A = pd.read_pickle("/tmp/claude-0/ay_oz.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy()
A = A.drop_duplicates(["tarih", "hipodrom", "kosu", "no"])
d = d.merge(A[["tarih", "hipodrom", "kosu", "no", "baba", "anne", "annebaba", "babababa", "yetistirici", "sahip", "dogum", "satis"]].rename(columns={"baba": "baba_a", "sahip": "sahip_a"}), on=["tarih", "hipodrom", "kosu", "no"], how="left")
log("satır", len(d), "atyarisi eşleşme (annebaba dolu): %.3f; 2025-10+: %.3f" % (d.annebaba.notna().mean(), d[d.tarih >= "2025-10-01"].annebaba.notna().mean()))
d["res"] = d.kazandi - 1.0 / d.n_at
mes = pd.to_numeric(d.mesafe, errors="coerce"); d["mb"] = pd.cut(mes, [0, 1399, 1799, 2199, 9999], labels=False).astype("float")
d["yz"] = np.where(d.pist.astype(str).str.lower().str.contains("çim|cim"), "c", "k")
d["k_baba_mb"] = d.baba_a.astype(str) + "|" + d.mb.astype(str); d["k_baba_pist"] = d.baba_a.astype(str) + "|" + d.yz
d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
def enc(col, name, shrink=50.0):
    k = d[col].astype(str).where(d[col].notna(), None)
    g = d.assign(_k=k).dropna(subset=["_k"]).groupby(["_k", "tarih"]).res.agg(["sum", "count"]).reset_index().sort_values(["_k", "tarih"])
    g["cs"] = g.groupby("_k")["sum"].cumsum() - g["sum"]; g["cn"] = g.groupby("_k")["count"].cumsum() - g["count"]
    g[name] = g.cs / (g.cn + shrink)
    m = d[["tarih"]].assign(_k=k).merge(g[["_k", "tarih", name]], on=["_k", "tarih"], how="left")[name].fillna(0.0).values
    return m
S = []
for col, name in (("annebaba", "e_fm"), ("babababa", "e_ff"), ("yetistirici", "e_br"), ("sahip_a", "e_ow"), ("k_baba_mb", "e_bmb"), ("k_baba_pist", "e_bpist")):
    d[name] = enc(col, name); S.append(name)
yr = (pd.to_datetime(d.tarih) - pd.to_datetime(d.dogum, unit="s")).dt.days / 365.25
d["age_g"] = yr.fillna(yr.median()); d["age_g3"] = d.age_g * (d.yas <= 3).astype(float); d["age_gf"] = (d.age_g - d.age_g.round()) * (d.yas <= 3).astype(float); S += ["age_g", "age_g3", "age_gf"]
d["sat_v"] = d.satis.notna().astype(float); d["sat_l"] = np.log1p(d.satis.fillna(0.0)); S += ["sat_v", "sat_l"]
key = [d.tarih, d.hipodrom, d.kosu]
for c in S: d[c] = d[c] - d.groupby(key)[c].transform("mean")
log("özellik kapsamları (sıfır olmayan oran): " + " ".join("%s %.2f" % (c, (d[c].abs() > 1e-9).mean()) for c in S), "| satış dolu %.3f" % d.satis.notna().mean())
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
    Z = q.groupby(k_, sort=False).e.transform("sum"); q["lp_"] = q.s - m - np.log(Z); w = q[q.kazandi == 1]
    return w.groupby(["tarih", "hipodrom", "kosu"]).lp_.sum()
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
R = []
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay]
    if te.empty: continue
    Jm = fit(tr, base + GL.LPEK, False); JS = fit(tr, base + S + GL.LPEK, False); Zm = fit(tr, base, True); ZS = fit(tr, base + S, True)
    df = pd.concat({"J": raceLL(te, sk(te, Jm, True)), "JS": raceLL(te, sk(te, JS, True)), "Z": raceLL(te, sk(te, Zm, False)), "ZS": raceLL(te, sk(te, ZS, False))}, axis=1).dropna()
    ilk = te.groupby(["tarih", "hipodrom", "kosu"]).apply(lambda q: (q.h_n <= 1).mean()); yg = te.groupby(["tarih", "hipodrom", "kosu"]).yas.mean()
    df["ilk"] = ilk.reindex(df.index); df["yg"] = yg.reindex(df.index)
    for (a_, b_, c_), r in df.iterrows(): R.append((ay, a_, r.J, r.JS, r.Z, r.ZS, r.ilk, r.yg))
    log(ay, "n", len(df), "J %.4f JS %.4f Z %.4f ZS %.4f" % tuple(df[c].mean() for c in ["J", "JS", "Z", "ZS"]), "%d sn" % (time.time() - t0))
D = pd.DataFrame(R, columns=["ay", "gun", "J", "JS", "Z", "ZS", "ilk", "yg"])
def ci(x, gun, boot=1000):
    x = np.asarray(x); ud, inv = np.unique(gun, return_inverse=True); N = np.bincount(inv); S_ = np.bincount(inv, weights=x); bs = []
    for _ in range(boot):
        k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S_).sum() / (k * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T146 koşu", len(D))
for nm, m in (("TÜMÜ", D.ay.notna()), ("ilk-oranı ≥%10", D.ilk >= .10), ("alan yaşı ≤3", D.yg <= 3)):
    x = D[m]
    for a, b, ad in (("ZS", "Z", "piyasasız ZS−Z"), ("JS", "J", "piyasalı JS−J")):
        mm, lo, hi = ci((x[a] - x[b]).values, x.gun.values); log("  %-16s %-16s n=%5d %+.5f [%+.5f, %+.5f]" % (nm, ad, len(x), mm, lo, hi), "-> ADAY" if (nm == "TÜMÜ" and a == "ZS" and lo > 0) else "")
log("bitti")
