"""T191: kilo-düzeltmeli hız figürü (K) ve rakip-gücü ('zorluk merkezi') düzeltmeli figür (Z) Jason'a bilgi katıyor mu?
Ön kayıt: hipotez_defteri T191. Actions: t191.yml. Betik sonuca bakılarak ayarlanmaz."""
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

r = d.rel_sure.astype(float)
# --- beta (sn/kg): yalnız 2025-07-01 ÖNCESİ, koşu içi regresyon rel_sure ~ f_kilo, tek sefer, sonra sabit
tr0 = d[(d.tarih < "2025-07-01") & r.notna() & d.f_kilo.notna()]
x = tr0.f_kilo - tr0.groupby("rid").f_kilo.transform("mean")
y = tr0.rel_sure - tr0.groupby("rid").rel_sure.transform("mean")
beta = float((x * y).sum() / (x * x).sum())
print("beta sn/kg:", round(beta, 5), "n", len(tr0), flush=True)

def gun_duz(v):
    k = d.tarih + "|" + d.hipodrom.astype(str) + "|" + d.pist.astype(str)
    sm = v.groupby(k).transform("sum"); sc = v.groupby(k).transform("count")
    return v - (sm - v.fillna(0)) / (sc - v.notna()).clip(lower=1)

def son3(v):
    t = pd.DataFrame({"at": d["at"].values, "v": v.values}, index=d.index)
    return t.groupby("at").v.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean()).fillna(0).clip(-3, 3)

def kosu_ici(s):
    return s - s.groupby(d.rid).transform("mean")

yeni = {}
if beta > 0:
    yeni["fK"] = kosu_ici(son3(gun_duz(r - beta * d.f_kilo)))
else:
    print("beta<=0: K kolu çalıştırılmıyor (ön kayıt kuralı)", flush=True)
# Z: yarıştaki ilk 4'ün YARIŞ ÖNCESİ f_fig3 ortalaması = rakip zayıflığı (büyük = yavaş/zayıf alan)
S = d[d.sira <= 4].groupby("rid").f_fig3.mean().reindex(d.rid).values
S = pd.Series(S, index=d.index); S = (S - S.mean()).fillna(0.0)
yeni["fZ"] = kosu_ici(son3(gun_duz(r) + S))
for k, v in yeni.items():
    d["f_" + k] = v

base = M["feat"] + EK + LPEK
kollar = {"Jason": base}
if "fK" in yeni: kollar["J_K"] = base + ["f_fK"]
kollar["J_Z"] = base + ["f_fZ"]
if "fK" in yeni: kollar["J_KZ"] = base + ["f_fK", "f_fZ"]

d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str)
rows = []
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q3"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
    te["rid"] = te.groupby(O.K).ngroup()
    for ad, feat in kollar.items():
        th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
        te["p_" + ad] = skorla(te, feat, th, mu, sd)
    w = te[te.kazandi == 1]
    o = {"fold": kq, "tarih": w.tarih.values}
    for ad in kollar: o[ad] = (np.log(w["p_" + ad]) - np.log(w.p_piyasa)).values
    rows.append(pd.DataFrame(o)); print(kq, len(w), {a: round(float(rows[-1][a].mean()), 5) for a in kollar}, flush=True)
R = pd.concat(rows, ignore_index=True)
R["yil"] = R.tarih.str[:4]
rng = np.random.default_rng(1910)

def ga(v, tarih, lo, hi, B=20000):
    g = pd.Series(v).groupby(np.asarray(tarih)).agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values
    n = len(s); idx = rng.integers(0, n, (B, n)); m = s[idx].sum(1) / c[idx].sum(1)
    return float(s.sum() / c.sum()), float(np.percentile(m, lo)), float(np.percentile(m, hi))

res = {"beta": beta}
for ad in [a for a in kollar if a != "Jason"]:
    dd = (R[ad] - R.Jason).values
    bonf = ad in ("J_K", "J_Z")
    lo, hi = (1.25, 98.75) if bonf else (2.5, 97.5)
    t = ga(dd, R.tarih.values, lo, hi); res[ad] = {"tum": t}
    for y_ in ("2025", "2026"):
        m = (R.yil == y_).values; res[ad][y_] = ga(dd[m], R.tarih.values[m], lo, hi)
    print(ad, "GA", "Bonf %97.5" if bonf else "%95", {k: [round(x, 5) for x in v] for k, v in res[ad].items() if k != "beta"}, flush=True)

def ok(ad):
    if ad not in res: return False
    return res[ad]["tum"][1] > 0 and res[ad]["2025"][0] > 0 and res[ad]["2026"][0] > 0
print("KARAR K:", "ADAY (gölge, ayrı ön kayıt)" if ok("J_K") else "YOK", "| Z:", "ADAY (gölge, ayrı ön kayıt)" if ok("J_Z") else "YOK")
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t191.json"), "w"), indent=1)
