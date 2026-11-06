"""T156 raporu (ön kayıt: hipotez_defteri 2026-11-06 20:45). Büyük ödemeler DAHİL ROI; gün-küme bootstrap 2000; birincil %97,5 (2 karşılaştırma)."""
import pickle, numpy as np, pandas as pd
rng = np.random.default_rng(1560)
K = pd.DataFrame(pickle.load(open("/tmp/claude-0/t156_kayit.pkl", "rb")))
print("koşu", K.key.nunique(), "gün", K.gun.nunique(), "ay", K.ay.min(), "..", K.ay.max())


def roi_ga(x, q=(2.5, 97.5), sutun="getiri"):
    g = x.groupby("gun").agg(m=("maliyet", "sum"), r=(sutun, "sum")); ug = g.index.values; bs = []
    for _ in range(2000):
        s = rng.choice(ug, len(ug)); m = g.m[s].sum(); bs.append(g.r[s].sum() / m - 1 if m else np.nan)
    return g.r.sum() / g.m.sum() - 1, np.nanpercentile(bs, q)


def fark_ga(a, b, q):
    ga = a.groupby("gun").agg(m=("maliyet", "sum"), r=("getiri", "sum")); gb = b.groupby("gun").agg(m=("maliyet", "sum"), r=("getiri", "sum"))
    ug = ga.index.union(gb.index).values; ga = ga.reindex(ug, fill_value=0); gb = gb.reindex(ug, fill_value=0); bs = []
    for _ in range(2000):
        s = rng.choice(ug, len(ug)); bs.append(ga.r[s].sum() / ga.m[s].sum() - gb.r[s].sum() / gb.m[s].sum())
    return ga.r.sum() / ga.m.sum() - gb.r.sum() / gb.m.sum(), np.percentile(bs, q)


for B in (48, 96, 150):
    print(f"--- bütçe {B} ---")
    for s in "ABC":
        x = K[(K.B == B) & (K.s == s) & (K.oyna == 1)]
        r, (lo, hi) = roi_ga(x); dv, _ = roi_ga(x, sutun="getiri_dv")
        ens = (x.getiri.sum() - x.getiri.max()) / x.maliyet.sum() - 1 if len(x) else np.nan
        print(f"   {s}: oynanan {len(x):4d} isabet {int(x.isabet.sum()):3d} maliyet {x.maliyet.sum():10.0f} getiri {x.getiri.sum():10.0f} ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}] (%95) | DEVİR dahil {dv:+.3f} | en büyük çıkarılınca (bilgi) {ens:+.3f} | ort. tutma {x.tutma.mean():.4f}, ort. EV/maliyet {(x.ev / x.maliyet).mean():.2f}")
x96 = K[K.B == 96]
d, (lo, hi) = fark_ga(x96[(x96.s == "B") & (x96.oyna == 1)], x96[(x96.s == "A") & (x96.oyna == 1)], (1.25, 98.75))
print(f"BİRİNCİL (1) bütçe 96 ROI(B) − ROI(A) {d:+.3f} [{lo:+.3f}; {hi:+.3f}] (%97,5) → {'EV kurucu ADAY' if lo > 0 else 'aday değil'}")
r, (lo, hi) = roi_ga(x96[(x96.s == "C") & (x96.oyna == 1)], (1.25, 98.75))
print(f"BİRİNCİL (2) bütçe 96 ROI(C) {r:+.3f} [{lo:+.3f}; {hi:+.3f}] (%97,5) → {'C kârlı ADAY (ileri pencere)' if lo > 0 else 'kârlı değil'}")
