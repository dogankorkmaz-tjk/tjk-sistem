"""Devir (havuz yapısı) etkisi. Ön kayıt: hipotez_defteri 2026-10-24 19:00."""
import os, sys, glob, random
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/*.csv.gz"))])
O = O[O.tur.isin(["SIRALI 5 Lİ BAHİS", "SIRALI 5 Lİ BAHİS DEVİR"])]
tp = piyasa_gamma(R); G = np.r_[1.0, tp[10:14]]; print("gam", G.round(3), flush=True)
RK = {r["key"]: r for r in R}
def prob(p, order):
    p = np.array(p, float).copy(); a = 1.0
    for k, i in enumerate(order):
        w = p ** G[k]; a *= w[i] / w.sum(); p[i] = 0.0
    return a
pool = {}; devir = {}
for q in O.itertuples():
    key = (q.tarih, q.hipodrom, int(q.kosu)); pool.setdefault(key, []).append(q)
rows = []
for hip in sorted({k[1] for k in pool}):
    ks = sorted([k for k in pool if k[1] == hip], key=lambda k: (k[0], k[2])); prev_dev = None
    for k in ks:
        r = RK.get(k); rs = pool[k]
        dv = any(q.tur.endswith("DEVİR") for q in rs)
        din = 0.0
        if prev_dev is not None and (pd.Timestamp(k[0]) - pd.Timestamp(prev_dev[0][0])).days <= 3: din = prev_dev[1]
        if r is not None and not dv:
            pm = np.exp(r["lm"]); pm = pm / pm.sum(); Q = 0.0; ok = True
            for q in rs:
                try: order = [r["nos"].index(int(x)) for x in str(q.kombo).split("/")]
                except Exception: ok = False; break
                Q += prob(pm, order) * q.tutar / 1.25
            if ok: rows.append((r["gun"], k, din, Q))
        prev_dev = (k, max(q.tutar for q in rs)) if dv else None
D = pd.DataFrame(rows, columns=["gun", "key", "devir", "Q"]); print("havuz koşusu", len(D), "devirli", (D.devir > 0).sum(), flush=True)
random.seed(3)
def ort(x): return x.Q.mean()
def boot(sel_a, sel_b, n=1000):
    gl = sorted(D.gun.unique()); by = {g: D[D.gun == g] for g in gl}; out = []
    for _ in range(n):
        S = pd.concat([by[random.choice(gl)] for _ in gl]); a = S[sel_a(S)].Q.mean(); b = S[sel_b(S)].Q.mean(); out.append(a - b)
    return np.nanpercentile(out, [2.5, 97.5])
a = lambda S: S.devir > 0; b = lambda S: S.devir == 0
print("Q devirsiz %.3f (n=%d) | devirli %.3f (n=%d) | fark %.3f %s" % (D[D.devir == 0].Q.mean(), (D.devir == 0).sum(), D[D.devir > 0].Q.mean(), (D.devir > 0).sum(), D[D.devir > 0].Q.mean() - D[D.devir == 0].Q.mean(), boot(a, b).round(3)))
print("medyan Q devirsiz %.3f devirli %.3f" % (D[D.devir == 0].Q.median(), D[D.devir > 0].Q.median()))
d2 = D[D.devir > 0].copy()
if len(d2) > 8:
    d2["dilim"] = pd.qcut(d2.devir, 3, labels=["küçük", "orta", "büyük"])
    print(d2.groupby("dilim", observed=True).agg(n=("Q", "size"), devir_ort=("devir", "mean"), Q_ort=("Q", "mean"), Q_med=("Q", "median")).round(3).to_string())
print("korelasyon(log devir, Q) devirliler:", round(float(np.corrcoef(np.log(d2.devir), d2.Q)[0, 1]), 3), "| Spearman:", round(float(d2.devir.corr(d2.Q, method="spearman")), 3))
