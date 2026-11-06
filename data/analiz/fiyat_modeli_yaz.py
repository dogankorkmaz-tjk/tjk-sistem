"""Canlı değer kuponu için fiyat modeli katsayıları (T166 ile aynı yürüyen regresyon, tüm geçmiş): log(ödeme) ~ log(1/p_piyasa) + log(p_model/p_piyasa)."""
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
import json
EG = {3: [], 4: [], 5: []}
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; lm = c["L0"][i][:n]; g = list(c["g3"])
        p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        for K in (3, 4, 5):
            od = ODM.get((key[0], key[1], int(key[2]), K))
            if od is None or n < K + 2 or not all(x in nos for x in od["seq"]) or od["devir"] or od["tutar"] <= 0: continue
            Pw = np.array([tuple(nos.index(x) for x in od["seq"])]); pmw = pl(Pw, pm, BS.G_P, K)[0]; pmo = pl(Pw, p, g, K)[0]
            EG[K].append((math.log(1 / pmw), math.log(pmo / pmw), math.log(od["tutar"])))
O = {}
for K in (3, 4, 5):
    X = np.array(EG[K]); A = np.c_[np.ones(len(X)), X[:, 0], X[:, 1]]; beta, *_ = np.linalg.lstsq(A, X[:, 2], rcond=None)
    O[str(K)] = dict(b=[round(float(x), 5) for x in beta], s2=round(float((X[:, 2] - A @ beta).var()), 5), n=len(X), birim=BIRIM[K])
O["kayma"] = 0.96; O["kaynak"] = "data/analiz/fiyat_modeli_yaz.py (T166 yöntemi; 2025-10..2026-10); kayma: T168"
json.dump(O, open("docs/data/fiyat_modeli.json", "w"), ensure_ascii=False, indent=1); print(O)
