"""T174 (ön kayıt hipotez_defteri 2026-11-07 02:1x): koşu seçimi — seçim dönemi 2025-10..2026-04, doğrulama 2026-05..10."""
import pickle, glob, numpy as np, pandas as pd
rng = np.random.default_rng(174)
BUYUK = {"istanbul", "ankara", "izmir", "bursa", "adana", "antalya", "kocaeli"}
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
F = pd.read_pickle("/tmp/claude-0/ozellik_tum.pkl"); F["tarih"] = F.tarih.astype(str)
PIST = F.groupby(["tarih", "hipodrom", "kosu"]).pist.first().to_dict()
AT = {}
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        n = len(c["nos"][i]); s = np.array(c["S3"][i][:n]); lm = np.array(c["L0"][i][:n])
        p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        k3 = (key[0], key[1], int(key[2]))
        AT[k3] = dict(buyuk=key[1] in BUYUK, n=n, cim=str(PIST.get(k3, "")).lower().startswith("ç"), kl=float((p * np.log(p / pm)).sum()), fav=float(pm.max()))
# bahis satırları: gun, key, S (yatırılan), r (dönen)
B = {}
d = pickle.load(open("/tmp/claude-0/t169b.pkl", "rb")); x = d[(d.tur == "si") & (d.tip == "kombine")]
B["sıralı ikili kombine (taban)"] = pd.DataFrame(dict(gun=x.gun, key=x.key, S=x.S, r=x.r))
d = pickle.load(open("/tmp/claude-0/t169.pkl", "rb")); x = d[(d.tur == "ik") & (d.tip == "kombine") & (d.U == 0.75)]
B["ikili kombine"] = pd.DataFrame(dict(gun=x.gun, key=x.key, S=x.S, r=x.r))
d, OWN = pickle.load(open("/tmp/claude-0/t170_kayit.pkl", "rb")); x = d[(d.K == 5) & (d.tip == "kombine") & (d.th == 1.2) & (d.B == 1000)].copy()
N = x.hip.map(OWN).astype(float) + x.carry; W = np.maximum(1.0, N / np.where(x.tutar > 0, x.tutar, np.nan))
g = np.where(x.devir, N + 0.75 * x.S, x.u * (N + 0.75 * x.S) / (W + x.u)); x["r"] = np.where(x.u > 0, np.nan_to_num(g), 0.0)
B["sıralı 5'li kombine"] = pd.DataFrame(dict(gun=x.gun, key=list(zip(x.gun, x.hip, x.kosu)), S=x.S, r=x.r))
def roi(y): return y.r.sum() / y.S.sum() - 1 if y.S.sum() > 0 else np.nan
def boot_fark(a, b, q):
    A_ = a.groupby("gun").agg(m=("S", "sum"), r=("r", "sum")); B_ = b.groupby("gun").agg(m=("S", "sum"), r=("r", "sum"))
    J = A_.join(B_, lsuffix="a", rsuffix="b", how="outer").fillna(0); ug = J.index.values; bs = []
    for _ in range(4000):
        j = J.loc[rng.choice(ug, len(ug))]; bs.append(j.ra.sum() / max(j.ma.sum(), 1e-9) - j.rb.sum() / max(j.mb.sum(), 1e-9))
    return np.percentile(bs, q)
print("tarih aralığı:", {k: (v.gun.min(), v.gun.max(), len(v[v.S > 0])) for k, v in B.items()})
for ad, D in B.items():
    D = D[D.S > 0].copy()
    for c_ in ("buyuk", "n", "cim", "kl", "fav"): D[c_] = [AT.get(tuple(k), {}).get(c_, np.nan) for k in D.key]
    D = D.dropna(subset=["n"]); P1 = D[D.gun <= "2026-04-30"]; P2 = D[D.gun >= "2026-05-01"]
    kl_m, fav_m = P1.kl.median(), P1.fav.median()
    BOL = {"hipodrom büyük/küçük": lambda z: z.buyuk.astype(bool), "at sayısı ≤10/≥11": lambda z: z.n <= 10, "pist çim/kum": lambda z: z.cim.astype(bool),
           f"ayrışma yüksek/düşük (KL>{kl_m:.3f})": lambda z: z.kl > kl_m, f"favori güçlü/zayıf (>{fav_m:.2f})": lambda z: z.fav > fav_m}
    print(f"=== {ad}: seçim {len(P1)} koşu ROI {roi(P1):+.3f} | doğrulama {len(P2)} koşu ROI {roi(P2):+.3f}")
    for bad, f in BOL.items():
        m1 = f(P1); a1, b1 = roi(P1[m1]), roi(P1[~m1])
        if abs(a1 - b1) < 0.10:
            print(f"   {bad}: seçimde fark küçük ({a1:+.3f} / {b1:+.3f}) → seçilmedi"); continue
        oyna = m1 if a1 > b1 else ~m1; m2 = f(P2) if a1 > b1 else ~f(P2)
        o2, x2 = P2[m2], P2[~m2]; fk = roi(o2) - roi(x2); lo, hi = boot_fark(o2, x2, [2.5, 97.5]); lb, _ = boot_fark(o2, x2, [0.167, 99.833])
        taraf = "1. taraf" if a1 > b1 else "2. taraf"
        hk = "DOĞRULANDI (Bonferroni de)" if lb > 0 else "doğrulandı (%95)" if lo > 0 else "doğrulanmadı"
        print(f"   {bad}: seçim oyna={taraf} ({max(a1,b1):+.3f} vs {min(a1,b1):+.3f}) | doğrulama oyna {roi(o2):+.3f} ({len(o2)} koşu, {int((o2.r>0).sum())} isabet) vs oynama {roi(x2):+.3f} ({len(x2)}) fark {fk:+.3f} [{lo:+.3f}; {hi:+.3f}] → {hk}")
