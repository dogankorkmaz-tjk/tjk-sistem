"""T138+T139. ÜRETİM DOSYALARINA YAZMAZ (yalnız /tmp/claude-0/jason_d.pkl okur)."""
import sys, numpy as np, pandas as pd, time
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(138)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy()
base = M["feat"] + GL.EK
mes = pd.to_numeric(d.mesafe, errors="coerce"); orta = ((mes >= 1400) & (mes < 1800)).astype(float); uzun = (mes >= 1800).astype(float)
cim = d.pist.astype(str).str.lower().str.contains("çim|cim|turf").astype(float)
mo, mu_, mc = float(orta[mes.notna()].mean()), float(uzun[mes.notna()].mean()), float(cim[d.pist.notna()].mean())
orta = orta.where(mes.notna(), mo); uzun = uzun.where(mes.notna(), mu_); cim = cim.where(d.pist.notna(), mc)
IX = []
for tag, ind, c0 in (("orta", orta, mo), ("uzun", uzun, mu_), ("cim", cim, mc)):
    for f in base:
        n = f + "x" + tag; d[n] = d[f].fillna(0.0) * (ind - c0); IX.append(n)
kg = pd.to_numeric(d.kilo, errors="coerce"); d["kg_rel"] = (kg - kg.groupby([d.tarih, d.hipodrom, d.kosu]).transform("mean")).fillna(0.0)
d["kg_uzun"] = d.kg_rel * (uzun - mu_); d["kg_orta"] = d.kg_rel * (orta - mo); KG = ["kg_rel", "kg_uzun", "kg_orta"]
log("satır", len(d), "özellik", len(base), "etkileşim", len(IX))
def fit(tr, feat, sifir):
    t = tr.copy()
    if sifir: t["lp"] = 0.0
    th, mu, sd, nk = GL._fit(t, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th]}
def skor(te, A, piyasali):
    z = GL.z2(te, A) if [f for f in A["feat"] if f not in GL.LPEK] else np.zeros(len(te))
    if not piyasali: return z
    lp2a = float(A["w"][1 + A["feat"].index("f_lp2")] / A["sd"]["f_lp2"]) if "f_lp2" in A["feat"] else 0.0
    return A["w"][0] * te.lp.values + lp2a * te.lp.values ** 2 + z
def raceLL(te, s):
    t = te[["tarih", "hipodrom", "kosu", "kazandi", "p_piyasa"]].copy(); t["s"] = s
    k = [t.tarih, t.hipodrom, t.kosu]; m = t.groupby(k, sort=False).s.transform("max"); t["e"] = np.exp(t.s - m)
    Z = t.groupby(k, sort=False).e.transform("sum"); t["lp_"] = t.s - m - np.log(Z); w = t[t.kazandi == 1]
    return w.groupby(["tarih", "hipodrom", "kosu"]).agg(l=("lp_", "sum"), pp=("p_piyasa", "first"))
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
rows = []
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay]
    if te.empty: continue
    Pk = fit(tr, ["f_lp2"], False); J = fit(tr, base + GL.LPEK, False)
    Z = fit(tr, base, True); ZB = fit(tr, base + IX, True); ZK = fit(tr, base + KG, True)
    R = {"P": raceLL(te, te.lp.values), "Pk": raceLL(te, skor(te, Pk, True)), "J": raceLL(te, skor(te, J, True)),
         "Z": raceLL(te, skor(te, Z, False)), "ZB": raceLL(te, skor(te, ZB, False)), "ZK": raceLL(te, skor(te, ZK, False))}
    df = pd.concat({k: v.l for k, v in R.items()}, axis=1).dropna(); df["pp"] = R["P"].pp.reindex(df.index)
    for (t, h, k), r in df.iterrows(): rows.append((ay, t, r.P, r.Pk, r.J, r.Z, r.ZB, r.ZK, r.pp))
    log(ay, "test koşu", len(df), "P %.4f Pk %.4f J %.4f Z %.4f ZB %.4f ZK %.4f" % tuple(df[c].mean() for c in ["P", "Pk", "J", "Z", "ZB", "ZK"]), "%d sn" % (time.time() - t0))
D = pd.DataFrame(rows, columns=["ay", "gun", "P", "Pk", "J", "Z", "ZB", "ZK", "pp"]); ud, inv = np.unique(D.gun, return_inverse=True); N = np.bincount(inv)
def ci(x):
    S = np.bincount(inv, weights=x); bs = []
    for _ in range(1000):
        k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S).sum() / (k * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T138 ortalama kazanan log-olasılığı (yüksek iyi), koşu", len(D), "gün", len(ud))
for c in ["P", "Pk", "J", "Z"]: log("  %-3s %.4f" % (c, D[c].mean()))
for a, b, ad in (("J", "Pk", "özelliklerin piyasaya katkısı J−Pk"), ("J", "Z", "piyasanın özelliklere katkısı J−Z"), ("Z", "P", "özellikler tek başına − ham piyasa Z−P"), ("Z", "Pk", "Z − kalibre piyasa")):
    m, lo, hi = ci((D[a] - D[b]).values); log("  %-42s %+.5f [%+.5f, %+.5f]" % (ad, m, lo, hi))
log("kovaya göre (kazananın piyasa olasılığı) ort. log p: P / Z / J")
for lo_, hi_ in ((0, .05), (.05, .10), (.10, .20), (.20, .35), (.35, 1.01)):
    q = D[(D.pp >= lo_) & (D.pp < hi_)]; log("  %.2f-%.2f n=%5d  P %.3f  Z %.3f  J %.3f" % (lo_, hi_, len(q), q.P.mean(), q.Z.mean(), q.J.mean()))
log("=== T139 (piyasasız)")
for a, b, ad in (("ZB", "Z", "mesafe/pist etkileşimleri ZB−Z"), ("ZK", "Z", "göreli kilo (+uzun,+orta) ZK−Z")):
    m, lo, hi = ci((D[a] - D[b]).values); mde = 2.8 / 1.96 * (hi - lo) / 2
    log("  %-34s %+.5f [%+.5f, %+.5f]  MDE(80%% güç) %.5f nat/koşu" % (ad, m, lo, hi, mde), "-> ADAY" if lo > 0 else "-> ayırt edilemedi")
log("ay bazında ZB−Z pozitif:", int((D.groupby("ay").apply(lambda g: (g.ZB - g.Z).mean()) > 0).sum()), "/", D.ay.nunique(), " ZK−Z pozitif:", int((D.groupby("ay").apply(lambda g: (g.ZK - g.Z).mean()) > 0).sum()))
log("bitti")
