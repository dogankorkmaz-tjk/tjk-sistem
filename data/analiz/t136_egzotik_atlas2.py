"""T136: ÜÇLÜ BAHİS ve SIRALI 5'Lİ havuz verimlilik atlası (modelsiz). hipotez_defteri.md ön kaydı 2026-11-06."""
import glob, numpy as np, pandas as pd
rng = np.random.default_rng(136)
def log(*a): print(*a, flush=True)
GP = [1.0, .87, .74, .74, .74]
T = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "kosmadi", "p_piyasa"]) for f in sorted(glob.glob("data/temiz/20*.csv.gz")) if f.split("/")[-1][:4] >= "2024"])
T = T[(T.kosmadi != True) & T.p_piyasa.notna()]
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202[456]-*.csv.gz"))])
HAV = {"ÜÇLÜ BAHİS": dict(k=3, bins=[.001, .003, .01, .03], ad=["<0,1%", "0,1-0,3%", "0,3-1%", "1-3%", ">=3%"], bedel=(1.0, 2.0), tur=["ÜÇLÜ BAHİS"], devir=[]),
       "SIRALI 5'Lİ": dict(k=5, bins=[1e-7, 1e-6, 1e-5, 1e-4, 1e-3], ad=["<1e-7", "1e-7..1e-6", "1e-6..1e-5", "1e-5..1e-4", "1e-4..1e-3", ">=1e-3"], bedel=(1.0, 1.25), tur=["SIRALI 5 Lİ BAHİS"], devir=["SIRALI 5 Lİ BAHİS DEVİR"])}
def hepsi(p, k):
    n = len(p); probs = p.copy(); used = np.eye(n, dtype=bool)
    for L in range(1, k):
        pg = p ** GP[L]; S = pg.sum(); su = used @ pg
        cand = pg[None, :] / (S - su)[:, None]; cand[used] = 0.0
        pr = (probs[:, None] * cand).ravel(); idx = np.flatnonzero(pr > 0)
        pi, pj = np.divmod(idx, n); u2 = used[pi].copy(); u2[np.arange(len(pi)), pj] = True; used = u2; probs = pr[idx]
    return probs
def winp(p, seq):
    pr = p[seq[0]]
    for L in range(1, len(seq)):
        pg = p ** GP[L]; pr *= pg[seq[L]] / (pg.sum() - pg[list(seq[:L])].sum())
    return pr
for ad, c in HAV.items():
    k = c["k"]; X = O[O.tur.isin(c["tur"])]; XD = O[O.tur.isin(c["devir"])] if c["devir"] else X.iloc[0:0]
    W = {}; 
    for r in X.itertuples():
        try: seq = [int(x.replace(",", "")) if x.isdigit() else None for x in str(r.kombo).split("/")]
        except Exception: continue
        if len(seq) == k and None not in seq: W.setdefault((r.tarih, r.hipodrom, int(r.kosu)), []).append((seq, float(r.tutar)))
    DV = set((r.tarih, r.hipodrom, int(r.kosu)) for r in XD.itertuples())
    nb = len(c["bins"]) + 1; dayacc = {}; atl = 0; nr = 0
    for (t, h, kk), g in T.groupby(["tarih", "hipodrom", "kosu"], sort=False):
        key = (t, h, int(kk))
        if key not in W and key not in DV: continue
        if len(g) < k + 1: continue
        if len(g) > 16: atl += 1; continue
        nos = g.no.astype(int).values; p = g.p_piyasa.values / g.p_piyasa.sum(); ix = {n: i for i, n in enumerate(nos)}
        pr = hepsi(p, k); cnt = np.bincount(np.digitize(pr, c["bins"]), minlength=nb); pay = np.zeros(nb)
        for seq, tu in W.get(key, []):
            if all(s in ix for s in seq): pay[np.digitize(winp(p, [ix[s] for s in seq]), c["bins"])] += tu
        nr += 1
        for b in range(nb):
            d = dayacc.setdefault((b, t), [0.0, 0]); d[0] += pay[b]; d[1] += int(cnt[b])
    D = pd.DataFrame([(b, t, v[0], v[1]) for (b, t), v in dayacc.items()], columns=["bin", "gun", "pay", "n"])
    log("====", ad, "koşu", nr, "atlanan(n>16)", atl, "devir koşu", len(DV))
    for bd in c["bedel"]:
        tot = D.pay.sum() / bd / D.n.sum(); gecerli = 0.5 <= tot <= 0.9
        log("  -- birim hipotezi bedel=%.2f: havuz geneli ROI %.3f %s" % (bd, tot, "(plausibl)" if gecerli else "(plausibl değil)"))
        for b in range(nb):
            Y = D[D.bin == b].reset_index(drop=True)
            if Y.n.sum() == 0: continue
            pay = Y.pay.values / bd; n = Y.n.values; roi = pay.sum() / n.sum(); bs = []
            for _ in range(1000):
                kx = rng.integers(0, len(Y), len(Y)); bs.append(pay[kx].sum() / n[kx].sum())
            lo, hi = np.percentile(bs, [0.5, 99.5])
            log("     %-12s kombo %12d  ROI %.3f [%.3f, %.3f] %s" % (c["ad"][b], n.sum(), roi, lo, hi, "<<< ADAY" if (lo > 1 and gecerli) else ""))
log("bitti")
