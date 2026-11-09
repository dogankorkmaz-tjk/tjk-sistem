"""T192: tay (<=3 yaş koşusu) ve yetişkin koşuları için AYRI model (ayrı katsayılar) Jason'a (tek model) göre kazanan olabilirliğini artırır mı?
Ön kayıt: hipotez_defteri T192. Actions: t192.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
import numpy as np, pandas as pd
from tjk import ortak as O
from tjk.ozellik import hazirla
from tjk import mesafe as MS
from tjk.golge import _fit, _oku, EK, LPEK
from tjk.calistir import yukle_model
from tjk.walkforward import skorla

M = yukle_model()
d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.temiz & d.kazandi.notna() & d.lp.notna()].copy()
d["tarih"] = d.tarih.astype(str)
d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
d["rid"] = d.groupby(O.K).ngroup()
ymax = d.groupby("rid").yas.transform("max")
d["tay"] = (ymax <= 3).astype(int)        # koşudaki en yaşlı at <=3 → tay koşusu; yas bilinmiyorsa yetişkin
print("tay koşu payı (satır):", round(float(d.tay.mean()), 3), "koşu:", int(d.groupby("rid").tay.first().sum()), "/", int(d.rid.nunique()), flush=True)
feat = M["feat"] + EK + LPEK
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
rows = []; kats = {}
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q3"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup()
    th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0)); te["p_J"] = skorla(te, feat, th, mu, sd)
    te["p_A"] = np.nan
    for g in (0, 1):
        trg = tr[tr.tay == g]
        thg, mug, sdg, nkg = _fit(trg, feat, M.get("lam", 100.0))
        pg = skorla(te, feat, thg, mug, sdg)
        te.loc[te.tay == g, "p_A"] = pg[(te.tay == g).values]
        kats[(kq, g)] = (len(trg), thg)
    w = te[te.kazandi == 1]
    rows.append(pd.DataFrame({"fold": kq, "tarih": w.tarih.values, "tay": w.tay.values,
                              "J": (np.log(w.p_J) - np.log(w.p_piyasa)).values, "A": (np.log(w.p_A) - np.log(w.p_piyasa)).values}))
    print(kq, len(w), "tay", int(w.tay.sum()), "J", round(float(rows[-1].J.mean()), 5), "A", round(float(rows[-1].A.mean()), 5), flush=True)
R = pd.concat(rows, ignore_index=True); R["yil"] = R.tarih.str[:4]; R["dd"] = R.A - R.J
rng = np.random.default_rng(1920)
def ga(v, tarih, lo, hi, B=20000):
    g = pd.Series(np.asarray(v)).groupby(np.asarray(tarih)).agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values
    n = len(s); idx = rng.integers(0, n, (B, n)); m = s[idx].sum(1) / c[idx].sum(1)
    return float(s.sum() / c.sum()), float(np.percentile(m, lo)), float(np.percentile(m, hi)), int(len(v))
res = {}
for ad, msk in (("tay", R.tay == 1), ("yetiskin", R.tay == 0), ("toplam", R.tay >= 0)):
    S = R[msk]; lo, hi = (1.25, 98.75) if ad != "toplam" else (2.5, 97.5)
    res[ad] = {"tum": ga(S.dd, S.tarih, lo, hi)}
    for y in ("2025", "2026"):
        Sy = S[S.yil == y]; res[ad][y] = ga(Sy.dd, Sy.tarih, lo, hi) if len(Sy) else None
    print(ad, {k: ([round(x, 5) for x in v[:3]] + [v[3]] if v else None) for k, v in res[ad].items()}, flush=True)
def ok(ad): 
    r = res[ad]; return r["tum"][1] > 0 and r["2025"] is not None and r["2025"][0] > 0 and r["2026"] is not None and r["2026"][0] > 0
print("KARAR: tay", "ADAY" if ok("tay") else "YOK", "| yetiskin", "ADAY" if ok("yetiskin") else "YOK", "(toplam bilgi amaçlı)")
# betimleyici: son foldda iki grubun katsayıları (std ölçekli), farkı en büyük 12 özellik
kq = sorted({k for k, _ in kats})[-1]
(n0, t0), (n1, t1) = kats[(kq, 0)], kats[(kq, 1)]
names = ["lp(piyasa)"] + feat
dif = sorted(zip(names, t0, t1), key=lambda x: -abs(x[2] - x[1]))[:12]
print("KATSAYI (son fold", kq, "; eğitim n yetişkin", n0, "tay", n1, ") özellik: yetişkin / tay")
for a, b, c in dif: print(f"  {a}: {b:+.3f} / {c:+.3f}")
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t192.json"), "w"), indent=1)
