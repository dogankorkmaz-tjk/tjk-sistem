"""T152-S raporu: sahip sızıntı kontrolü (ön kayıt: hipotez_defteri 2026-11-06 12:20). Aynı kural, %99,17."""
import pickle, numpy as np
rng = np.random.default_rng(152); AD = ["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]; Q = (100 / 12, 100 - 100 / 12)   # %99,17 GA (6 karşılaştırma)
Q = (0.41667, 99.58333)
def yuk(v, n): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}{'N' if n else ''}_2025-10.pkl", "rb"))
print("taban kontrolü: MJ piyasasız", round(np.concatenate([x[0] for x in yuk("MJ", 1).values()])[:, 0].mean(), 4), "(T150/T151: 1,9326) | MJ piyasalı",
      round(np.concatenate([x[0] for x in yuk("MJ", 0).values()])[:, 0].mean(), 4), "(T151: 1,8433)")
for V, ad in (("MJSYG", "T146 soy/yaş, yarış-günü sahibi"),):
    for n, tur in ((1, "piyasasız"), (0, "piyasalı")):
        A, B = yuk(V, n), yuk("MJ", n); ays = sorted(A); assert sorted(B) == ays
        for m in ays: assert A[m][1] == B[m][1] and A[m][0].shape == B[m][0].shape, (V, n, m)
        pa = np.concatenate([A[m][0] for m in ays]); pb = np.concatenate([B[m][0] for m in ays]); assert not np.isnan(pa).any()
        gun = np.array(sum([A[m][1] for m in ays], [])); ug, inv = np.unique(gun, return_inverse=True); D = pa - pb; N = np.bincount(inv)
        print(f"{ad} · {tur}: {len(gun)} koşu, {len(ug)} gün | {V} {pa[:,0].mean():.4f} − MJ {pb[:,0].mean():.4f}")
        for j, nm in enumerate(AD):
            S = np.bincount(inv, weights=D[:, j]); bs = []
            for _ in range(1000):
                k = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((k @ S) / (k @ N))
            lo, hi = np.percentile(bs, Q); ay = [np.sign(np.mean(A[m][0][:, j] - B[m][0][:, j])) for m in ays]
            print(f"   {nm:8s} {D[:,j].mean():+.5f} [{lo:+.5f}; {hi:+.5f}] (%99,17) | ay −:{ay.count(-1)}/{len(ays)}")
            if j == 0:
                k_ = ("aşama-1 ADAYI" if n else "ana model ADAYI (ileri pencere gerekli)") if hi < 0 else ("ZARAR" if lo > 0 else "etkisiz")
                print(f"   KARAR: {k_}")

print("BETİMSEL: MJSYG − MJSY (sızıntı payı; + = yarış-günü sahibiyle kötüleşme)")
for n, tur in ((1, "piyasasız"), (0, "piyasalı")):
    A, B = yuk("MJSYG", n), yuk("MJSY", n); ays = sorted(A)
    for m in ays: assert A[m][1] == B[m][1]
    D = np.concatenate([A[m][0] for m in ays]) - np.concatenate([B[m][0] for m in ays])
    print(f"   {tur}: kazanan {D[:,0].mean():+.5f}  ilk5 {D[:,4].mean():+.5f}")

