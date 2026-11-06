"""T151 raporu (ön kayıt: hipotez_defteri 2026-11-06 10:45)."""
import pickle, numpy as np
rng = np.random.default_rng(151); AD = ["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]
def yuk(v, n): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}{'N' if n else ''}_2025-10.pkl", "rb"))
def fark(a, b, ad, q=(2.5, 97.5)):
    A, B = yuk(*a), yuk(*b); ays = sorted(A); assert sorted(B) == ays
    for m in ays: assert A[m][1] == B[m][1] and A[m][0].shape == B[m][0].shape, m
    pa = np.concatenate([A[m][0] for m in ays]); pb = np.concatenate([B[m][0] for m in ays])
    assert not np.isnan(pa).any() and not np.isnan(pb).any()
    gun = np.array(sum([A[m][1] for m in ays], [])); ug, inv = np.unique(gun, return_inverse=True); D = pa - pb
    print(f"{ad}: {len(gun)} koşu, {len(ug)} gün | A kazanan {pa[:,0].mean():.4f}, B {pb[:,0].mean():.4f}")
    out = {}
    for j, n in enumerate(AD):
        S = np.bincount(inv, weights=D[:, j]); N = np.bincount(inv); bs = []
        for _ in range(1000):
            k = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((k @ S) / (k @ N))
        lo, hi = np.percentile(bs, q); out[n] = (D[:, j].mean(), lo, hi)
        aylar = [np.sign(np.mean(A[m][0][:, j] - B[m][0][:, j])) for m in ays]
        print(f"  {n:8s} {D[:,j].mean():+.5f} [{lo:+.5f}; {hi:+.5f}] (GA %{q[1]-q[0]:.1f}) | ay işareti −:{aylar.count(-1)}/{len(ays)}")
    return out, D, inv, ug
print("T150 PM0 yeniden üretim kontrolü (beklenen 1,9326):", round(np.concatenate([v[0] for v in yuk("MJ", 1).values()])[:, 0].mean(), 4))
P1, *_ = fark(("MJDE", 1), ("MJ", 1), "P1 piyasasız MJDE−MJ", (1.25, 98.75))
k = "aşama-1 ADAYI" if P1["kazanan"][2] < 0 else ("ZARAR" if P1["kazanan"][1] > 0 else "etkisiz"); print("  KARAR P1:", k)
P2, *_ = fark(("MJDE", 0), ("MJ", 0), "P2 piyasalı MJDE−MJ", (1.25, 98.75))
k = "ana model ADAYI (ileri pencere gerekli)" if P2["kazanan"][2] < 0 else ("ZARAR" if P2["kazanan"][1] > 0 else "etkisiz"); print("  KARAR P2:", k)
for n_, ad in ((0, "piyasalı (İKİNCİL H_hafıza)"), (1, "piyasasız (karşı kontrol)")):
    _, Ds, inv, ug = fark(("MJDE1", n_), ("MJ", n_), f"Δ_son {ad}")
    _, De, inv2, ug2 = fark(("MJDEE", n_), ("MJ", n_), f"Δ_eski {ad}")
    D = De[:, 0] - Ds[:, 0]; S = np.bincount(inv, weights=D); N = np.bincount(inv); bs = []
    for _ in range(1000):
        kk = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((kk @ S) / (kk @ N))
    lo, hi = np.percentile(bs, [2.5, 97.5]); print(f"  D = Δ_eski − Δ_son ({ad}) kazanan: {D.mean():+.5f} [{lo:+.5f}; {hi:+.5f}]" + ("  → H_hafıza DESTEK" if (n_ == 0 and hi < 0) else ""))
