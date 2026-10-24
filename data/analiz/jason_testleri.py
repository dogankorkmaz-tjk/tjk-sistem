"""TEST 1 (Jason'ı modele ekle) ve TEST 2 (G1-S v2 onayı tüyoyu iyileştirir mi). Ön kayıt: hipotez_defteri 2026-10-24 12:40."""
import os, sys, random
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
from scipy.optimize import minimize_scalar
J = pd.read_pickle("/tmp/claude-0/jason_wf.pkl"); JI = {(r.tarih, r.hipodrom, int(r.kosu), int(r.no)): (r.z2, r.pj, r.p_piyasa, r.ganyan, r.kazandi) for r in J.itertuples()}
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]; D = []      # (ay, r, s_v2, zJ, gam)
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
    for r in te:
        k = [JI.get((r["key"][0], r["key"][1], int(r["key"][2]), n)) for n in r["nos"]]
        if any(x is None for x in k): continue
        D.append((a, r, skor(r, t1, bg), np.array([x[0] for x in k]), np.r_[1.0, t1[10:14]], k))
print("koşu", len(D), flush=True)
def nll(c, items):
    tot = 0.0
    for a, r, s, z, gam, _ in items:
        S = (s + c * z)[None, :]; out, _, _ = steps(S, gam); tot += sum(o.sum() for o in out)
    return tot
def olc(c, items):
    o = []
    for a, r, s, z, gam, _ in items:
        S = (s + c * z)[None, :]; out, _, _ = steps(S, gam); o.append([x[0] for x in out])
    return np.cumsum(np.array(o), axis=1)
# ---- TEST 1
base, ek, gun = [], [], []; cs = {}
for a in [x for x in test if x >= "2026-07"]:
    tr = [x for x in D if x[0] < a]; te = [x for x in D if x[0] == a]
    c = minimize_scalar(lambda c: nll(c, tr) + 20.0 * c * c, bounds=(-3, 3), method="bounded").x; cs[a] = round(c, 3)
    base.append(olc(0.0, te)); ek.append(olc(c, te)); gun += [x[1]["gun"] for x in te]
print("c katsayıları (ay: c):", cs)
base = np.concatenate(base); ek = np.concatenate(ek); gun = np.array(gun); ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}; random.seed(9)
print(f"TEST 1: {len(gun)} koşu, {len(ug)} gün")
for j, ad in enumerate(["kazanan", "sıralı ikili", "sıralı üçlü", "ilk 4", "ilk 5"]):
    d = ek[:, j] - base[:, j]; bs = [d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(800)]
    print(f"  {ad:14s} v2 {base[:,j].mean():.4f} | v2+Jason {ek[:,j].mean():.4f} | fark {d.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
# ---- TEST 2
rows = []
for a, r, s, z, gam, k in D:
    p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(r["lm"])
    for i, n in enumerate(r["nos"]):
        pj, pp, g_, kz = k[i][1], k[i][2], k[i][3], k[i][4]
        if pj >= 0.06 and pj / pp >= 1.30:
            rows.append((r["gun"], p[i] / pm[i], float(g_) if kz == 1 else 0.0, kz == 1))
T = pd.DataFrame(rows, columns=["gun", "v2oran", "getiri", "kaz"]); T["onay"] = T.v2oran >= 1.0
print(f"TEST 2: tüyo sayısı {len(T)} (2026-04..10, tüm D koşuları)")
def roi(df): return df.getiri.sum() / len(df) - 1
ugT = sorted(T.gun.unique()); gT = {g: T[T.gun == g] for g in ugT}
def bsroi(sel):
    L = []
    for _ in range(1000):
        df = pd.concat([gT[random.choice(ugT)] for _ in ugT]); df = df[sel(df)] if sel else df; L.append(roi(df) if len(df) else np.nan)
    return np.nanpercentile(L, [2.5, 97.5])
for ad, df in (("tüm tüyolar", T), ("G1-S onaylı (oran≥1)", T[T.onay]), ("onaysız (oran<1)", T[~T.onay])):
    print(f"  {ad:24s} n={len(df):4d} isabet {df.kaz.mean():.1%} ROI {roi(df):+.1%}")
fk = []
for _ in range(1000):
    df = pd.concat([gT[random.choice(ugT)] for _ in ugT]); a_, b_ = df[df.onay], df[~df.onay]
    if len(a_) and len(b_): fk.append(roi(a_) - roi(b_))
print(f"  onaylı − onaysız ROI farkı {roi(T[T.onay])-roi(T[~T.onay]):+.1%} [{np.percentile(fk,2.5):+.1%},{np.percentile(fk,97.5):+.1%}]")
for lo, hi in ((0, .8), (.8, 1.0), (1.0, 1.2), (1.2, 9)):
    df = T[(T.v2oran >= lo) & (T.v2oran < hi)]; print(f"  v2oran [{lo},{hi}) n={len(df)} ROI {roi(df):+.1%} isabet {df.kaz.mean():.1%}" if len(df) else "")
