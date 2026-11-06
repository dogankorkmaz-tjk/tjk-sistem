"""T164 (ön kayıt: hipotez_defteri 2026-11-07 00:2x): üçlü / tabela / sıralı 5'li tek kombinasyon değer bahsi; fiyat tahmini (c terimli)."""
import glob, pickle, itertools, math, sys, numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import besli as BS
rng = np.random.default_rng(164)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
TUR = {3: "ÜÇLÜ BAHİS", 4: "TABELA BAHİS", 5: "SIRALI 5 Lİ BAHİS"}
OD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202*.csv.gz"))])
ODM = {}
for r in OD[OD.tur.isin(list(TUR.values()) + [v + " DEVİR" for v in TUR.values()])].itertuples():
    k = len(str(r.kombo).split("/")); dv = "DEVİR" in r.tur
    try: seq = tuple(int(x) for x in str(r.kombo).split("/"))
    except Exception: continue
    o = ODM.setdefault((r.tarih, r.hipodrom, int(r.kosu), k), {"seq": seq, "tutar": 0.0, "devir": True})
    if not dv: o["tutar"] = max(o["tutar"], float(r.tutar)); o["devir"] = False
def pl(P, w_all, G, K):
    out = np.ones(len(P))
    for k in range(K):
        wk = np.power(np.maximum(w_all, 1e-12), G[k]); T = wk.sum(); den = T - sum(wk[P[:, j]] for j in range(k)) if k else T
        out *= wk[P[:, k]] / den
    return out
PERM = {}; KAYIT = []; EG = {3: [], 4: [], 5: []}
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb")); MOD = {}
    for K in (3, 4, 5):
        X = np.array(EG[K])
        if len(X) >= 80:
            A = np.c_[np.ones(len(X)), X[:, 0], X[:, 1]]; beta, *_ = np.linalg.lstsq(A, X[:, 2], rcond=None); s2 = (X[:, 2] - A @ beta).var()
            A0 = np.c_[np.ones(len(X)), X[:, 0]]; b0, *_ = np.linalg.lstsq(A0, X[:, 2], rcond=None); s20 = (X[:, 2] - A0 @ b0).var()
            MOD[K] = (beta, s2, b0, s20)
    yeni = {3: [], 4: [], 5: []}
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; lm = c["L0"][i][:n]; g = list(c["g3"])
        p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        for K in (3, 4, 5):
            od = ODM.get((key[0], key[1], int(key[2]), K))
            if od is None or n < K + 2 or not all(x in nos for x in od["seq"]): continue
            ix = tuple(nos.index(x) for x in od["seq"])
            Pw = np.array([ix]); pmw = pl(Pw, pm, BS.G_P, K)[0]; pmo = pl(Pw, p, g, K)[0]
            if not od["devir"] and od["tutar"] > 0: yeni[K].append((math.log(1 / pmw), math.log(pmo / pmw), math.log(od["tutar"])))
            if K not in MOD: continue
            beta, s2, b0, s20 = MOD[K]
            t = sorted(range(n), key=lambda j: -p[j])[:9]
            P = np.array(list(itertools.permutations(t, K))); pmod = pl(P, p, g, K); pmk = pl(P, pm, BS.G_P, K)
            x1 = np.log(1 / np.maximum(pmk, 1e-15)); x2 = np.log(np.maximum(pmod, 1e-15) / np.maximum(pmk, 1e-15))
            oh = np.exp(beta[0] + beta[1] * x1 + beta[2] * x2 + s2 / 2); oh0 = np.exp(b0[0] + b0[1] * x1 + s20 / 2)
            ev = pmod * oh; ev0 = pmod * oh0
            kaz = np.all(P == np.array(ix), axis=1); getiri = 0.0 if od["devir"] else od["tutar"]
            for th in (1.2, 1.5, 2.0, 3.0):
                sel = ev >= th; sel0 = ev0 >= th
                KAYIT.append(dict(gun=key[0], K=K, th=th, n=int(sel.sum()), hit=int((sel & kaz).any()), getiri=getiri * int((sel & kaz).any()),
                                  n0=int(sel0.sum()), getiri0=getiri * int((sel0 & kaz).any()), kaz_aday=int(kaz.any())))
    for K in (3, 4, 5): EG[K] += yeni[K]
    print(ay, {K: (None if K not in MOD else (round(MOD[K][0][1], 3), round(MOD[K][0][2], 3))) for K in (3, 4, 5)}, flush=True)
D = pd.DataFrame(KAYIT); pickle.dump(D, open("/tmp/claude-0/t164_kayit.pkl", "wb"))
def roi(x, mal, get, q):
    g = x.groupby("gun").agg(m=(mal, "sum"), r=(get, "sum")); g = g[g.m > 0]; ug = g.index.values; bs = []
    for _ in range(3000):
        s = rng.choice(ug, len(ug)); bs.append(g.r[s].sum() / g.m[s].sum() - 1)
    return g.r.sum() / g.m.sum() - 1, np.percentile(bs, q)
for K, ad in ((3, "üçlü"), (4, "tabela"), (5, "sıralı 5'li")):
    print(f"--- {ad} (koşu {D[(D.K == K) & (D.th == 1.2)].shape[0]}, kazanan kombinasyon ilk-9 içinde %{100 * D[(D.K == K) & (D.th == 1.2)].kaz_aday.mean():.0f}) ---")
    for th in (1.2, 1.5, 2.0, 3.0):
        x = D[(D.K == K) & (D.th == th)]; q = (0.833, 99.167) if th == 1.2 else (2.5, 97.5)
        if x.n.sum() == 0: continue
        r, (lo, hi) = roi(x, "n", "getiri", q); r0, _ = roi(x, "n0", "getiri0", q)
        ens = (x.getiri.sum() - x.getiri.max()) / x.n.sum() - 1
        print(f"   EV ≥ {th}: bahis {x.n.sum()} oynanan koşu {(x.n > 0).sum()} isabet {x.hit.sum()} ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}] ({'%98,33 BİRİNCİL' if th == 1.2 else '%95'}) | en büyük çıkarılınca {ens:+.3f} | c=0 (T156 tipi) ROI {r0:+.3f}")
    x = D[(D.K == K) & (D.th == 1.2)]; r, (lo, hi) = roi(x, "n", "getiri", (0.833, 99.167)); print(f"   KARAR ({ad}):", "kârlı ADAY" if lo > 0 else "kârlı değil")
