"""T171-A (ön kayıt hipotez_defteri 2026-11-07 02:0x): sürpriz kuponu — Benter sürprizi vs piyasa sürprizi (aynı yapı)."""
import glob, pickle, itertools, math, sys, numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import besli as BS
rng = np.random.default_rng(171)
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
YAPI = {3: [(2, 0), (3, 1), (3, 2)], 4: [(2, 0), (3, 0), (4, 1), (4, 2)], 5: [(2, 0), (3, 0), (4, 1), (4, 2), (4, 3)]}   # (M sayısı, S sayısı) her sıra
KAYIT = []
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; lm = c["L0"][i][:n]
        p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        Mo = list(np.argsort(-p)); mr = np.argsort(np.argsort(-pm)) + 1
        for K in (3, 4, 5):
            od = ODM.get((key[0], key[1], int(key[2]), K))
            if od is None or n < K + 3 or not all(x in nos for x in od["seq"]): continue
            ix = tuple(nos.index(x) for x in od["seq"])
            havuz = [j for j in range(n) if mr[j] > K and j not in Mo[:4]]
            if len(havuz) < 3: continue
            secim = {"A_benter": sorted(havuz, key=lambda j: -p[j]), "B_piyasa": sorted(havuz, key=lambda j: -pm[j]), "C_oran": sorted(havuz, key=lambda j: -(p[j] / pm[j]))}
            for tip, S in secim.items():
                sets = [set(Mo[:m]) | set(S[:k]) for m, k in YAPI[K]]
                kom = [t for t in itertools.product(*sets) if len(set(t)) == K]
                cost = len(kom) * BIRIM[K]
                if cost <= 0: continue
                ms = math.ceil(20 / cost) if cost < 20 else 1
                KAYIT.append(dict(gun=key[0], hip=key[1], K=K, tip=tip, S=cost * ms, u=float(ms) if ix in set(kom) else 0.0, nkomb=len(kom),
                                  tutar=od["tutar"], devir=od["devir"], carry=CARRY.get((key[0], key[1], int(key[2])), 0.0) if K == 5 else 0.0))
    print(ay, "tamam", flush=True)
D = pd.DataFrame(KAYIT); pickle.dump((D, OWNMED), open("/tmp/claude-0/t171a.pkl", "wb"))
KB = {3: 1.0, 4: 0.5, 5: 1.0}
def getiri(D, k):
    N = D.hip.map(OWNMED).astype(float) * k + D.carry
    W = np.maximum(1.0, N / np.where(D.tutar > 0, D.tutar, np.nan))
    g = np.where(D.devir, N + 0.75 * D.S, D.u * (N + 0.75 * D.S) / (W + D.u))
    return np.where(D.u > 0, np.nan_to_num(g), 0.0)
def topla(x, K): x = x.assign(_g=getiri(x, KB[K])); return x.groupby("gun").agg(m=("S", "sum"), r=("_g", "sum"))
def esle(a, b, K, q):
    J = topla(a, K).join(topla(b, K), lsuffix="A", rsuffix="B", how="outer").fillna(0); ug = J.index.values
    f = lambda j: (j.rA.sum() / max(j.mA.sum(), 1e-9) - 1, j.rB.sum() / max(j.mB.sum(), 1e-9) - 1)
    ra, rb = f(J); bs = []
    for _ in range(3000):
        j = J.loc[rng.choice(ug, len(ug))]; x, y = f(j); bs.append((x, y, x - y))
    lo, hi = np.percentile(np.array(bs), q, axis=0); return (ra, lo[0], hi[0]), (rb, lo[1], hi[1]), (ra - rb, lo[2], hi[2])
oz = lambda x: f"{len(x)} koşu, ort {x.S.mean():.0f} TL / {x.nkomb.mean():.0f} komb, {int((x.u > 0).sum())} isabet"
for K, ad in ((3, "üçlü"), (4, "tabela"), (5, "sıralı 5'li")):
    a = D[(D.K == K) & (D.tip == "A_benter")]; b = D[(D.K == K) & (D.tip == "B_piyasa")]; cc = D[(D.K == K) & (D.tip == "C_oran")]
    A_, B_, F_ = esle(a, b, K, (0.833, 99.167)); C_, _, FC = esle(cc, b, K, (2.5, 97.5))
    print(f"=== {ad} BİRİNCİL (%98,33): A Benter sürprizi {A_[0]:+.3f} [{A_[1]:+.3f}; {A_[2]:+.3f}] ({oz(a)}) | B piyasa sürprizi {B_[0]:+.3f} [{B_[1]:+.3f}; {B_[2]:+.3f}] ({oz(b)}) | A−B {F_[0]:+.3f} [{F_[1]:+.3f}; {F_[2]:+.3f}]")
    print(f"    C Benter/piyasa oranıyla sürpriz: {C_[0]:+.3f} [{C_[1]:+.3f}; {C_[2]:+.3f}] ({oz(cc)}) | C−B {FC[0]:+.3f} [{FC[1]:+.3f}; {FC[2]:+.3f}]")
