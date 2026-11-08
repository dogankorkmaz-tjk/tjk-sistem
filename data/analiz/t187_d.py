"""T187-D: sıralı bahislerde (sıralı ikili, üçlü, tabela) piyasa-yanlış-fiyat ölçümü. Ön kayıt: hipotez_defteri T187-D. Actions: t187_d.yml."""
import os, sys, math, itertools
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import glob, pandas as pd
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/*.csv.gz"))])
TURLER = {"SIRALI İKİLİ": (2, 1.0, 0.02), "ÜÇLÜ BAHİS": (3, 2.0, 0.005), "TABELA BAHİS": (4, 1.5, 0.001)}
PAY = {}
for q in O[O.tur.isin(TURLER)].itertuples():
    PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu), q.tur), {}).setdefault(str(q.kombo), 0.0)
    PAY[(q.tarih, q.hipodrom, int(q.kosu), q.tur)][str(q.kombo)] += float(q.tutar)
UG = 9; PERM = {}
def perms(n, k):
    if (n, k) not in PERM: PERM[(n, k)] = np.array(list(itertools.permutations(range(n), k)), dtype=np.int32)
    return PERM[(n, k)]
def kombo_p(s, gam, uni, k):
    """Evren (indeks listesi) içindeki tüm sıralı k'lı kombinasyonların PL olasılığı; adım j: exp(gam_j * s)."""
    n = len(s); P = perms(len(uni), k); u = np.array(uni); pr = np.ones(len(P)); W = []
    for j in range(k):
        z = gam[j] * s; z = z - z.max(); w = np.exp(z); W.append(w)
    for j in range(k):
        d = W[j].sum() - sum((W[j][u[P[:, m]]] for m in range(j)), 0.0)
        pr = pr * W[j][u[P[:, j]]] / d
    return P, pr
BINS = {2: [.01, .02, .04, .08], 3: [.002, .005, .01, .03], 4: [.0005, .001, .003, .01]}
def kutu(p, k): return int(np.searchsorted(BINS[k], p, side="right"))
GUN = {}   # (tur, tip) -> gün -> vektör
def ekle(tur, ad, gun, v):
    d = GUN.setdefault((tur, ad), {}); d[gun] = d.get(gun, 0) + np.array(v, float)
R0 = {}
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= os.environ.get("T187_BAS", "2025-03")]
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1) if a >= "2026-04" else None
    gm = [1.0] + list(tp[10:14]); gg = [1.0] + list(t1[10:14])
    for r in te:
        sm_, sg_ = skor(r, tp), skor(r, t1, bg); n = len(sm_); nos = r["nos"]
        pg1 = np.exp(sg_ - sg_.max()); uni = list(np.argsort(-pg1)[:min(UG, n)])
        for tur, (k, bir, taban) in TURLER.items():
            py = PAY.get((r["key"][0], r["key"][1], r["key"][2], tur))
            if not py or n < k + 1: continue
            gerc = "/".join(str(nos[i]) for i in range(k))
            if gerc not in py: continue      # kazanan kombinasyonun ödemesi yok → koşu dışı (iptal/ortak bitiş)
            odeme = py[gerc]
            if k <= 3 and n <= 20:           # R0: tüm sıralı kombinasyonlar
                nc = math.perm(n, k); ekle(tur, "R0", r["gun"], [nc * bir, odeme, 1])
            P, pm_ = kombo_p(sm_, gm, uni, k); _, pg_ = kombo_p(sg_, gg, uni, k)
            ig = [i for i in range(len(P)) if tuple(P[i]) == tuple(range(k))] if all(i in uni for i in range(k)) else []
            gercek_ix = None
            if all(i in uni for i in range(k)):
                pos = [uni.index(i) for i in range(k)]; gercek_ix = int(np.where((P == np.array(pos)).all(1))[0][0])
            # A: kutular
            for b in range(len(BINS[k]) + 1):
                m = np.array([kutu(p, k) == b for p in pm_])
                if not m.any(): continue
                hit = 1 if (gercek_ix is not None and m[gercek_ix]) else 0
                ekle(tur, f"A{b}", r["gun"], [m.sum(), pm_[m].sum(), pg_[m].sum(), hit, m.sum() * bir, hit * odeme])
            # D: bayrak
            for esik in (1.3, 1.2, 1.5, 2.0):
                f = (pg_ / np.maximum(pm_, 1e-12) >= esik) & (pg_ >= taban); N = int(f.sum())
                if N == 0: continue
                tag = "ANA" if esik == 1.3 else f"s{esik}"
                def arm(mask): 
                    h = 1 if (gercek_ix is not None and mask[gercek_ix]) else 0
                    return [N * bir, h * odeme, h, 1]
                ekle(tur, f"D_{tag}_model", r["gun"], arm(f) + [pg_[f].sum(), pm_[f].sum()])
                if esik == 1.3:
                    top_m = np.zeros(len(P), bool); top_m[np.argsort(-pm_)[:N]] = True
                    top_g = np.zeros(len(P), bool); top_g[np.argsort(-pg_)[:N]] = True
                    ekle(tur, "D_ref_piyasaTopN", r["gun"], arm(top_m) + [pg_[top_m].sum(), pm_[top_m].sum()])
                    ekle(tur, "D_ref_modelTopN", r["gun"], arm(top_g) + [pg_[top_g].sum(), pm_[top_g].sum()])
    print(a, len(te), flush=True)
rng = np.random.default_rng(1870)
def boot(d, B=3000, q=(2.5, 97.5)):
    gunler = sorted(d); M = np.array([d[g] for g in gunler]); W = rng.multinomial(len(gunler), np.ones(len(gunler)) / len(gunler), size=B).astype(float)
    return M.sum(0), W @ M, q
def roi_satir(tur, ad, q=(2.5, 97.5), ek=True):
    d = GUN.get((tur, ad))
    if not d: print(f"  {ad}: yok"); return None
    tot, S, _ = boot(d); roi = tot[1] / tot[0] - 1; r_ = S[:, 1] / S[:, 0] - 1; ga = np.percentile(r_, q)
    s = f"  {ad:20s} maliyet {tot[0]:9.0f} ödeme {tot[1]:9.0f} isabet {int(tot[2]):4d} koşu {int(tot[3]):5d} ROI {roi:+.1%} [{ga[0]:+.1%};{ga[1]:+.1%}]"
    if len(tot) > 5: s += f"  beklenen isabet: model {tot[4]:.1f} piyasa {tot[5]:.1f}"
    print(s, flush=True); return roi, ga
print("\n=== R0 birim doğrulaması (tüm kombinasyonlar) ===")
for tur in TURLER:
    d = GUN.get((tur, "R0"))
    if d:
        T = np.array(list(d.values())).sum(0); print(f"{tur}: koşu {int(T[2])} maliyet {T[0]:.0f} ödeme {T[1]:.0f} ROI {T[1]/T[0]-1:+.1%}")
print("\n=== A kalibrasyon: kutu → n, Σp_piyasa, Σp_model, isabet, isabet/Σpm, isabet/Σpg, tüm-kutu-ROI [GA] ===")
for tur, (k, bir, tb) in TURLER.items():
    print(tur)
    for b in range(len(BINS[k]) + 1):
        d = GUN.get((tur, f"A{b}"))
        if not d: continue
        tot, S, _ = boot(d, 2000); ga = np.percentile(S[:, 5] / S[:, 4] - 1, (2.5, 97.5))
        lo = ([0] + BINS[k])[b]; print(f"  p_piyasa≥{lo}: n={int(tot[0])} Σpm {tot[1]:.1f} Σpg {tot[2]:.1f} isabet {int(tot[3])} oran_pm {tot[3]/tot[1]:.3f} oran_pg {tot[3]/tot[2]:.3f} ROI {tot[5]/tot[4]-1:+.1%} [{ga[0]:+.1%};{ga[1]:+.1%}]", flush=True)
print("\n=== D değer işareti (Bonferroni %95/3 → %0,83–%99,17) ===")
for tur in TURLER:
    print(tur)
    for ad in ("D_ANA_model", "D_ref_piyasaTopN", "D_ref_modelTopN", "D_s1.2_model", "D_s1.5_model", "D_s2.0_model"):
        roi_satir(tur, ad, q=(0.83, 99.17) if ad == "D_ANA_model" else (2.5, 97.5))
print("\nKARAR (ön kayıt): ANA ROI GA(Bonf.) alt > 0 → ADAY; nokta>0 ama alt<=0 → işaret; nokta<=0 → YOK.")
