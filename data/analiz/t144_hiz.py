"""T144 hız puanı derinleştirme. ÜRETİM DOSYALARINA YAZMAZ."""
import sys, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(144)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy().sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
t = pd.to_numeric(d.derece_sn, errors="coerce"); mes = pd.to_numeric(d.mesafe, errors="coerce")
ok = t.notna() & (t > 20) & mes.notna()
d["grp"] = d.hipodrom.astype(str) + "|" + mes.astype(str) + "|" + d.pist.astype(str)
ust = ok & (d.pct <= 0.5)
g = d[ust].assign(t=t[ust]).groupby(["grp", "tarih"]).agg(n=("t", "size"), s=("t", "sum")).reset_index().sort_values("tarih")
g["cn"] = g.groupby("grp").n.cumsum() - g.n; g["cs"] = g.groupby("grp").s.cumsum() - g.s
g["std"] = np.where(g.cn >= 8, g.cs / g.cn.clip(lower=1), np.nan)
d = d.merge(g[["grp", "tarih", "std"]], on=["grp", "tarih"], how="left")
t = pd.to_numeric(d.derece_sn, errors="coerce"); ok = t.notna() & (t > 20) & d["std"].notna()
d["raw"] = np.where(ok, -(t / d["std"] - 1) * 100, np.nan)
k = d.tarih + "|" + d.hipodrom.astype(str) + "|" + d.pist.astype(str)
sm = d.groupby(k).raw.transform("sum"); sc = d.groupby(k).raw.transform("count")
d["fig"] = (d.raw - (sm - d.raw.fillna(0)) / (sc - d.raw.notna()).clip(lower=1)).clip(-6, 6)
d["mb"] = pd.to_numeric(d.mesafe, errors="coerce") // 200
d = d.sort_values(["at", "tarih", "kosu"]).reset_index(drop=True)
gg = d.groupby("at", sort=False).fig
d["fg_son"] = gg.shift(1)
d["fg_ort5"] = gg.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
d["fg_en5"] = gg.transform(lambda s: s.shift(1).rolling(5, min_periods=1).max())
d["fg_trend"] = d.fg_son - gg.transform(lambda s: s.shift(2).rolling(3, min_periods=1).mean())
d["fg_var"] = gg.transform(lambda s: s.shift(1).rolling(5, min_periods=1).count()) / 5.0
# hücre: aynı mesafe bandı (±1 kutu = ±200 m) içinde son 5'te en iyi; hesap atın kendi geçmişi üzerinde
hc = np.full(len(d), np.nan); at = d.at.values; fg = d.fig.values; mb = d.mb.values
i = 0
while i < len(d):
    j = i
    while j < len(d) and at[j] == at[i]: j += 1
    for r in range(i, j):
        best = np.nan
        for q in range(max(i, r - 5), r):
            if not np.isnan(fg[q]) and not np.isnan(mb[q]) and not np.isnan(mb[r]) and abs(mb[q] - mb[r]) <= 1:
                best = fg[q] if np.isnan(best) else max(best, fg[q])
        hc[r] = best
    i = j
d["fg_hucre"] = hc
d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
H = []; key = [d.tarih, d.hipodrom, d.kosu]
for c in ("fg_son", "fg_ort5", "fg_en5", "fg_trend", "fg_hucre", "fg_var"):
    d[c + "_yok"] = d[c].isna().astype(float); mu = d[c].mean(); x = d[c].fillna(mu) - mu
    d["f_" + c] = x - x.groupby(key).transform("mean"); H += ["f_" + c, c + "_yok"]
log("kapsam fg_son %.3f fg_hucre %.3f (2025-10+: %.3f)" % (d.fg_son.notna().mean(), d.fg_hucre.notna().mean(), d[d.tarih >= "2025-10-01"].fg_son.notna().mean()))
base = M["feat"] + GL.EK
def fit(tr, feat, sifir):
    z = tr.copy()
    if sifir: z["lp"] = 0.0
    th, mu, sd, nk = GL._fit(z, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k_: float(v) for k_, v in mu.items()}, "sd": {k_: float(v) for k_, v in sd.items()}, "w": [float(x_) for x_ in th]}
def sk(te, A, p):
    z = GL.z2(te, A)
    if not p: return z
    return A["w"][0] * te.lp.values + float(A["w"][1 + A["feat"].index("f_lp2")] / A["sd"]["f_lp2"]) * te.lp.values ** 2 + z
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
    A = fit(tr, base + GL.LPEK, False); B = fit(tr, base + H + GL.LPEK, False); Z = fit(tr, base, True); ZH = fit(tr, base + H, True)
    df = pd.concat({"J": raceLL(te, sk(te, A, True)), "JH": raceLL(te, sk(te, B, True)), "Z": raceLL(te, sk(te, Z, False)), "ZH": raceLL(te, sk(te, ZH, False))}, axis=1).dropna()
    for (a_, b_, c_), r in df.iterrows(): R.append((ay, a_, r.J, r.JH, r.Z, r.ZH))
    log(ay, "n", len(df), "J %.4f JH %.4f Z %.4f ZH %.4f" % tuple(df[c].mean() for c in ["J", "JH", "Z", "ZH"]), "%d sn" % (time.time() - t0))
D = pd.DataFrame(R, columns=["ay", "gun", "J", "JH", "Z", "ZH"]); ud, inv = np.unique(D.gun, return_inverse=True); N = np.bincount(inv)
def ci(x):
    x = np.asarray(x); S = np.bincount(inv, weights=x); bs = []
    for _ in range(1000):
        kk = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((kk * S).sum() / (kk * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T144 koşu", len(D), "gün", len(ud))
for a, b, ad in (("ZH", "Z", "piyasasız ZH − Z (ANA KARAR)"), ("JH", "J", "piyasa ofsetli JH − J")):
    m, lo, hi = ci(D[a] - D[b]); log("  %-32s %+.5f [%+.5f, %+.5f]  pozitif ay %d/%d" % (ad, m, lo, hi, int((D.groupby("ay").apply(lambda q: (q[a] - q[b]).mean()) > 0).sum()), D.ay.nunique()), "-> ADAY" if (a == "ZH" and lo > 0) else "")
log("bitti")
