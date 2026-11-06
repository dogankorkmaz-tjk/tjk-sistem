"""T157 (ön kayıt: hipotez_defteri 2026-11-06 20:55): sabit ihtimalli oran, Benter + kapanış ganyanının üstüne bilgi ekler mi? (LODO c)"""
import glob, json, math, numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
rng = np.random.default_rng(157); K = []
for f in sorted(glob.glob("data/piyasa/2026-*.csv.gz")):
    gun = f[-17:-7]
    if gun > "2026-11-05": continue
    d = pd.read_csv(f); d = d[(d.tip == 1001) & (d.oran > 1.0)]
    try: G = json.load(open(f"docs/data/gun/{gun}.json", encoding="utf-8"))
    except Exception: continue
    if G.get("w0_g1") is None: continue
    son = d.sort_values("saat").groupby(["hipodrom", "kosu", "no"]).oran.last()
    for h in G["hipodromlar"]:
        for k in h["kosular"]:
            so = k.get("sonuc") or {}; at = [a for a in k["atlar"] if not a.get("kosmaz") and str(a["no"]) in so]
            if len(at) < 4: continue
            try:
                z = np.array([a["z6"] for a in at], float); g = np.array([so[str(a["no"])]["g"] for a in at], float)
                fo = np.array([son[(h["id"], k["kosu"], a["no"])] for a in at], float)
                sira = np.array([so[str(a["no"])].get("sira") or 99 for a in at])
            except (KeyError, TypeError): continue
            if (g <= 1).any() or not (sira == 1).any() or np.isnan(z).any(): continue
            pk = (1 / g) / (1 / g).sum(); ps = (1 / fo) / (1 / fo).sum()
            K.append(dict(gun=gun, b=G["w0_g1"] * np.log(pk) + z, x=np.log(ps), w=int(np.argmax(sira == 1))))
print("koşu", len(K), "gün", len({k["gun"] for k in K}))
def ll(r, c): s = r["b"] + c * r["x"]; s = s - s.max(); return -(s[r["w"]] - np.log(np.exp(s).sum()))
gunler = sorted({k["gun"] for k in K}); D = []; C = {}
for g in gunler:
    tr = [r for r in K if r["gun"] != g]; c = minimize_scalar(lambda c: sum(ll(r, c) for r in tr), bounds=(-2, 3), method="bounded").x; C[g] = round(c, 3)
    for r in K:
        if r["gun"] == g: D.append((g, ll(r, c) - ll(r, 0.0), ll(r, 0.0)))
D = pd.DataFrame(D, columns=["gun", "d", "l0"]); ug = D.gun.unique(); S = D.groupby("gun").d.sum(); N = D.groupby("gun").size(); bs = []
for _ in range(4000):
    s = rng.choice(ug, len(ug)); bs.append(S[s].sum() / N[s].sum())
lo, hi = np.percentile(bs, [2.5, 97.5])
print(f"L1−L0 (kazanan log kaybı) {D.d.mean():+.4f} [{lo:+.4f}; {hi:+.4f}] | L0 {D.l0.mean():.4f} | gün başına iyileşen {int((S < 0).sum())}/{len(S)}")
print("günlere göre c (dışarıda bırakılarak):", C)
print("KARAR:", "ADAY (sabit oran ek bilgi taşıyor)" if hi < 0 else ("ZARAR" if lo > 0 else "etkisiz / ayırt edilemedi (güç sınırlı)"))
