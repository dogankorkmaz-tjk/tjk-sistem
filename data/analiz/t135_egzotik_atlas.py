"""T135: sıralı ikili / ikili havuz verimlilik atlası (modelsiz). hipotez_defteri.md ön kaydı 2026-11-06."""
import glob, numpy as np, pandas as pd
rng = np.random.default_rng(135)
def log(*a): print(*a, flush=True)
G = 0.87; BIN = [0, .005, .01, .02, .04, .08, 1.01]; AD = ["<0,5%", "0,5-1%", "1-2%", "2-4%", "4-8%", ">=8%"]
T = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "kosmadi", "p_piyasa"]) for f in sorted(glob.glob("data/temiz/20*.csv.gz")) if f.split("/")[-1][:4] >= "2024"])
T = T[(T.kosmadi != True) & T.p_piyasa.notna()]
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202[456]-*.csv.gz"))]); O = O[O.tur.isin(["SIRALI İKİLİ", "İKİLİ"])]
W = {}
for r in O.itertuples():
    try: a, b = [int(x) for x in str(r.kombo).split("/")]
    except Exception: continue
    W.setdefault((r.tarih, r.hipodrom, int(r.kosu), r.tur), []).append((a, b, float(r.tutar)))
acc = {(t, b): [0.0, 0, []] for t in ("SIRALI İKİLİ", "İKİLİ") for b in range(6)}   # [ödeme toplamı, kombo sayısı] ; gün bazlı liste
dayacc = {}   # (tur,bin,gun)->[odeme,kombo]
n_race = 0
for (t, h, k), g in T.groupby(["tarih", "hipodrom", "kosu"], sort=False):
    if len(g) < 5: continue
    keys = [(t, h, int(k), "SIRALI İKİLİ"), (t, h, int(k), "İKİLİ")]
    if not any(x in W for x in keys): continue
    nos = g.no.astype(int).values; p = g.p_piyasa.values / g.p_piyasa.sum(); pg = p ** G; S = pg.sum()
    Q = p[:, None] * pg[None, :] / (S - pg)[:, None]; np.fill_diagonal(Q, 0)    # Q[i,j]=q(i->j)
    n_race += 1; ix = {n: i for i, n in enumerate(nos)}
    # sıralı ikili
    if keys[0] in W:
        qb = np.digitize(Q, BIN[1:-1]); off = ~np.eye(len(nos), dtype=bool)
        for b in range(6):
            cnt = int(((qb == b) & off & (Q > 0)).sum()); pay = 0.0
            for a, c, tu in W[keys[0]]:
                if a in ix and c in ix and qb[ix[a], ix[c]] == b: pay += tu
            d = dayacc.setdefault(("SIRALI İKİLİ", b, t), [0.0, 0]); d[0] += pay; d[1] += cnt
    if keys[1] in W:
        U = Q + Q.T; iu = np.triu_indices(len(nos), 1); uq = U[iu]; ub = np.digitize(uq, BIN[1:-1])
        for b in range(6):
            cnt = int((ub == b).sum()); pay = 0.0
            for a, c, tu in W[keys[1]]:
                if a in ix and c in ix:
                    i, j = sorted((ix[a], ix[c]))
                    if np.digitize(U[i, j], BIN[1:-1]) == b: pay += tu
            d = dayacc.setdefault(("İKİLİ", b, t), [0.0, 0]); d[0] += pay; d[1] += cnt
log("koşu", n_race)
D = pd.DataFrame([(a, b, t, v[0], v[1]) for (a, b, t), v in dayacc.items()], columns=["tur", "bin", "gun", "pay", "n"])
for tur in ("SIRALI İKİLİ", "İKİLİ"):
    X = D[D.tur == tur]; tot = X.pay.sum() / X.n.sum(); log("====", tur, "havuz geneli ROI %.3f" % tot)
    for b in range(6):
        Y = X[X.bin == b].reset_index(drop=True)
        if Y.n.sum() == 0: continue
        pay = Y.pay.values; n = Y.n.values; roi = pay.sum() / n.sum(); bs = []
        for _ in range(1000):
            k = rng.integers(0, len(Y), len(Y)); bs.append(pay[k].sum() / n[k].sum())
        lo, hi = np.percentile(bs, [0.5, 99.5])
        yr = {y: (Y[Y.gun.str[:4] == y].pay.sum() / max(Y[Y.gun.str[:4] == y].n.sum(), 1)) for y in ("2024", "2025", "2026")}
        log("  %-7s kombo %9d  ROI %.3f [%.3f, %.3f] (%%99)  sapma %+.3f | yıl 2024 %.2f 2025 %.2f 2026 %.2f %s" % (AD[b], n.sum(), roi, lo, hi, roi - tot, yr["2024"], yr["2025"], yr["2026"], "<<< ADAY" if lo > 1 else ""))
log("bitti")
