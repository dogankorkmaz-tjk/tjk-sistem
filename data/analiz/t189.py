"""T189: PLASE (ilk 2) piyasa-yanlış-fiyat geriye testi. Ön kayıt: hipotez_defteri T189. Actions: t189.yml."""
import os, sys, math, itertools
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import glob, pandas as pd
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/*.csv.gz"))])
PAY = {}
for q in O[O.tur == "PLASE"].itertuples():
    PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu)), {})[str(q.kombo)] = PAY.get((q.tarih, q.hipodrom, int(q.kosu)), {}).get(str(q.kombo), 0.0) + float(q.tutar)
GUN = {}
def ekle(ad, gun, v):
    d = GUN.setdefault(ad, {}); d[gun] = d.get(gun, 0) + np.array(v, float)
def ilk2(s, g0, g1):
    z = s - s.max(); w1 = np.exp(g0 * z); p1 = w1 / w1.sum(); w2 = np.exp(g1 * z); W2 = w2.sum()
    q = p1 / np.maximum(W2 - w2, 1e-12)
    return p1 + w2 * (q.sum() - q)
BINS = [.1, .2, .35, .5]
def kutu(p): return int(np.searchsorted(BINS, p, side="right"))
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= os.environ.get("T189_BAS", "2025-03")]
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    tp = piyasa_gamma(tr); t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1) if a >= "2026-04" else None
    gm = [1.0] + list(tp[10:14]); gg = [1.0] + list(t1[10:14])
    for r in te:
        py = PAY.get((r["key"][0], r["key"][1], r["key"][2]))
        n = len(r["nos"])
        if not py or n < 4: continue
        sm_, sg_ = skor(r, tp), skor(r, t1, bg)
        pm2, pg2 = ilk2(sm_, gm[0], gm[1]), ilk2(sg_, gg[0], gg[1])
        ode = np.array([py.get(str(no), 0.0) for no in r["nos"]]); hit = (ode > 0).astype(float)
        ekle("R0", r["gun"], [n, ode.sum(), hit.sum(), 1])
        for b in range(len(BINS) + 1):
            m = np.array([kutu(p) == b for p in pm2])
            if m.any(): ekle(f"A{b}", r["gun"], [m.sum(), pm2[m].sum(), pg2[m].sum(), hit[m].sum(), ode[m].sum()])
        for esik in (1.15, 1.10, 1.25, 1.40):
            f = (pg2 / np.maximum(pm2, 1e-12) >= esik) & (pg2 >= 0.10); N = int(f.sum())
            if N == 0: continue
            tag = "ANA" if esik == 1.15 else f"s{esik}"
            ekle(f"D_{tag}", r["gun"], [N, ode[f].sum(), hit[f].sum(), 1, pg2[f].sum(), pm2[f].sum()])
            if esik == 1.15:
                tm = np.argsort(-pm2)[:N]; tg = np.argsort(-pg2)[:N]
                ekle("D_ref_piyasaTopN", r["gun"], [N, ode[tm].sum(), hit[tm].sum(), 1, pg2[tm].sum(), pm2[tm].sum()])
                ekle("D_ref_modelTopN", r["gun"], [N, ode[tg].sum(), hit[tg].sum(), 1, pg2[tg].sum(), pm2[tg].sum()])
    print(a, len(te), flush=True)
rng = np.random.default_rng(1890)
def boot(d, B=3000):
    gunler = sorted(d); M = np.array([d[g] for g in gunler]); W = rng.multinomial(len(gunler), np.ones(len(gunler)) / len(gunler), size=B).astype(float)
    return M.sum(0), W @ M
def roi_satir(ad, q=(2.5, 97.5)):
    d = GUN.get(ad)
    if not d: print(f"  {ad}: yok"); return
    tot, S = boot(d); roi = tot[1] / tot[0] - 1; ga = np.percentile(S[:, 1] / S[:, 0] - 1, q)
    s = f"  {ad:18s} bahis {tot[0]:8.0f} ödeme {tot[1]:9.0f} isabet {int(tot[2]):5d} ROI {roi:+.1%} [{ga[0]:+.1%};{ga[1]:+.1%}]"
    if len(tot) > 5: s += f"  beklenen isabet: model {tot[4]:.1f} piyasa {tot[5]:.1f}"
    print(s, flush=True)
print("\n=== R0 (koşudaki tüm atlara 1 TL) ===")
roi_satir("R0")
print("\n=== A kalibrasyon: kutu (piyasa P(ilk2)) → n, Σpm, Σpg, isabet, ROI ===")
for b in range(len(BINS) + 1):
    d = GUN.get(f"A{b}")
    if not d: continue
    tot, S = boot(d, 2000); ga = np.percentile(S[:, 4] / S[:, 0] - 1, (2.5, 97.5))
    print(f"  kutu{b}: n={int(tot[0])} Σpm {tot[1]:.0f} Σpg {tot[2]:.0f} isabet {int(tot[3])} oran_pm {tot[3]/tot[1]:.3f} oran_pg {tot[3]/tot[2]:.3f} ROI {tot[4]/tot[0]-1:+.1%} [{ga[0]:+.1%};{ga[1]:+.1%}]")
print("\n=== D değer işareti ===")
roi_satir("D_ANA", q=(0.83, 99.17))
for ad in ("D_ref_piyasaTopN", "D_ref_modelTopN", "D_s1.1", "D_s1.25", "D_s1.4"): roi_satir(ad)
print("\nKARAR (ön kayıt): ANA ROI GA(Bonf.) alt > 0 → ADAY; nokta>0 ama alt<=0 → işaret; nokta<=0 → YOK.")
