"""T154 raporu (ön kayıt: hipotez_defteri 2026-11-06 12:30). MJP − MJ; 2 karşılaştırma → %97,5 GA (gün-küme bootstrap 1000).
Birincil: ilk5 birikimli PL kaybı, GA üst <0. Koruma: kazanan GA alt < +0,0005."""
import pickle, json, numpy as np
rng = np.random.default_rng(154); AD = ["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]; Q = (1.25, 98.75)
def yuk(v, n): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}{'N' if n else ''}_2025-10.pkl", "rb"))
print("taban kontrolü: MJ piyasasız", round(np.concatenate([x[0] for x in yuk("MJ", 1).values()])[:, 0].mean(), 4), "(1,9326) | MJ piyasalı",
      round(np.concatenate([x[0] for x in yuk("MJ", 0).values()])[:, 0].mean(), 4), "(1,8433)")
for n, tur in ((1, "piyasasız"), (0, "piyasalı")):
    A, B = yuk("MJP", n), yuk("MJ", n); ays = sorted(A); assert sorted(B) == ays
    for m in ays: assert A[m][1] == B[m][1] and A[m][0].shape == B[m][0].shape, (n, m)
    pa = np.concatenate([A[m][0] for m in ays]); pb = np.concatenate([B[m][0] for m in ays]); assert not np.isnan(pa).any()
    gun = np.array(sum([A[m][1] for m in ays], [])); ug, inv = np.unique(gun, return_inverse=True); D = pa - pb; N = np.bincount(inv)
    print(f"{tur}: {len(gun)} koşu, {len(ug)} gün | MJP kazanan {pa[:,0].mean():.4f} ilk5 {pa[:,4].mean():.4f} − MJ {pb[:,0].mean():.4f} / {pb[:,4].mean():.4f}")
    GA = {}
    for j, nm in enumerate(AD):
        S = np.bincount(inv, weights=D[:, j]); bs = []
        for _ in range(1000):
            k = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((k @ S) / (k @ N))
        lo, hi = np.percentile(bs, Q); GA[nm] = (lo, hi); ay = [np.sign(np.mean(A[m][0][:, j] - B[m][0][:, j])) for m in ays]
        print(f"   {nm:8s} {D[:,j].mean():+.5f} [{lo:+.5f}; {hi:+.5f}] (%97,5) | ay −:{ay.count(-1)}/{len(ays)}")
    kor = GA["kazanan"][0] < 0.0005
    if GA["ilk5"][1] < 0 and kor: k_ = "ana model ADAYI (ileri pencere gerekli)" if n == 0 else "aşama-1 ADAYI"
    elif GA["ilk5"][0] > 0: k_ = "ZARAR"
    elif not kor: k_ = "koruma bozuldu (kazanan kötüleşti) → eklenmez"
    else: k_ = "etkisiz"
    print(f"   koruma (kazanan GA alt < +0,0005): {'sağlandı' if kor else 'BOZULDU'} | KARAR: {k_}")
    try:
        dl = json.load(open(f"data/analiz/t154_delta{'N' if n else ''}.json")); son = dl["delta"][max(dl["delta"])]
        print("   δ (son eğitim):", ", ".join(f"{f} {v:+.3f}" for f, v in sorted(zip(dl["ozellik"], son), key=lambda x: -abs(x[1]))))
    except Exception as e:
        print("   δ okunamadı:", e)
