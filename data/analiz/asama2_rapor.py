"""4. adım raporu: aşama 2 birleşik kazanç = pseudo-R²(Benter piyasalı) − pseudo-R²(kalibre piyasa), Benter 1994 ölçüsü (birleşik − piyasa).
Girdi: /tmp/claude-0/cache_MJ_<ay>.pkl (T151 MJ NOLP=0: v3_galopsuz ve v3 galoplu), /tmp/claude-0/kalpiyasa_2025-10.pkl. Koşu anahtarıyla eşleştirilir."""
import pickle, glob, numpy as np
rng = np.random.default_rng(42); K = pickle.load(open("/tmp/claude-0/kalpiyasa_2025-10.pkl", "rb"))
B, G, Kp, U, gun, ham = [], [], [], [], [], []
for a in sorted(K):
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{a}.pkl", "rb")); kl, kg, kk = K[a]; ix = {k: i for i, k in enumerate(kk)}
    cn = pickle.load(open(f"/tmp/claude-0/cache_MJN_{a}.pkl", "rb")); iu = {k: i for i, k in enumerate(cn["keys"])}   # eşit/ham piyasa referansı NOLP=1 önbelleğinde
    c["ref_uni"] = [cn["ref_uni"][iu[k]] if k in iu else np.full(5, np.nan) for k in c["keys"]]; c["ref_mkt"] = [cn["ref_mkt"][iu[k]] if k in iu else np.full(5, np.nan) for k in c["keys"]]
    ort = [(i, ix[k]) for i, k in enumerate(c["keys"]) if k in ix and k in iu]
    for i, j in ort:
        B.append(c["v3_galopsuz"][i]); G.append(c["v3"][i] if a >= "2026-03" else np.full(5, np.nan)); Kp.append(np.cumsum(kl[j])); U.append(c["ref_uni"][i]); ham.append(c["ref_mkt"][i]); gun.append(c["gun"][i])
    print(a, "harness", len(c["keys"]), "kalpiyasa", len(kk), "eşleşen", len(ort))
B, G, Kp, U, ham = map(np.array, (B, G, Kp, U, ham)); gun = np.array(gun); ug, inv = np.unique(gun, return_inverse=True)
def r2(L): return 1 - L[:, 0].mean() / U[:, 0].mean()
print(f"\n{len(gun)} koşu, {len(ug)} gün | kazanan kaybı: Benter {B[:,0].mean():.4f}, kalibre piyasa {Kp[:,0].mean():.4f}, ham piyasa {ham[:,0].mean():.4f}, eşit {U[:,0].mean():.4f}")
print(f"pseudo-R²: Benter {r2(B):.4f}, kalibre piyasa {r2(Kp):.4f}, ham piyasa {r2(ham):.4f}")
def ga(x, y, msk=None):
    m = np.ones(len(x), bool) if msk is None else msk; i2 = inv[m]; ug2 = np.unique(i2); S1 = np.bincount(i2, weights=x[m], minlength=len(ug)); S2 = np.bincount(i2, weights=y[m], minlength=len(ug)); bs = []
    for _ in range(1000):
        k = np.bincount(rng.choice(ug2, len(ug2)), minlength=len(ug)); bs.append((k @ S2 - k @ S1) / (k @ np.bincount(i2, weights=U[m, 0], minlength=len(ug))))
    return (y[m].mean() - x[m].mean()) / U[m, 0].mean(), *np.percentile(bs, [2.5, 97.5])
d, lo, hi = ga(B[:, 0], Kp[:, 0]); print(f"AŞAMA 2 birleşik kazanç (Benter − kalibre piyasa, pseudo-R²): {d:+.4f} [{lo:+.4f}; {hi:+.4f}]  | Benter 1994: +0,0090 (9 faktör, OOS), +0,0178 (tam, örnek tipi belirsiz)")
m = ~np.isnan(G[:, 0])
d, lo, hi = ga(B[:, 0], Kp[:, 0], m); print(f"  aynı aylar (2026-03..10) galopsuz: {d:+.4f} [{lo:+.4f}; {hi:+.4f}]")
d, lo, hi = ga(np.where(m, G[:, 0], 0), Kp[:, 0], m); print(f"  aynı aylar (2026-03..10) galoplu (üretim Benter v3): {d:+.4f} [{lo:+.4f}; {hi:+.4f}]")
for j, n in enumerate(["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]):
    print(f"  {n:8s} Benter {B[:,j].mean():.4f} kalibre piyasa {Kp[:,j].mean():.4f} fark {B[:,j].mean()-Kp[:,j].mean():+.4f}")
