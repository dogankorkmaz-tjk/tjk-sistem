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
def combos(s, gam, k):
    out = {}; n = len(s)
    for c in itertools.permutations(range(n), k):
        pr = 1.0; used = []
        for j, i in enumerate(c):
            z = np.exp(gam[j] * (s - s.max())); m = np.ones(n, bool); m[used] = False; pr *= z[i] / z[m].sum(); used.append(i)
        out[c] = pr
    return out
def kup(a):
    kind, p, gam = a; p = [float(x) for x in p]; G = list(gam)
    if kind == "t24": o = tabela.kupon(p, 24, G)
    elif kind == "t120": o = tabela.kupon(p, 120, G)
    else: o = besli.kupon_g(p, int(kind[1:]), G=G)
    return None if o is None else o[0]
ST = {}; POOL = {"TABELA": [], "S5": []}
for a in test:
    for k, r in enumerate(RES[a]["te"]):
        n = len(r["lm"]); key = r["key"]; pr = PAY.get(key)
        if not pr: continue
        pk = np.exp(r["lm"]); mod = {"v2": (RES[a]["S2"][k, :n], RES[a]["gam"]), "v3": (RES[a]["S3g"][k, :n], RES[a]["g3"])}
        for tur, kk in (("SIRALI İKİLİ", 2), ("ÜÇLÜ BAHİS", 3), ("İKİLİ", 2)):
            if tur not in pr: continue
            pay = {}
            for c, t in pr[tur]: pay[c] = pay.get(c, 0) + t
            A = E._kombolar(dict(enumerate(pk)), kk)
            if tur == "İKİLİ":
                A2 = {}
                for c, v in A.items(): A2[tuple(sorted(c))] = A2.get(tuple(sorted(c)), 0) + v
                A = A2
            for m, (s, gam) in mod.items():
                B = combos(s, gam, kk)
                if tur == "İKİLİ":
                    B2 = {}
                    for c, v in B.items(): B2[tuple(sorted(c))] = B2.get(tuple(sorted(c)), 0) + v
                    B = B2
                sec = [c for c in A if A[c] >= E.ESIK[tur] and B[c] / A[c] >= 1.15]
                if not sec: continue
                ST.setdefault((m, tur), []).append((r["gun"], len(sec) * E.BIRIM[tur], sum(pay.get(tuple(r["nos"][i] for i in c), 0.0) for c in sec)))
        if "TABELA BAHİS" in pr or "TABELA BAHİS SIRASIZ" in pr: POOL["TABELA"].append((a, k, r, pr, mod))
        if "SIRALI 5 Lİ BAHİS" in pr or "SIRALI 5 Lİ BAHİS DEVİR" in pr: POOL["S5"].append((a, k, r, pr, mod))
random.seed(13)
def roi_rep(L, ad):
    gun = sorted({x[0] for x in L}); gg = {g: [x for x in L if x[0] == g] for g in gun}
    def roi(G): b = sum(x[1] for g in G for x in gg[g]); return (sum(x[2] for g in G for x in gg[g]) - b) / b
    bs = [roi([random.choice(gun) for _ in gun]) for _ in range(600)]
    print(f"{ad:28s} n={len(L):4d} ROI {roi(gun):+7.1%} [{np.percentile(bs,2.5):+.1%},{np.percentile(bs,97.5):+.1%}]", flush=True)
print("\n== EGZOTİK ROI (seçim kuralı oran≥1,15) ==")
for key in sorted(ST): roi_rep(ST[key], f"{key[0]} {key[1]}")
for bahis, kinds, unit, nL in (("TABELA", ("t24", "t120"), 1.5, 4), ("S5", ("b96",), 1.25, 5)):
    for kind in kinds:
        for m in ("v2", "v3"):
            with Pool(2) as pool: out = pool.map(kup, [(kind, smx(x[4][m][0]), x[4][m][1]) for x in POOL[bahis]], chunksize=8)
            L = []
            for x, sets in zip(POOL[bahis], out):
                if sets is None: continue
                hit = all(i in sets[i] for i in range(nL)); pr = x[3]
                if bahis == "TABELA":
                    v = sum(1 for z in itertools.product(*sets) if len(set(z)) == 4); npm = sum(1 for z in itertools.product(*sets) if len(set(z)) == 4 and set(z) == {0, 1, 2, 3})
                    sirali = max([t for _, t in pr.get("TABELA BAHİS", [(0, 0.0)])]); sirasiz = max([t for _, t in pr.get("TABELA BAHİS SIRASIZ", [(0, 0.0)])])
                    kz = (sirali if hit else 0.0) + (npm - (1 if hit else 0)) * sirasiz
                else:
                    v = besli.gecerli_say(sets); kz = max([t for _, t in pr.get("SIRALI 5 Lİ BAHİS", [(0, 0.0)])]) if hit else 0.0
                L.append((x[2]["gun"], v * unit, kz))
            roi_rep(L, f"{bahis} {kind} {m} (tutma {sum(1 for l in L if l[2]>0)})")
