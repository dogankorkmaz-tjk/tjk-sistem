"""T163 (ön kayıt: hipotez_defteri 2026-11-07 00:1x): ikili / sıralı ikili muhtemellerine karşı Benter (MJ) değer bahisleri."""
import json, glob, pickle, numpy as np, pandas as pd
rng = np.random.default_rng(163)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
HMAP = {"DBAKIR": "diyarbakir"}
MUH = {}
for f in glob.glob("data/muh_gecmis/20*.json"):
    t = f[-15:-5]
    for k, v in json.load(open(f)).items():
        h, kn = k.rsplit("-", 1); MUH[(t, HMAP.get(h, h.lower()), int(kn))] = v
R = []
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        m = MUH.get((key[0], key[1], int(key[2])))
        if not m: continue
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; g = c["g3"]
        p1 = np.exp(s - s.max()); p1 /= p1.sum(); w2 = np.power(p1, g[1]); kaz = nos[0], nos[1]   # nos bitiriş sırasında
        def sp(a, b):
            if a not in nos or b not in nos or a == b: return None
            ia, ib = nos.index(a), nos.index(b); return p1[ia] * w2[ib] / (w2.sum() - w2[ia])
        for tur, L in (("si", m.get("si") or []), ("ik", m.get("ik") or [])):
            for x in L:
                try: a, b, o = int(x[0]), int(x[1]), float(str(x[2]).replace(",", "."))
                except Exception: continue
                if tur == "si":
                    p = sp(a, b); hit = (a, b) == kaz
                else:
                    pa, pb = sp(a, b), sp(b, a); p = None if pa is None else pa + pb; hit = {a, b} == set(kaz)
                if p is None or o <= 1: continue
                R.append(dict(gun=key[0], key=(key[0], key[1], int(key[2])), tur=tur, p=p, o=o, ev=p * o, hit=hit, getiri=o * hit))
D = pd.DataFrame(R); print("koşu", D.key.nunique(), "gün", D.gun.nunique(), "| listelenen kombinasyon", len(D))
for tur in ("si", "ik"):
    x = D[D.tur == tur]; kaz_listede = x.groupby("key").hit.any().mean()
    print(f"{tur}: kazanan kombinasyon listede: %{100 * kaz_listede:.0f} koşu | hepsine 1 birim ROI {x.getiri.sum() / len(x) - 1:+.3f}")
def roi(x, q):
    g = x.groupby("gun").agg(m=("getiri", "size"), r=("getiri", "sum")); ug = g.index.values; bs = []
    for _ in range(4000):
        s = rng.choice(ug, len(ug)); bs.append(g.r[s].sum() / g.m[s].sum() - 1)
    return x.getiri.sum() / len(x) - 1, np.percentile(bs, q)
for tur, ad in (("si", "sıralı ikili"), ("ik", "ikili")):
    print(f"--- {ad} ---")
    for th in (1.0, 1.2, 1.5, 2.0):
        x = D[(D.tur == tur) & (D.ev >= th)]
        if not len(x): continue
        r, (lo, hi) = roi(x, (1.25, 98.75) if th == 1.2 else (2.5, 97.5))
        ens = (x.getiri.sum() - x.getiri.max()) / len(x) - 1
        print(f"   p×o ≥ {th}: bahis {len(x)} koşu {x.key.nunique()} isabet {int(x.hit.sum())} ROI {r:+.3f} [{lo:+.3f}; {hi:+.3f}] ({'%97,5 BİRİNCİL' if th == 1.2 else '%95'}) | en büyük çıkarılınca {ens:+.3f}")
    x = D[(D.tur == tur) & (D.ev >= 1.2)]; r, (lo, hi) = roi(x, (1.25, 98.75)); print(f"   KARAR ({ad}):", "kârlı ADAY" if lo > 0 else "kârlı değil")
