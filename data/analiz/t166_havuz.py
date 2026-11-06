"""T166 (ön kayıt: hipotez_defteri 2026-11-07 00:4x): T165 seçimi + veriye dayalı havuz (5'li ardışık devir farkları, devreden tutar, tek-bilen devir kazancı)."""
import glob, pickle, itertools, math, sys, numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import besli as BS
rng = np.random.default_rng(166)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
TUR = {3: "ÜÇLÜ BAHİS", 4: "TABELA BAHİS", 5: "SIRALI 5 Lİ BAHİS"}; BIRIM = {3: 2.0, 4: 1.5, 5: 1.25}
OD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202*.csv.gz"))]); ODM = {}
for r in OD[OD.tur.isin(list(TUR.values()) + [v + " DEVİR" for v in TUR.values()])].itertuples():
    try: seq = tuple(int(x) for x in str(r.kombo).split("/"))
    except Exception: continue
    o = ODM.setdefault((r.tarih, r.hipodrom, int(r.kosu), len(seq)), {"seq": seq, "tutar": 0.0, "devir": True, "devir_tutar": 0.0})
    if "DEVİR" in r.tur: o["devir_tutar"] = max(o["devir_tutar"], float(r.tutar))
    else: o["tutar"] = max(o["tutar"], float(r.tutar)); o["devir"] = False
# --- 5'li havuz: ardışık devir farkları ve devreden tutar
B5 = sorted(((k[1], k[0], k[2]), v) for k, v in ODM.items() if k[3] == 5)
OWN = {}; CARRY = {}; onceki = {}
for (h, t, kn), v in B5:
    p = onceki.get(h)
    CARRY[(t, h, kn)] = p["devir_tutar"] if (p and p["devir"]) else 0.0
    if p and p["devir"] and v["devir"]: OWN.setdefault(h, []).append(v["devir_tutar"] - p["devir_tutar"])
    onceki[h] = v
BUYUK = {"istanbul", "ankara", "izmir", "bursa", "adana", "antalya", "kocaeli"}
grup = {g: np.median([x for h, L in OWN.items() for x in L if (h in BUYUK) == g]) for g in (True, False)}
OWNMED = {h: (np.median(OWN[h]) if h in OWN and len(OWN[h]) >= 3 else grup[h in BUYUK]) for h in {k[1] for k in ODM}}
print("5'li kendi havuz medyanı:", {h: round(v) for h, v in sorted(OWNMED.items())}, "| grup", {k: round(v) for k, v in grup.items()})
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
            kk = (key[0], key[1], int(key[2]), K); od = ODM.get(kk)
            if od is None or n < K + 2 or not all(x in nos for x in od["seq"]): continue
            ix = tuple(nos.index(x) for x in od["seq"]); Pw = np.array([ix]); pmw = pl(Pw, pm, BS.G_P, K)[0]; pmo = pl(Pw, p, g, K)[0]
            if not od["devir"] and od["tutar"] > 0: yeni[K].append((math.log(1 / pmw), math.log(pmo / pmw), math.log(od["tutar"])))
            if K not in MOD: continue
            beta, s2 = MOD[K]; t = sorted(range(n), key=lambda j: -p[j])[:9]
            P = np.array(list(itertools.permutations(t, K))); pmod = pl(P, p, g, K); pmk = pl(P, pm, BS.G_P, K)
            oh = np.exp(beta[0] + beta[1] * np.log(1 / np.maximum(pmk, 1e-15)) + beta[2] * np.log(np.maximum(pmod, 1e-15) / np.maximum(pmk, 1e-15)) + s2 / 2)
            oran = pmod * oh / BIRIM[K]; sira = np.argsort(-oran); kaz = np.all(P == np.array(ix), axis=1)
            for th, B in ((1.2, 1000), (1.0, 1000), (1.5, 1000), (1.2, 500), (1.2, 2500)):
                sec = sira[oran[sira] >= th][: int(B // BIRIM[K])]; S = len(sec) * BIRIM[K]
                KAYIT.append(dict(gun=key[0], hip=key[1], K=K, th=th, B=B, S=S if S >= 20 else 0.0, hit=int(S >= 20 and bool(kaz[sec].any())),
                                  tutar=od["tutar"], devir=od["devir"], carry=CARRY.get((key[0], key[1], int(key[2])), 0.0) if K == 5 else 0.0))
    for K in (3, 4, 5): EG[K] += yeni[K]
    print(ay, "tamam", flush=True)
D = pd.DataFrame(KAYIT); pickle.dump((D, OWNMED), open("/tmp/claude-0/t166_kayit.pkl", "wb"))
def getiri(D, k, devir_kazanc=True):
    N = D.hip.map(OWNMED).astype(float) * k + D.carry
    W = np.maximum(1.0, N / np.where(D.tutar > 0, D.tutar, np.nan))
    g = np.where(D.devir, (N + 0.75 * D.S) if devir_kazanc else 0.0, (N + 0.75 * D.S) / (W + 1))
    return np.where(D.hit == 1, np.nan_to_num(g), 0.0)
def roi(x, gcol, q):
    g = x.assign(_g=gcol).groupby("gun").agg(m=("S", "sum"), r=("_g", "sum")); g = g[g.m > 0]; ug = g.index.values; bs = []
    for _ in range(3000):
        s = rng.choice(ug, len(ug)); bs.append(g.r[s].sum() / g.m[s].sum() - 1)
    return g.r.sum() / g.m.sum() - 1, np.percentile(bs, q)
KB = {3: (1.0, (0.5, 2.0)), 4: (0.5, (0.25, 1.0)), 5: (1.0, (0.5, 2.0))}
for K, ad in ((3, "üçlü"), (4, "tabela"), (5, "sıralı 5'li")):
    x = D[(D.K == K) & (D.th == 1.2) & (D.B == 1000)].copy(); o = x[x.S > 0]; k0, ks = KB[K]
    r, (lo, hi) = roi(x, getiri(x, k0), (0.833, 99.167))
    duy = [roi(x, getiri(x, k), (2.5, 97.5))[0] for k in ks]
    print(f"=== {ad}: BİRİNCİL (eşik 1,2, 1.000 TL, havuz k={k0}) koşu {len(o)} ort. {o.S.mean():,.0f} TL isabet {int(o.hit.sum())} (bunların DEVİR olanı {int((o.hit & o.devir).sum())}) → ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}] | duyarlılık k={ks}: {[round(v, 3) for v in duy]} → {'KÂRLI ADAY' if lo > 0 and min(duy) > 0 else 'kârlı değil'}")
    r2, (lo2, hi2) = roi(x, getiri(x, k0, False), (2.5, 97.5)); print(f"      DEVİR isabeti 0 sayılırsa: {r2:+.3f} [{lo2:+.3f}; {hi2:+.3f}]")
    for th, B in ((1.0, 1000), (1.5, 1000), (1.2, 500), (1.2, 2500)):
        x2 = D[(D.K == K) & (D.th == th) & (D.B == B)].copy(); o2 = x2[x2.S > 0]
        if not len(o2): continue
        r3, (lo3, hi3) = roi(x2, getiri(x2, k0), (2.5, 97.5)); print(f"      eşik {th} bütçe {B}: koşu {len(o2)} ort. {o2.S.mean():,.0f} TL isabet {int(o2.hit.sum())} ROI {r3:+.3f} [{lo3:+.3f}; {hi3:+.3f}]")
