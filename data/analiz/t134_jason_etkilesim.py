"""T134: Jason'a mesafe/pist etkileşimleri, yürüyen test. ÜRETİM DOSYALARINA YAZMAZ (yalnız /tmp/claude-0/jason_d.pkl okur)."""
import sys, numpy as np, pandas as pd, time
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
rng = np.random.default_rng(134)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy()
base = M["feat"] + GL.EK; feat = base + GL.LPEK
mes = pd.to_numeric(d.mesafe, errors="coerce"); orta = ((mes >= 1400) & (mes < 1800)).astype(float); uzun = (mes >= 1800).astype(float)
cim = d.pist.astype(str).str.lower().str.contains("çim|cim|turf").astype(float)
mo, mu_, mc = float(orta[mes.notna()].mean()), float(uzun[mes.notna()].mean()), float(cim[d.pist.notna()].mean())   # DÜZELTME: eksik mesafe/pist = nötr (gösterge = ortalama -> etkileşim 0); ilk koşuda eksikler "kısa/kum" sayılıyordu (hata)
orta = orta.where(mes.notna(), mo); uzun = uzun.where(mes.notna(), mu_); cim = cim.where(d.pist.notna(), mc)
log("band payları orta %.3f uzun %.3f çim %.3f"%(mo,mu_,mc), "satır", len(d), "mesafe eksik", int(mes.isna().sum()))
IX = []
for tag, ind, c0 in (("orta", orta, mo), ("uzun", uzun, mu_), ("cim", cim, mc)):
    for f in base:
        n = f + "×" + tag; d[n] = d[f].fillna(0.0) * (ind - c0); IX.append(n)
featB = base + IX + GL.LPEK;   # DÜZELTME 2: golge.z2 ağırlıkları sırayla eşler, f_lp2 (LPEK) listenin SONUNDA olmalı; ilk iki koşuda IX sonrasına konunca ağırlıklar kayıyordu (hatalı)
log("özellik A", len(feat), "B", len(featB))
rows = []
def skor(te, A):
    lp2a = float(A["w"][1 + A["feat"].index("f_lp2")] / A["sd"]["f_lp2"])
    z = GL.z2(te, A); s = A["w"][0] * te.lp.values + lp2a * te.lp.values ** 2 + z
    return s
def raceLL(te, s):
    t = te[["tarih", "hipodrom", "kosu", "kazandi"]].copy(); t["s"] = s
    g = t.groupby(["tarih", "hipodrom", "kosu"], sort=False)
    m = g.s.transform("max"); t["e"] = np.exp(t.s - m); Z = t.groupby([t.tarih, t.hipodrom, t.kosu], sort=False).e.transform("sum")
    t["lp_"] = t.s - m - np.log(Z); w = t[t.kazandi == 1]
    return w.groupby(["tarih", "hipodrom", "kosu"]).lp_.sum()
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
last = None
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay]
    if te.empty: continue
    thA, muA, sdA, nk = GL._fit(tr, feat, M.get("lam", 100.0)); A = {"feat": feat, "mu": {k: float(v) for k, v in muA.items()}, "sd": {k: float(v) for k, v in sdA.items()}, "w": [float(x) for x in thA]}
    thB, muB, sdB, _ = GL._fit(tr, featB, M.get("lam", 100.0)); B = {"feat": featB, "mu": {k: float(v) for k, v in muB.items()}, "sd": {k: float(v) for k, v in sdB.items()}, "w": [float(x) for x in thB]}
    la = raceLL(te, skor(te, A)); lb = raceLL(te, skor(te, B)); g = (lb - la).dropna()
    for (t, h, k), v in g.items(): rows.append((ay, t, v))
    log(ay, "eğitim koşu", nk, "test koşu", len(g), "kazanç/koşu %+.5f" % g.mean(), "%d sn" % (time.time() - t0)); last = (B, thB, sdB)
D = pd.DataFrame(rows, columns=["ay", "gun", "g"]); ud, inv = np.unique(D.gun, return_inverse=True); S = np.bincount(inv, weights=D.g); N = np.bincount(inv)
bs = []
for _ in range(1000):
    k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S).sum() / (k * N).sum())
lo, hi = np.percentile(bs, [2.5, 97.5])
log("=== T134 KARAR: B−A %+.5f nat/koşu [%+.5f, %+.5f]  koşu %d gün %d  pozitif ay %d/%d" % (D.g.mean(), lo, hi, len(D), len(ud), (D.groupby("ay").g.mean() > 0).sum(), D.ay.nunique()), "-> KABUL (gölge aday önerilir)" if lo > 0 else "-> ayırt edilemedi")
B, thB, sdB = last; w = np.array(thB[1:1 + len(featB[:-1])]) if False else None
ws = pd.Series(thB[1:1 + len([f for f in featB if f not in GL.LPEK])], index=[f for f in featB if f not in GL.LPEK])
ix = ws[IX].abs().sort_values(ascending=False).head(10)
log("en büyük 10 etkileşim (standartlaştırılmış katsayı, son eğitim):"); [log("  %-24s %+.4f" % (n, ws[n])) for n in ix.index]
log("bitti")
