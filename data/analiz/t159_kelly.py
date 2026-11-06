"""T159 (ön kayıt: hipotez_defteri 2026-11-06 21:20): düz vs kesirli Kelly, Benter (MJ) değer ganyan bahisleri (p×g ≥ 1,2)."""
import glob, pickle, numpy as np, pandas as pd
rng = np.random.default_rng(159)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
T = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "ganyan", "kosmadi"]) for f in sorted(glob.glob("data/temiz/202[56]-*.csv.gz"))])
T = T[T.kosmadi != True]; GN = {(r.tarih, r.hipodrom, int(r.kosu), int(r.no)): float(r.ganyan) for r in T.itertuples() if r.ganyan == r.ganyan}
B = []
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; p = np.exp(s - s.max()); p /= p.sum()
        g = np.array([GN.get((key[0], key[1], int(key[2]), x), np.nan) for x in nos])
        if np.isnan(g).any(): continue
        ev = p * g; j = int(np.argmax(np.where(ev >= 1.2, ev, -1)))
        if ev[j] < 1.2: continue
        B.append(dict(gun=key[0], key=tuple(key), p=p[j], g=g[j], kazandi=int(j == 0)))   # nos bitiriş sırasında: indeks 0 = kazanan
D = pd.DataFrame(B).sort_values(["gun", "key"]).reset_index(drop=True)
print("bahis", len(D), "gün", D.gun.nunique(), "| isabet", D.kazandi.sum(), "| ort. ganyan", round(D.g.mean(), 2))
D["get_D"] = D.kazandi * D.g - 1
gs = D.groupby("gun").agg(k=("get_D", "sum"), n=("get_D", "size")); ug = gs.index.values; bs = []
for _ in range(4000):
    s = rng.choice(ug, len(ug)); bs.append(gs.k[s].sum() / gs.n[s].sum())
lo, hi = np.percentile(bs, [2.5, 97.5]); print(f"D (düz) ROI {D.get_D.sum() / len(D):+.3f} [{lo:+.3f}; {hi:+.3f}] | büyük ödeme çıkarılınca (bilgi) {(D.get_D.sum() - D.get_D.max()) / (len(D) - 1):+.3f}")
def sim(kesir):
    kasa = 100.0; tepe = 100.0; dd = 0.0; gunluk = {}
    for gun, x in D.groupby("gun", sort=True):
        k0 = kasa
        for r in x.itertuples():
            if kesir is None: b = 1.0
            else:
                f = (r.p * r.g - 1) / (r.g - 1); b = min(kesir * f * kasa, 0.05 * kasa)
                if b < 0.1: continue
            kasa += b * (r.g * r.kazandi - 1); tepe = max(tepe, kasa); dd = max(dd, 1 - kasa / tepe)
            if kasa <= 0: kasa = 1e-9
        gunluk[gun] = np.log(kasa / k0)
    return kasa, dd, pd.Series(gunluk)
sonuc = {ad: sim(k) for ad, k in (("D", None), ("K25", 0.25), ("K50", 0.5))}
for ad, (k, dd, g) in sonuc.items(): print(f"{ad:4s} son kasa {k:9.2f} | en büyük düşüş %{100 * dd:.0f} | gün başına log büyüme {g.mean():+.5f}")
d = (sonuc["K25"][2] - sonuc["D"][2]).dropna(); bs = [d.sample(len(d), replace=True, random_state=int(rng.integers(1e9))).mean() for _ in range(4000)]
lo, hi = np.percentile(bs, [2.5, 97.5]); print(f"K25 − D gün başına log büyüme {d.mean():+.5f} [{lo:+.5f}; {hi:+.5f}] → KARAR: {'Kelly önerilir' if lo > 0 else 'düz kalır'}")
