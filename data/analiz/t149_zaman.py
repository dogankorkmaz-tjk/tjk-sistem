"""T149 video tam sıra zaman serisi. ÜRETİM DOSYALARINA YAZMAZ."""
import sys, json, glob, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(149)
def log(*a): print(*a, flush=True)
rows = []
for f in glob.glob("data/video_seyir/20*.json"):
    b = f.split("/")[-1][:-5]; t, h, k = b.split("_"); j = json.load(open(f)); z = [x for x in (j.get("zaman") or []) if x.get("sira")]
    if len(z) < 15: continue
    n = len(z); a, c = n // 3, 2 * n // 3
    for no in j.get("numaralar") or []:
        r = np.array([(x["sira"].index(no) + 1) if no in x["sira"] else 6 for x in z], float)
        e, l = r[:a], r[c:]
        rows.append((t, h, int(k), int(no), (r == 1).mean(), (r <= 3).mean(), r.mean(), e.mean(), l.mean(), np.abs(np.diff(r)).mean(), (r[c - n // 3:] == 1).any()))
V = pd.DataFrame(rows, columns=["tarih", "hipodrom", "kosu", "no", "lead_frac", "top3_frac", "mean_rank", "early_rank", "late_rank", "vol", "led_late"])
log("video at-koşu satırı", len(V), "video", V.groupby(["tarih", "hipodrom", "kosu"]).ngroups)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl"); O = pd.read_pickle("/tmp/claude-0/video_ozet.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy()
d = d.merge(V, on=["tarih", "hipodrom", "kosu", "no"], how="left").merge(O, on=["tarih", "hipodrom", "kosu", "no"], how="left")
d["fade"] = np.where(d.early_rank.notna(), ((d.early_rank <= 2) & (d.sira >= 4)).astype(float), np.nan)
d["lead_lost"] = np.where(d.early_rank.notna(), (d.led_late.astype(float) == 1) & (d.sira >= 3), np.nan).astype(float)
d["_g"] = d.orta - d.gec; d["_f"] = d.gec - d.son; d["_t"] = d.erken - d.son
d["_flop"] = np.where(d.orta.notna(), ((d.son - d.orta) >= 3).astype(float), np.nan); d["_unl"] = np.where(d.orta.notna(), (((d.orta - d.gec) >= 2) & (d.son >= d.gec)).astype(float), np.nan)
d = d.sort_values(["at", "tarih", "kosu"]).reset_index(drop=True); gk = d.groupby("at", sort=False)
V2 = []; V1 = []
for src in ("lead_frac", "top3_frac", "mean_rank", "early_rank", "late_rank", "vol", "fade", "lead_lost"):
    n = "v2_" + src; d[n] = gk[src].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean()); V2.append(n)
d["v2_var"] = d.v2_lead_frac.notna().astype(float); V2.append("v2_var")
for src, n in (("_g", "ov_gain"), ("_f", "ov_fin"), ("_t", "ov_tot"), ("_flop", "ov_flop"), ("_unl", "ov_unl")):
    d[n] = gk[src].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean()); V1.append(n)
d["ov_var"] = d.ov_gain.notna().astype(float); V1.append("ov_var")
for n in V2[:-1] + V1[:-1]: d[n] = d[n].fillna(0.0)
d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
log("v2_var oranı (2025-10+): %.3f ; ov_var %.3f" % (d[d.tarih >= "2025-10-01"].v2_var.mean(), d[d.tarih >= "2025-10-01"].ov_var.mean()))
base = M["feat"] + GL.EK
def fit(tr, feat, sifir):
    z = tr.copy()
    if sifir: z["lp"] = 0.0
    th, mu, sd, nk = GL._fit(z, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k_: float(v) for k_, v in mu.items()}, "sd": {k_: float(v) for k_, v in sd.items()}, "w": [float(x) for x in th]}
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
    Jm = fit(tr, base + GL.LPEK, False); JV2 = fit(tr, base + V2 + GL.LPEK, False); Zm = fit(tr, base, True); ZV2 = fit(tr, base + V2, True); ZV = fit(tr, base + V1, True)
    df = pd.concat({"J": raceLL(te, sk(te, Jm, True)), "JV2": raceLL(te, sk(te, JV2, True)), "Z": raceLL(te, sk(te, Zm, False)), "ZV2": raceLL(te, sk(te, ZV2, False)), "ZV": raceLL(te, sk(te, ZV, False))}, axis=1).dropna()
    for (a_, b_, c_), r in df.iterrows(): R.append((ay, a_, r.J, r.JV2, r.Z, r.ZV2, r.ZV))
    log(ay, "n", len(df), "J %.4f JV2 %.4f Z %.4f ZV2 %.4f ZV %.4f" % tuple(df[c].mean() for c in ["J", "JV2", "Z", "ZV2", "ZV"]), "%d sn" % (time.time() - t0))
D = pd.DataFrame(R, columns=["ay", "gun", "J", "JV2", "Z", "ZV2", "ZV"]); ud, inv = np.unique(D.gun, return_inverse=True); N = np.bincount(inv)
def ci(x):
    x = np.asarray(x); S_ = np.bincount(inv, weights=x); bs = []
    for _ in range(1000):
        k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S_).sum() / (k * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T149 koşu", len(D))
res = {}
for a, b, ad in (("ZV2", "Z", "piyasasız ZV2−Z (ANA)"), ("ZV2", "ZV", "ZV2−ZV (T142'ye ek)"), ("ZV", "Z", "ZV−Z (T142, karşılaştırma)"), ("JV2", "J", "piyasalı JV2−J")):
    m, lo, hi = ci(D[a] - D[b]); res[ad] = lo; log("  %-30s %+.5f [%+.5f, %+.5f]  pozitif ay %d/%d" % (ad, m, lo, hi, int((D.groupby("ay").apply(lambda q: (q[a] - q[b]).mean()) > 0).sum()), D.ay.nunique()))
log("KARAR:", "ADAY" if res["piyasasız ZV2−Z (ANA)"] > 0 and res["ZV2−ZV (T142'ye ek)"] > 0 else "ADAY DEĞİL (T142'nin ötesinde ek bilgi yok)")
log("bitti")
