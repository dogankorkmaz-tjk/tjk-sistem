"""T142: videodan yarış içi olay özellikleri (atın ÖNCEKİ koşularından). ÜRETİM DOSYALARINA YAZMAZ."""
import sys, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(142)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl"); V = pd.read_pickle("/tmp/claude-0/video_ozet.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy()
d = d.merge(V, on=["tarih", "hipodrom", "kosu", "no"], how="left")
d["_g"] = d.orta - d.gec; d["_f"] = d.gec - d.son; d["_t"] = d.erken - d.son
d["_flop"] = np.where(d.orta.notna(), ((d.son - d.orta) >= 3).astype(float), np.nan)
d["_unl"] = np.where(d.orta.notna(), (((d.orta - d.gec) >= 2) & (d.son >= d.gec)).astype(float), np.nan)
d = d.sort_values(["at", "tarih", "kosu"]).reset_index(drop=True)
gk = d.groupby("at", sort=False)
OV = []
for src, n in (("_g", "ov_gain"), ("_f", "ov_fin"), ("_t", "ov_tot"), ("_flop", "ov_flop"), ("_unl", "ov_unl")):
    d[n] = gk[src].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean()); OV.append(n)
d["ov_var"] = (d[OV[0]].notna()).astype(float); OV.append("ov_var")
for n in OV[:-1]: d[n] = d[n].fillna(0.0)
log("satır", len(d), "ov_var oranı (2025-10+): %.3f" % d[d.tarih >= "2025-10-01"].ov_var.mean())
base = M["feat"] + GL.EK
def fit(tr, feat, sifir):
    t = tr.copy()
    if sifir: t["lp"] = 0.0
    th, mu, sd, nk = GL._fit(t, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th]}
def sk(te, A, p):
    z = GL.z2(te, A)
    if not p: return z
    return A["w"][0] * te.lp.values + float(A["w"][1 + A["feat"].index("f_lp2")] / A["sd"]["f_lp2"]) * te.lp.values ** 2 + z
def raceLL(te, s):
    t = te[["tarih", "hipodrom", "kosu", "kazandi"]].copy(); t["s"] = np.asarray(s)
    k = [t.tarih, t.hipodrom, t.kosu]; m = t.groupby(k, sort=False).s.transform("max"); t["e"] = np.exp(t.s - m)
    Z = t.groupby(k, sort=False).e.transform("sum"); t["lp_"] = t.s - m - np.log(Z); w = t[t.kazandi == 1]
    return w.groupby(["tarih", "hipodrom", "kosu"]).lp_.sum()
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
R = []
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay]
    if te.empty: continue
    A = fit(tr, base + GL.LPEK, False); B = fit(tr, base + OV + GL.LPEK, False); Z = fit(tr, base, True); ZB = fit(tr, base + OV, True)
    df = pd.concat({"A": raceLL(te, sk(te, A, True)), "B": raceLL(te, sk(te, B, True)), "Z": raceLL(te, sk(te, Z, False)), "ZB": raceLL(te, sk(te, ZB, False))}, axis=1).dropna()
    for (t, h, k), r in df.iterrows(): R.append((ay, t, r.A, r.B, r.Z, r.ZB))
    log(ay, "n", len(df), "A %.4f B %.4f Z %.4f ZB %.4f" % tuple(df[c].mean() for c in ["A", "B", "Z", "ZB"]), "%d sn" % (time.time() - t0))
D = pd.DataFrame(R, columns=["ay", "gun", "A", "B", "Z", "ZB"]); ud, inv = np.unique(D.gun, return_inverse=True); N = np.bincount(inv)
def ci(x):
    x = np.asarray(x); S = np.bincount(inv, weights=x); bs = []
    for _ in range(1000):
        k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S).sum() / (k * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T142 koşu", len(D), "gün", len(ud))
for a, b, ad in (("B", "A", "J+olay − J (piyasa ofsetli; KARAR)"), ("ZB", "Z", "Z+olay − Z (piyasasız)")):
    m, lo, hi = ci(D[a] - D[b]); log("  %-36s %+.5f [%+.5f, %+.5f]  pozitif ay %d/%d" % (ad, m, lo, hi, int((D.groupby("ay").apply(lambda g: (g[a] - g[b]).mean()) > 0).sum()), D.ay.nunique()), "-> ADAY" if (a == "B" and lo > 0) else "")
log("bitti")
