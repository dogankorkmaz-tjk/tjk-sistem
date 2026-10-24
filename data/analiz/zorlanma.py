"""Zorlanma/korunma hipotezi. Ön kayıt: hipotez_defteri 2026-10-24 17:30."""
import numpy as np, pandas as pd, random
d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d = d[["tarih", "hipodrom", "kosu", "at", "sira", "derece_sn", "kazandi", "p_piyasa", "ganyan", "n_at"]].copy()
d = d[d.sira.notna() & (d.sira > 0) & d.derece_sn.notna() & (d.derece_sn > 0)].copy()
d["rk"] = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
d = d.sort_values(["tarih", "hipodrom", "kosu", "sira"])
g = d.groupby(["tarih", "hipodrom", "kosu"])
d["ahead"] = d.derece_sn - g.derece_sn.shift(1); d["behind"] = g.derece_sn.shift(-1) - d.derece_sn
tw = g.derece_sn.transform("min"); d["kayip"] = (d.derece_sn - tw) / tw
d["HP1"] = np.fmin(d.ahead.fillna(9), d.behind.fillna(9)) <= 0.10
d["HP2"] = (d.sira == 1) & (d.behind <= 0.15)
d["EZ"] = (d.rk <= 3) & (d.sira >= 5) & (d.kayip >= 0.015)
d["tarih_dt"] = pd.to_datetime(d.tarih)
d = d.sort_values(["at", "tarih", "hipodrom", "kosu"])
ga = d.groupby("at")
for c in ("tarih_dt", "p_piyasa", "kazandi", "ganyan"): d["n_" + c] = ga[c].shift(-1)
d["gun_ara"] = (d.n_tarih_dt - d.tarih_dt).dt.days
x = d[d.n_p_piyasa.notna() & (d.gun_ara <= 90) & (d.gun_ara >= 1)].copy()
x["fazla"] = x.n_kazandi.astype(float) - x.n_p_piyasa
x["getiri"] = np.where(x.n_kazandi == 1, x.n_ganyan, 0.0) - 1.0
x["kat"] = pd.cut(x.rk, [0, 1, 2, 3, 6, 99], labels=["1", "2", "3", "4-6", "7+"])
x["gun"] = x.n_tarih_dt.dt.strftime("%Y-%m-%d")
print("önceki-sonraki çift:", len(x), "| bayrak sayıları HP1/HP2/EZ:", int(x.HP1.sum()), int(x.HP2.sum()), int(x.EZ.sum()))
random.seed(21); np.random.seed(21); ug = sorted(x.gun.unique()); gi = {g: i for i, g in enumerate(ug)}; x["gi"] = x.gun.map(gi); NG = len(ug)
kats = ["1", "2", "3", "4-6", "7+"]; x["ki"] = x.kat.astype(str).map({k: i for i, k in enumerate(kats)})
def tablo(bay, col):
    T = np.zeros((NG, 5, 2, 2))                                  # gün, katman, bayrak, (toplam, sayı)
    f = x[bay].astype(int).values; np.add.at(T, (x.gi.values, x.ki.values, f, 0), x[col].values); np.add.at(T, (x.gi.values, x.ki.values, f, 1), 1.0)
    return T
def fark_t(T):
    S = T.sum(0); s = n = 0.0
    for k in range(5):
        if S[k, 1, 1] > 0 and S[k, 0, 1] > 0: s += (S[k, 1, 0] / S[k, 1, 1] - S[k, 0, 0] / S[k, 0, 1]) * S[k, 1, 1]; n += S[k, 1, 1]
    return s / n if n else np.nan
for bay, bek in (("HP1", "<0"), ("HP2", "<0"), ("EZ", ">0")):
    for col in ("fazla", "getiri"):
        T = tablo(bay, col); f = fark_t(T); L = [fark_t(T[np.random.randint(0, NG, NG)]) for _ in range(1500)]; q = np.nanpercentile(L, [1.7, 2.5, 97.5, 98.3])
        a, b = x[x[bay]], x[~x[bay]]
        print(f"{bay} (beklenen {bek}) n={len(a):6d} {col:7s} bayraklı {a[col].mean():+.4f} bayraksız {b[col].mean():+.4f} | katmanlı fark {f:+.4f} %95 [{q[1]:+.4f},{q[2]:+.4f}] %98,3 [{q[0]:+.4f},{q[3]:+.4f}]", flush=True)
