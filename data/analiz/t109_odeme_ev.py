"""T107 (pencere doğrulama) + T108 (ödeme modeli, ödeme-ağırlıklı kupon). Ön kayıt: hipotez_defteri T107/T108. Girdi: /tmp/claude-0/pool_v3b.pkl (t107_havuz_uret.py).
python3 data/analiz/t108_odeme_ev.py"""
import os, sys, pickle, itertools
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk.besli import G_P
P = pickle.load(open("/tmp/claude-0/pool_v3b.pkl", "rb")); print("havuz", len(P), flush=True)
PERM = np.array(list(itertools.permutations(range(9), 5)), dtype=np.int16)
def pl_orders(logit, gam, aday, tot_w):
    """aday (9 yerel→at indeksi), W_j = exp(gam_j·logit); tüm koşu paydası tot_w[j]"""
    n = len(aday); pr = np.ones(len(PERM)); sub = np.zeros((len(PERM), 5))
    for j in range(5):
        w = np.exp(gam[j] * (logit - logit.max())); den = np.full(len(PERM), w.sum())
        for k in range(j): den = den - w[aday[PERM[:, k]]]
        pr = pr * w[aday[PERM[:, j]]] / den
    return pr
def smx(s): e = np.exp(s - s.max()); return e / e.sum()
def kupon_ev(args):
    """açgözlü: değer vektörü v ile ΔV/Δmaliyet; B=bütçe (geçerli kombo sayısı)"""
    v, B = args; inset = [np.zeros(9, bool) for _ in range(5)]
    for j in range(5): inset[j][j] = True
    def mask(ins): return ins[0][PERM[:, 0]] & ins[1][PERM[:, 1]] & ins[2][PERM[:, 2]] & ins[3][PERM[:, 3]] & ins[4][PERM[:, 4]]
    m = mask(inset); cnt = int(m.sum()); V = float(v[m].sum())
    while True:
        best = None
        for j in range(5):
            for h in range(9):
                if inset[j][h]: continue
                inset[j][h] = True; mm = mask(inset); c2 = int(mm.sum()); inset[j][h] = False
                if c2 > B or c2 <= cnt: continue
                g = (float(v[mm].sum()) - V) / (c2 - cnt)
                if best is None or g > best[0]: best = (g, j, h, c2, float(v[mm].sum()))
        if best is None: break
        _, j, h, cnt, V = best; inset[j][h] = True
    return [np.where(i)[0] for i in inset], cnt
# --- havuz özellikleri ---
rows = []
for p in P:
    n = len(p["lm"]); pm = smx(p["lm"]); win = [x for x in p["pay"] if x[0] == "SIRALI 5 Lİ BAHİS" and x[2] > 0]; dev = any("DEVİR" in x[0] for x in p["pay"])
    Gm = np.array(G_P); lg = np.log(np.clip(pm, 1e-9, 1)); lp = 0.0; rem = [np.exp(Gm[j] * lg) for j in range(5)]
    for j in range(5): lp += Gm[j] * lg[j] - np.log(rem[j].sum() - sum(rem[j][k] for k in range(j)))
    p.update(n=n, pay_win=max([x[2] for x in win]) if win else 0.0, kendi_devir=dev, lpk=-lp)   # lpk = -log P_piyasa(gerçek sıra)
D = pd.DataFrame([dict(gun=p["gun"], ay=p["ay"], hip=p["key"][1], kosu=int(p["key"][2]), n=p["n"], pay=p["pay_win"], dev=p["kendi_devir"], lpk=p["lpk"]) for p in P])
D["i"] = range(len(D)); D = D.sort_values(["hip", "gun", "kosu"]); dv = {}
for h, g in D.groupby("hip", sort=False):
    last = None
    for r in g.itertuples(): dv[r.i] = bool(last is not None and last[1] and (pd.Timestamp(r.gun) - pd.Timestamp(last[0])).days <= 3); last = (r.gun, r.dev)
D["devirli"] = D.i.map(dv); D = D.sort_values("i").reset_index(drop=True)
for k in ("devirli",): D[k] = D[k].astype(int)
HIP = sorted(D.hip.unique())
def feat(df): return np.column_stack([np.ones(len(df)), df.lpk.values, np.log(df.n.values), df.devirli.values] + [(df.hip.values == h).astype(float) for h in HIP[1:]])
aylar = sorted(D.ay.unique()); out = []; MOD = {}
# --- ödeme modeli, ileri-yürüyüş ---
pr_rows = []
for a in aylar:
    tr = D[(D.ay < a) & (D.pay > 0)]
    if len(tr) < 120: continue
    X = feat(tr); y = np.log(tr.pay.values); b = np.linalg.solve(X.T @ X + 1.0 * np.eye(X.shape[1]), X.T @ y); sig2 = float(((y - X @ b) ** 2).mean()); MOD[a] = (b, sig2)
    te = D[(D.ay == a) & (D.pay > 0)]
    if len(te): pr_rows.append(pd.DataFrame(dict(ay=a, y=np.log(te.pay.values), yh=feat(te) @ b, gun=te.gun.values)))
PR = pd.concat(pr_rows); r2 = 1 - ((PR.y - PR.yh) ** 2).sum() / ((PR.y - PR.y.mean()) ** 2).sum(); bias = float((PR.y - PR.yh).mean())
sl = np.polyfit(PR.yh, PR.y, 1)
out.append(f"T108 ödeme modeli OOS: n={len(PR)} kazanan ödeme, R²={r2:.3f}, ort sapma (log) {bias:+.3f}, kalibrasyon eğimi {sl[0]:.2f}; model ayları {sorted(MOD)[0]}..{sorted(MOD)[-1]}")
# --- kuponlar ---
jobs = []; meta = []
for i, p in enumerate(P):
    a = p["ay"]
    if a not in MOD: continue
    n = p["n"]; pmod = smx(p["gam"][0] * p["S"] if False else p["S"]); aday = np.argsort(-pmod)[:9]
    if n < 9: continue
    Pm = pl_orders(p["S"], p["gam"], aday, None); Pk = pl_orders(p["lm"], G_P, aday, None)
    # kazanan ödeme tahmini: log pay = b0 + b1*(-log Pk) + b2*log n + b3*devirli + hip
    r = D.iloc[i]; b, s2 = MOD[a]; hv = np.array([1.0] + [float(r.hip == h) for h in HIP[1:]])
    mu = b[0] + b[1] * (-np.log(np.clip(Pk, 1e-12, 1))) + b[2] * np.log(r.n) + b[3] * r.devirli + (b[4:] @ hv[1:])
    vE = Pm * np.exp(mu + s2 / 2)
    jobs.append((vE, 96)); jobs.append((Pm, 96)); meta.append(i)
with Pool(2) as pool: res = pool.map(kupon_ev, jobs, chunksize=4)
R_ = []
for q, i in enumerate(meta):
    p = P[i]; r = D.iloc[i]; pmod = smx(p["S"]); aday = np.argsort(-pmod)[:9]; loc = {int(h): k for k, h in enumerate(aday)}
    row = dict(gun=p["gun"], ay=p["ay"], n=p["n"], devirli=int(r.devirli), pay=r.pay)
    for nm, (sets, cnt) in (("ev", res[2 * q]), ("pr", res[2 * q + 1])):
        hit = all((j in loc and loc[j] in set(sets[j].tolist())) for j in range(5)); row[nm + "_hit"] = int(hit); row[nm + "_b"] = cnt * 1.25; row[nm + "_k"] = r.pay if hit else 0.0
    R_.append(row)
R_ = pd.DataFrame(R_); R_.to_pickle("/tmp/claude-0/t109_rows.pkl"); rr = np.random.default_rng(23)
def roi(df, k, b): return (df[k].sum() - df[b].sum()) / max(df[b].sum(), 1e-9)
def ga(df, fn, B=3000):
    ix = df.groupby("gun").indices; ds = list(ix); v = []
    for _ in range(B):
        idx = np.concatenate([ix[ds[j]] for j in rr.integers(0, len(ds), len(ds))]); v.append(fn(df.iloc[idx]))
    return np.percentile(v, [2.5, 97.5])
fd = lambda x: roi(x, "ev_k", "ev_b") - roi(x, "pr_k", "pr_b")
ESKI = ("2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10")
for ad, df in (("TÜM PENCERE", R_), ("BAĞIMSIZ (yeni aylar)", R_[~R_.ay.isin(ESKI)]), ("ESKİ (Nis–Eki 2026)", R_[~~R_.ay.isin(ESKI)])):
    if len(df) == 0: continue
    g = ga(df, fd); out.append(f"{ad}: {len(df)} havuz | EV-kupon vuruş {int(df.ev_hit.sum())} ROI {roi(df,'ev_k','ev_b'):+.1%} | olasılık-kupon vuruş {int(df.pr_hit.sum())} ROI {roi(df,'pr_k','pr_b'):+.1%} | fark {fd(df):+.1%} GA95 [{g[0]:+.1%},{g[1]:+.1%}] | ort bedel {df.ev_b.mean():.0f}/{df.pr_b.mean():.0f}")
# T107 H1/H2 (olasılık-kupon, yeni aylar)
Y = R_[~R_.ay.isin(ESKI)]
for ad, df in (("H1 ≥16 atlı (yeni aylar)", Y[Y.n >= 16]), ("≥16 atlı (eski)", R_[(~~R_.ay.isin(ESKI)) & (R_.n >= 16)]), ("H2 devirli (yeni aylar)", Y[Y.devirli == 1]), ("devirsiz (yeni aylar)", Y[Y.devirli == 0])):
    if len(df) == 0: out.append(f"{ad}: n=0"); continue
    f1 = lambda x: roi(x, "pr_k", "pr_b"); g = ga(df, f1); out.append(f"{ad}: n={len(df)} vuruş {int(df.pr_hit.sum())} ROI {f1(df):+.1%} GA95 [{g[0]:+.1%},{g[1]:+.1%}]")
open("data/analiz/t109_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
