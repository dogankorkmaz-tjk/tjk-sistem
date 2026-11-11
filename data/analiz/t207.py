"""T207: kısa dizili ganyanlarda AGF-favori kuponu taban getirisi. Ön kayıt: hipotez_defteri T207. Betimleyici."""
import os, sys, json, glob, itertools
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
import numpy as np, pandas as pd
from tjk import ortak as O
tr2a = lambda s: str(s).translate(O.TR).lower()
Z = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "zengin", "*.csv.gz")))])[["tarih", "hipodrom", "kosu", "no", "agf_son"]]
Z["hip"] = Z.hipodrom.map(tr2a); Z["tarih"] = Z.tarih.astype(str)
RACE = {}
for (t, h, k), g in Z.groupby(["tarih", "hip", "kosu"]):
    if g.agf_son.notna().all() and g.agf_son.sum() > 50:
        a = g.agf_son.clip(lower=0.01).values; RACE[(t, h, int(k))] = (g.no.astype(int).values, a / a.sum())
Od = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))])
TURLER = {"ÇİFTE": 2, "3'LÜ GANYAN": 3, "4'LÜ GANYAN": 4, "5'Lİ GANYAN": 5, "6'LI GANYAN": 6}
Od = Od[Od.tur.isin(TURLER)].drop_duplicates(["tarih", "hipodrom", "kosu", "tur", "seq"]).copy(); Od["tarih"] = Od.tarih.astype(str); Od["hip"] = Od.hipodrom.map(tr2a)
def kazananlar(kombo, n):
    p = str(kombo).split("/")
    if len(p) != n: return None
    try: return [set(int(x) for x in s.split(",")) for s in p]
    except Exception: return None
def ayaklar(r, n, mod):
    ks = range(r.kosu - n + 1, r.kosu + 1) if mod == "son" else range(r.kosu, r.kosu + n)
    L = [RACE.get((r.tarih, r.hip, k)) for k in ks]
    return None if any(l is None for l in L) else L
# hizalama doğrulaması
secim = {}
for tur, n in TURLER.items():
    S = Od[Od.tur == tur]; oran = {}
    for mod in ("son", "ilk"):
        ok = tot = 0
        for r in S.head(800).itertuples():
            W = kazananlar(r.kombo, n); L = ayaklar(r, n, mod)
            if W is None or L is None: continue
            tot += 1; ok += all(w <= set(l[0].tolist()) for w, l in zip(W, L))
        oran[mod] = ok / max(tot, 1)
    secim[tur] = max(oran, key=oran.get); print("hizalama", tur, oran, "->", secim[tur], flush=True)
NC = 5
def kupon(L, B):
    cand = [np.argsort(-l[1])[:NC] for l in L]; idx = np.array(list(itertools.product(*[range(len(c)) for c in cand])))
    la = np.zeros(len(idx))
    for j, c in enumerate(cand): la += np.log(L[j][1][c[idx[:, j]]])
    o = np.argsort(-la)[:B]; return [[int(L[j][0][cand[j][i]]) for j, i in enumerate(idx[k])] for k in o]
rows = []
for r in Od.itertuples():
    n = TURLER[r.tur]; W = kazananlar(r.kombo, n); L = ayaklar(r, n, secim[r.tur])
    if W is None or L is None: continue
    for B in (16, 64):
        cl = kupon(L, B); win = sum(all(c[j] in W[j] for j in range(n)) for c in cl)
        hit = sum(any(c[j] in W[j] for c in cl) for j in range(n))
        rows.append(dict(tur=r.tur, n=n, B=B, gun=r.tarih, cost=len(cl), pay=float(r.tutar) * win, hit=hit, tam=int(win > 0), yil=r.tarih[:4]))
D = pd.DataFrame(rows); print("kupon satırı", len(D), flush=True)
rng = np.random.default_rng(2070); BB = 3000
def ozet(df):
    g = df.groupby("gun").agg(c=("cost", "sum"), p=("pay", "sum")).values; m = len(g); idx = rng.integers(0, m, (BB, m)); T = g[idx].sum(1)
    return {"dizi": int(len(df)), "tutan_ayak": float(df.hit.mean()), "tam": int(df.tam.sum()), "ROI": float(g[:, 1].sum() / g[:, 0].sum()), "GA95": [float(x) for x in np.percentile(T[:, 1] / T[:, 0], [2.5, 97.5])], "maliyet": float(df.cost.mean())}
res = {}
for tur in TURLER:
    for B in (16, 64):
        for nm, df in (("tum", D), ("2025", D[D.yil == "2025"]), ("2026", D[D.yil == "2026"])):
            s = df[(df.tur == tur) & (df.B == B)]
            if len(s) >= 50: res[f"{tur}|B{B}|{nm}"] = ozet(s); print(tur, B, nm, json.dumps(res[f"{tur}|B{B}|{nm}"], ensure_ascii=False), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t207.json"), "w"), indent=1, ensure_ascii=False)
