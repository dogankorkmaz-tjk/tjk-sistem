"""T162 raporu (ön kayıt: hipotez_defteri 2026-11-06 23:3x). Birincil MJT9S − MJT9 kazanan, %97,5 (2 karşılaştırma); betimsel ilk5 ve MJT9S − MJ."""
import pickle, numpy as np
rng = np.random.default_rng(162); AD = ["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]
def yuk(v, n): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}{'N' if n else ''}_2025-10.pkl", "rb"))
def kars(A, B, q):
    ays = sorted(A); assert sorted(B) == ays
    for m in ays: assert A[m][1] == B[m][1]
    D = np.concatenate([A[m][0] for m in ays]) - np.concatenate([B[m][0] for m in ays]); gun = np.array(sum([A[m][1] for m in ays], []))
    ug, inv = np.unique(gun, return_inverse=True); N = np.bincount(inv); out = {}
    for j, nm in enumerate(AD):
        S = np.bincount(inv, weights=D[:, j]); bs = []
        for _ in range(1000):
            k = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((k @ S) / (k @ N))
        out[nm] = (D[:, j].mean(), *np.percentile(bs, q), sum(np.mean(A[m][0][:, j] - B[m][0][:, j]) < 0 for m in ays), len(ays))
    return out, len(gun), len(ug)
for n, tur in ((1, "piyasasız"), (0, "piyasalı")):
    for base, rol, q in (("MJT9", "BİRİNCİL", (1.25, 98.75)), ("MJ", "betimsel", (2.5, 97.5))):
        o, nk, ng = kars(yuk("MJT9S", n), yuk(base, n), q)
        print(f"{tur} MJT9S − {base} ({rol}; {nk} koşu, {ng} gün; GA {'%97,5' if rol == 'BİRİNCİL' else '%95'})")
        for nm in AD: m, lo, hi, a, t = o[nm]; print(f"   {nm:8s} {m:+.5f} [{lo:+.5f}; {hi:+.5f}] ay −:{a}/{t}")
        if rol == "BİRİNCİL":
            m, lo, hi, a, t = o["kazanan"]
            print("   KARAR:", ("ana model ADAYI (ileri pencere)" if n == 0 else "aşama-1 ADAYI") if hi < 0 else ("ZARAR" if lo > 0 else "etkisiz"))
