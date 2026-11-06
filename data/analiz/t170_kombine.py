"""T170: kombine kupon (n at) vs T167 virgüllü — temel: T167 (ön kayıt hipotez_defteri 2026-11-07 00:56): T166 değer seçimi → bayide oynanabilir virgüllü kupon; liste ile eşleştirilmiş karşılaştırma."""
import glob, pickle, itertools, math, sys, numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import besli as BS
rng = np.random.default_rng(170)
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
def kupon(P, oran, th, B, birim, K, haric=None):
    """Açgözlü virgüllü kupon. Döner: (dahil maskesi, maliyet) ya da None."""
    ok = np.ones(len(P), bool) if haric is None else ~haric
    adayl = np.where(ok)[0]
    if not len(adayl): return None
    b = adayl[np.argmax(oran[adayl])]
    if oran[b] < th: return None
    S = [{int(P[b, k])} for k in range(K)]
    M = [P[:, k] == P[b, k] for k in range(K)]
    while True:
        cur = np.logical_and.reduce(M) & ok; best = None
        for k in range(K):
            for h in set(np.unique(P[:, k])) - S[k]:
                Mk = M[k] | (P[:, k] == h); m = cur | (np.logical_and.reduce([Mk if j == k else M[j] for j in range(K)]) & ok)
                yeni = m & ~cur; c = m.sum() * birim
                if c > B or not yeni.any(): continue
                d = (oran[yeni] - th).sum()
                if d > 0 and (best is None or d > best[0]): best = (d, k, h, Mk)
        if best is None: break
        _, k, h, Mk = best; S[k].add(h); M[k] = Mk
    m = np.logical_and.reduce(M) & ok
    return m, m.sum() * birim
def kombine(P, oran, th, B, birim, K):
    b = int(np.argmax(oran))
    if oran[b] < th: return None
    n = int(P.max()) + 1; mem = np.zeros(n, bool); mem[P[b]] = True; cur = mem[P].all(1)
    while True:
        sec = None
        for h in np.unique(P):
            if mem[h]: continue
            m2 = mem.copy(); m2[h] = True; nw = m2[P].all(1); yeni = nw & ~cur
            if nw.sum() * birim > B or not yeni.any(): continue
            d = (oran[yeni] - th).sum()
            if d > 0 and (sec is None or d > sec[0]): sec = (d, h, nw)
        if sec is None: break
        mem[sec[1]] = True; cur = sec[2]
    return cur, cur.sum() * birim, int(mem.sum())
KAYIT = []; EG = {3: [], 4: [], 5: []}
VAR = ((1.2, 1000), (1.0, 1000), (1.2, 500))
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
            beta, s2 = MOD[K]; t = sorted(range(n), key=lambda j: -p[j])[:9]; bi = BIRIM[K]
            P = np.array(list(itertools.permutations(t, K))); pmod = pl(P, p, g, K); pmk = pl(P, pm, BS.G_P, K)
            oh = np.exp(beta[0] + beta[1] * np.log(1 / np.maximum(pmk, 1e-15)) + beta[2] * np.log(np.maximum(pmod, 1e-15) / np.maximum(pmk, 1e-15)) + s2 / 2)
            oran = pmod * oh / bi; sira = np.argsort(-oran); kaz = np.all(P == np.array(ix), axis=1)
            ort = dict(gun=key[0], hip=key[1], kosu=int(key[2]), K=K, tutar=od["tutar"], devir=od["devir"], carry=CARRY.get((key[0], key[1], int(key[2])), 0.0) if K == 5 else 0.0)
            for th, B in VAR:
                for tip in ("virgul", "kombine"):
                    if tip == "virgul":
                        r = kupon(P, oran, th, B, bi, K); nat = 0
                        if r is not None: m, cst = r
                    else:
                        r = kombine(P, oran, th, B, bi, K)
                        if r is not None: m, cst, nat = r
                    if r is None: KAYIT.append(dict(ort, th=th, B=B, tip=tip, S=0.0, u=0.0, dolgu=0.0, nkomb=0, nat=0)); continue
                    ms = math.ceil(20 / cst) if cst < 20 else 1
                    KAYIT.append(dict(ort, th=th, B=B, tip=tip, S=cst * ms, u=float(ms) if kaz[m].any() else 0.0, dolgu=(oran[m] < th).sum() * bi * ms, nkomb=int(m.sum()), nat=nat))
    for K in (3, 4, 5): EG[K] += yeni[K]
    print(ay, "tamam", flush=True)
D = pd.DataFrame(KAYIT); pickle.dump((D, OWNMED), open("/tmp/claude-0/t170_kayit.pkl", "wb"))
KB = {3: 1.0, 4: 0.5, 5: 1.0}
def getiri(D, k):
    N = D.hip.map(OWNMED).astype(float) * k + D.carry
    W = np.maximum(1.0, N / np.where(D.tutar > 0, D.tutar, np.nan))
    g = np.where(D.devir, N + 0.75 * D.S, D.u * (N + 0.75 * D.S) / (W + D.u))
    return np.where(D.u > 0, np.nan_to_num(g), 0.0)
def topla(x, K):
    x = x.assign(_g=getiri(x, KB[K])); return x.groupby("gun").agg(m=("S", "sum"), r=("_g", "sum"))
def rapor(K, ad, th, B, q):
    a = D[(D.K == K) & (D.th == th) & (D.B == B)]
    L = topla(a[a.tip == "virgul"], K); C = topla(a[a.tip == "kombine"], K)
    J = L.join(C, lsuffix="L", rsuffix="C", how="outer").fillna(0); J = J[(J.mL > 0) | (J.mC > 0)]; ug = J.index.values
    f = lambda j: (j.rL.sum() / max(j.mL.sum(), 1e-9) - 1, j.rC.sum() / max(j.mC.sum(), 1e-9) - 1)
    rl, rc = f(J); bs = []
    for _ in range(3000):
        j = J.loc[rng.choice(ug, len(ug))]; x, y = f(j); bs.append((x, y, y - x))
    lo, hi = np.percentile(np.array(bs), q, axis=0)
    o = a[(a.tip == "kombine") & (a.S > 0)]; ov = a[(a.tip == "virgul") & (a.S > 0)]
    print(f"{ad} eşik {th} bütçe {B}: VİRGÜLLÜ {rl:+.3f} [{lo[0]:+.3f}; {hi[0]:+.3f}] ({len(ov)} koşu, ort {ov.S.mean():,.0f} TL, {int((ov.u>0).sum())} isabet) | KOMBİNE {rc:+.3f} [{lo[1]:+.3f}; {hi[1]:+.3f}] ({len(o)} koşu, ort {o.S.mean():,.0f} TL, ort {o.nkomb.mean():.0f} komb, {int((o.u>0).sum())} isabet, dolgu %{100*o.dolgu.sum()/max(o.S.sum(),1):.0f}) | FARK {rc-rl:+.3f} [{lo[2]:+.3f}; {hi[2]:+.3f}]", flush=True)
    print("     kombine at sayısı dağılımı %:", (o.nat.value_counts(normalize=True).sort_index() * 100).round(1).to_dict())
for K, ad in ((3, "üçlü"), (4, "tabela"), (5, "sıralı 5'li")):
    print("===", ad); rapor(K, ad, 1.2, 1000, (0.833, 99.167))
    for th, B in VAR[1:]: rapor(K, ad, th, B, (2.5, 97.5))
