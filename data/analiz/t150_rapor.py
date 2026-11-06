"""T150 raporu (ön kayıt: hipotez_defteri 2026-11-06 04:10). Girdi: /tmp/claude-0/v3_elo2MJN_2025-10.pkl, v3_elo2MJN_g_2025-10.pkl, v3_nolp_ref_2025-10.pkl"""
import pickle, numpy as np
rng = np.random.default_rng(150)
X = pickle.load(open("/tmp/claude-0/v3_elo2MJN_2025-10.pkl", "rb")); G = pickle.load(open("/tmp/claude-0/v3_elo2MJN_g_2025-10.pkl", "rb"))
R = pickle.load(open("/tmp/claude-0/v3_nolp_ref_2025-10.pkl", "rb"))
AD = ["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]
def rapor(ad, ays, S):
    p = np.concatenate([S[a][0] for a in ays]); m = np.concatenate([R[a][0] for a in ays]); u = np.concatenate([R[a][1] for a in ays])
    gun = np.array(sum([S[a][1] for a in ays], [])); ug, inv = np.unique(gun, return_inverse=True)
    print(f"{ad} [{ays[0]}..{ays[-1]}] {len(gun)} koşu, {len(ug)} gün; kontrol: NaN p {int(np.isnan(p).sum())}, m {int(np.isnan(m).sum())}, u {int(np.isnan(u).sum())}")
    for j, n in enumerate(AD):
        Sp, Sm, Su = (np.bincount(inv, weights=x[:, j]) for x in (p, m, u)); N = np.bincount(inv)
        rho = (Su.sum() - Sp.sum()) / (Su.sum() - Sm.sum()); bs = []
        for _ in range(1000):
            k = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((k @ Su - k @ Sp) / (k @ Su - k @ Sm))
        lo, hi = np.percentile(bs, [2.5, 97.5]); P, M_, U = p[:, j].mean(), m[:, j].mean(), u[:, j].mean()
        print(f"  {n:8s} kayıp model {P:.4f} piyasa {M_:.4f} eşit {U:.4f} | pseudo-R² model {1-P/U:.4f} piyasa {1-M_/U:.4f} | Ρ {rho:.3f} [{lo:.3f}, {hi:.3f}]")
        if j == 0:
            for e in (0.82, 1.02):
                k = "AŞILDI" if lo > e else ("altında" if hi < e else "ayırt edilemedi")
                print(f"     eşik {e}: {k}")
ays = sorted(X); rapor("PM0 (ANA)", ays, X)
for a in ays: 
    p = X[a][0][:, 0].mean(); m = R[a][0][:, 0].mean(); u = R[a][1][:, 0].mean(); print(f"    {a} n={len(X[a][1])} PM0 {p:.4f} piyasa {m:.4f} eşit {u:.4f} Ρ {(u-p)/(u-m):.3f}")
ga = [a for a in sorted(G) if a >= "2026-03"]
if ga: rapor("PM0g (galoplu, betimsel)", ga, G); rapor("PM0 aynı aylar (kıyas)", ga, X)
