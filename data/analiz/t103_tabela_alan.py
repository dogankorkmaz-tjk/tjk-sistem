"""T103: tabela alan büyüklüğü + değer filtresi (ön kayıt hipotez_defteri T103). python3 data/analiz/t103_tabela_alan.py"""
"""v3 doğrulama: aylık işaret tutarlılığı + egzotik ROI (v2 vs v3). Ön kayıt: hipotez_defteri 2026-10-24 12:45 (sızıntı denetimi/tutarlılık/ROI maddeleri)."""
import os, sys, glob, itertools, random
from multiprocessing import Pool
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_v3.py")).read(), "entegre_v3", "exec"))
from tjk import besli, tabela, egzotik as E
def smx(s): e = np.exp(s - s.max()); return e / e.sum()
print("\n== AYLIK TUTARLILIK (v3 − v2, ortalama nats/koşu) ==")
for a in test:
    d_ = RES[a]["v3"] - RES[a]["v2"]; print(a, len(d_), " ".join(f"{x:+.4f}" for x in d_.mean(0)), "(kazanan ikili üçlü ilk4 ilk5)")
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/2026-*.csv.gz"))]); PAY = {}
for q in O.itertuples():
    kk = None
    if q.tur in E.K:
        kk = tuple(int(z) for z in str(q.kombo).split("/")); kk = tuple(sorted(kk)) if q.tur == "İKİLİ" else kk
    PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu)), {}).setdefault(q.tur, []).append((kk, float(q.tutar)))
from tjk.besli import G_P
def smx(s): e = np.exp(s - s.max()); return e / e.sum()
POOL = []
for a in test:
    for k, r in enumerate(RES[a]["te"]):
        pr = PAY.get(r["key"])
        if pr and ("TABELA BAHİS" in pr or "TABELA BAHİS SIRASIZ" in pr): POOL.append((a, r, pr, RES[a]["S3g"][k, :len(r["lm"])], RES[a]["g3"]))
print("tabela koşu", len(POOL), flush=True)
def kupon2(args):
    kind, p, pk, gam = args; G = list(gam); p = [float(x) for x in p]; pk = [float(x) for x in pk]
    Wp, Tp = tabela._W(pk, G_P)
    if kind in ("t24", "t120"):
        o = tabela.kupon(p, 24 if kind == "t24" else 120, G)
        if o is None: return None
        sets, pm_ = o; return sets, pm_, tabela._prob(Wp, Tp, sets)
    W, T = tabela._W(p, G); sr = sorted(range(len(p)), key=lambda i: -p[i]); sets = [sr[:5]] * 4
    return sets, tabela._prob(W, T, sets), tabela._prob(Wp, Tp, sets)
rows = []
for kind in ("t24", "t120", "s5"):
    with Pool(2) as pool: out = pool.map(kupon2, [(kind, smx(x[3]), smx(x[1]["lm"]), x[4]) for x in POOL], chunksize=8)
    for x, o in zip(POOL, out):
        if o is None: continue
        sets, pm_, pq = o; pr = x[2]; hit = all(i in sets[i] for i in range(4)); n = len(x[1]["lm"])
        v = sum(1 for z in itertools.product(*sets) if len(set(z)) == 4); npm = sum(1 for z in itertools.product(*sets) if len(set(z)) == 4 and set(z) == {0, 1, 2, 3})
        sirali = max([t for _, t in pr.get("TABELA BAHİS", [(0, 0.0)])]); sirasiz = max([t for _, t in pr.get("TABELA BAHİS SIRASIZ", [(0, 0.0)])])
        kz = (sirali if hit else 0.0) + (npm - (1 if hit else 0)) * sirasiz
        rows.append((x[1]["gun"], x[0], kind, n, v * 1.5, kz, int(hit or npm > 0), pm_ / max(pq, 1e-9)))
import pandas as pd
D = pd.DataFrame(rows, columns=["gun", "ay", "kind", "n", "bedel", "kz", "tuttu", "oran"]); D.to_pickle("/tmp/claude-0/t103.pkl")
D["sinif"] = pd.cut(D.n, [0, 12, 15, 99], labels=["<=12", "13-15", ">=16"]); D["filt"] = np.where(D.oran >= 1.15, "oran>=1.15", "oran<1.15")
D["yari"] = np.where(D.ay <= "2026-07", "Nis-Tem", "Agu-Eki")
rr = np.random.default_rng(21)
def roi_ga(df, B=3000):
    if len(df) == 0: return None
    ix = df.groupby("gun").indices; ds = list(ix); b = df.bedel.values; k = df.kz.values; v = []
    for _ in range(B):
        s = rr.choice(len(ds), len(ds)); idx = np.concatenate([ix[ds[j]] for j in s]); v.append((k[idx].sum() - b[idx].sum()) / b[idx].sum())
    return (k.sum() - b.sum()) / b.sum(), np.percentile(v, [2.5, 97.5])
def fark_ga(a, b, B=3000):
    ug = sorted(set(a.gun) | set(b.gun)); ia = a.groupby("gun").indices; ib = b.groupby("gun").indices; f = []
    for _ in range(B):
        sm = rr.choice(len(ug), len(ug)); ba = ka = bb = kb = 0.0
        for g in (ug[j] for j in sm):
            if g in ia: ba += a.bedel.values[ia[g]].sum(); ka += a.kz.values[ia[g]].sum()
            if g in ib: bb += b.bedel.values[ib[g]].sum(); kb += b.kz.values[ib[g]].sum()
        if ba and bb: f.append((ka - ba) / ba - (kb - bb) / bb)
    ra = (a.kz.sum() - a.bedel.sum()) / a.bedel.sum(); rb = (b.kz.sum() - b.bedel.sum()) / b.bedel.sum()
    return ra - rb, np.percentile(f, [2.5, 97.5])
out = [f"T103: tabela koşu {len(POOL)}; kuponlar: t24, t120 (sıralı), s5 (sırasız 5 at); v3 ileri-yürüyüş 2026-04..10"]
for kind in ("t24", "t120", "s5"):
    X = D[D.kind == kind]; r0 = roi_ga(X); out.append(f"== {kind}: tüm {len(X)} koşu ROI {r0[0]:+.1%} [{r0[1][0]:+.1%},{r0[1][1]:+.1%}] tutma {int(X.tuttu.sum())}")
    for s_ in ("<=12", "13-15", ">=16"):
        Y = X[X.sinif == s_]
        if len(Y) == 0: continue
        r1 = roi_ga(Y); y1 = [roi_ga(Y[Y.yari == h])[0] if len(Y[Y.yari == h]) else float("nan") for h in ("Nis-Tem", "Agu-Eki")]
        out.append(f"   alan {s_:6s} n={len(Y):3d} tutma {int(Y.tuttu.sum()):2d} ROI {r1[0]:+.1%} [{r1[1][0]:+.1%},{r1[1][1]:+.1%}] | yarılar Nis-Tem {y1[0]:+.1%} Agu-Eki {y1[1]:+.1%}")
    for f_ in ("oran>=1.15", "oran<1.15"):
        Y = X[X.filt == f_]
        if len(Y): r1 = roi_ga(Y); out.append(f"   {f_:11s} n={len(Y):3d} tutma {int(Y.tuttu.sum()):2d} ROI {r1[0]:+.1%} [{r1[1][0]:+.1%},{r1[1][1]:+.1%}]")
    A = X[X.filt == "oran>=1.15"]; B = X[X.filt == "oran<1.15"]
    if len(A) and len(B): d_, g_ = fark_ga(A, B); out.append(f"   H2 fark (filtreli−filtresiz) {d_:+.1%} GA95 [{g_[0]:+.1%},{g_[1]:+.1%}]")
open("data/analiz/t103_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
