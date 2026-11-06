"""T165 (ön kayıt: hipotez_defteri 2026-11-07 00:3x): üçlü/tabela/sıralı 5'li değer bahsi; birim fiyat, 20 TL asgari, bütçe sınırı, havuz etkisi."""
import glob, pickle, itertools, math, sys, numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import besli as BS
rng = np.random.default_rng(165)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
TUR = {3: "ÜÇLÜ BAHİS", 4: "TABELA BAHİS", 5: "SIRALI 5 Lİ BAHİS"}; BIRIM = {3: 2.0, 4: 1.5, 5: 1.25}; N0 = {3: 150000.0, 4: 75000.0, 5: 120000.0}
BUTCE = (500, 1000, 2500, 10 ** 9); ESIK = (1.0, 1.2, 1.5, 2.0); NCARP = (0.5, 1.0, 2.0, None)     # None = havuz etkisiz
OD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202*.csv.gz"))]); ODM = {}
for r in OD[OD.tur.isin(list(TUR.values()) + [v + " DEVİR" for v in TUR.values()])].itertuples():
    try: seq = tuple(int(x) for x in str(r.kombo).split("/"))
    except Exception: continue
    o = ODM.setdefault((r.tarih, r.hipodrom, int(r.kosu), len(seq)), {"seq": seq, "tutar": 0.0, "devir": True})
    if "DEVİR" not in r.tur: o["tutar"] = max(o["tutar"], float(r.tutar)); o["devir"] = False
def pl(P, w_all, G, K):
    out = np.ones(len(P))
    for k in range(K):
        wk = np.power(np.maximum(w_all, 1e-12), G[k]); T = wk.sum(); den = T - sum(wk[P[:, j]] for j in range(k)) if k else T
        out *= wk[P[:, k]] / den
    return out
KAYIT = []; EG = {3: [], 4: [], 5: []}
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb")); MOD = {}
    for K in (3, 4, 5):
        X = np.array(EG[K])
        if len(X) >= 80:
            A = np.c_[np.ones(len(X)), X[:, 0], X[:, 1]]; beta, *_ = np.linalg.lstsq(A, X[:, 2], rcond=None); MOD[K] = (beta, (X[:, 2] - A @ beta).var())
    yeni = {3: [], 4: [], 5: []}
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; lm = c["L0"][i][:n]; g = list(c["g3"])
        p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        for K in (3, 4, 5):
            od = ODM.get((key[0], key[1], int(key[2]), K))
            if od is None or n < K + 2 or not all(x in nos for x in od["seq"]): continue
            ix = tuple(nos.index(x) for x in od["seq"]); Pw = np.array([ix])
            pmw = pl(Pw, pm, BS.G_P, K)[0]; pmo = pl(Pw, p, g, K)[0]
            if not od["devir"] and od["tutar"] > 0: yeni[K].append((math.log(1 / pmw), math.log(pmo / pmw), math.log(od["tutar"])))
            if K not in MOD: continue
            beta, s2 = MOD[K]; t = sorted(range(n), key=lambda j: -p[j])[:9]
            P = np.array(list(itertools.permutations(t, K))); pmod = pl(P, p, g, K); pmk = pl(P, pm, BS.G_P, K)
            oh = np.exp(beta[0] + beta[1] * np.log(1 / np.maximum(pmk, 1e-15)) + beta[2] * np.log(np.maximum(pmod, 1e-15) / np.maximum(pmk, 1e-15)) + s2 / 2)
            oran = pmod * oh / BIRIM[K]; sira = np.argsort(-oran); kaz = np.all(P == np.array(ix), axis=1)
            tutar = 0.0 if od["devir"] else od["tutar"]
            for th in ESIK:
                adayi = sira[oran[sira] >= th]
                for B in BUTCE:
                    sec = adayi[: int(B // BIRIM[K])]; S = len(sec) * BIRIM[K]
                    if S < 20: KAYIT.append(dict(gun=key[0], K=K, th=th, B=B, S=0.0, hit=0, **{f"g{x}": 0.0 for x in ("05", "1", "2", "yok")})); continue
                    hit = bool(kaz[sec].any()); r = dict(gun=key[0], K=K, th=th, B=B, S=S, hit=int(hit))
                    for nc, ad in zip(NCARP, ("05", "1", "2", "yok")):
                        if not hit or tutar == 0: r["g" + ad] = 0.0; continue
                        if nc is None: r["g" + ad] = tutar; continue
                        N = max(N0[K] * nc, tutar); r["g" + ad] = tutar * (N + S * 0.75) / (N + tutar)
                    KAYIT.append(r)
    for K in (3, 4, 5): EG[K] += yeni[K]
    print(ay, "tamam", flush=True)
D = pd.DataFrame(KAYIT); pickle.dump(D, open("/tmp/claude-0/t165_kayit.pkl", "wb"))
def roi(x, col, q):
    g = x.groupby("gun").agg(m=("S", "sum"), r=(col, "sum")); g = g[g.m > 0]; ug = g.index.values; bs = []
    for _ in range(3000):
        s = rng.choice(ug, len(ug)); bs.append(g.r[s].sum() / g.m[s].sum() - 1)
    return g.r.sum() / g.m.sum() - 1, np.percentile(bs, q)
for K, ad in ((3, "üçlü"), (4, "tabela"), (5, "sıralı 5'li")):
    x = D[(D.K == K) & (D.th == 1.2) & (D.B == 1000)]; o = x[x.S > 0]
    r, (lo, hi) = roi(x, "g1", (0.833, 99.167))
    print(f"=== {ad}: BİRİNCİL (eşik 1,2, bütçe 1.000 TL, havuz N={N0[K]:,.0f}) oynanan koşu {len(o)}, ort. bahis {o.S.mean():,.0f} TL, isabet {int(o.hit.sum())} → ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}] (%98,33) → {'KÂRLI ADAY' if lo > 0 else 'kârlı değil'}")
    for col, nm in (("g05", "havuz ×0,5"), ("g2", "havuz ×2"), ("gyok", "havuz etkisiz")):
        r, (lo, hi) = roi(x, col, (2.5, 97.5)); print(f"      {nm:14s} ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}]")
    for th in ESIK:
        for B in BUTCE:
            if (th, B) == (1.2, 1000): continue
            x2 = D[(D.K == K) & (D.th == th) & (D.B == B)]; o2 = x2[x2.S > 0]
            if not len(o2): continue
            r, (lo, hi) = roi(x2, "g1", (2.5, 97.5))
            print(f"   eşik {th} bütçe {'sınırsız' if B > 1e8 else B}: koşu {len(o2)} ort. {o2.S.mean():,.0f} TL isabet {int(o2.hit.sum())} ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}]")
