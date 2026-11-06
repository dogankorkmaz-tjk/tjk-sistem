"""T158 (ön kayıt: hipotez_defteri 2026-11-06 21:05): AGF zamanlamasının Benter kazanan tahminine etkisi (E: ≥45 dk önce, S: son ≤25 dk, K: kapanış ganyanı)."""
import glob, json, numpy as np, pandas as pd
rng = np.random.default_rng(158); R = []
def dk(s): h, m = s.split(":")[:2]; return int(h) * 60 + int(m)
for f in sorted(glob.glob("data/agf_zaman/2026-*.csv.gz")):
    gun = f[-17:-7]
    if gun > "2026-11-05": continue
    A = pd.read_csv(f)
    try: G = json.load(open(f"docs/data/gun/{gun}.json", encoding="utf-8"))
    except Exception: continue
    if G.get("w0_g1") is None: continue
    for h in G["hipodromlar"]:
        for k in h["kosular"]:
            so = k.get("sonuc") or {}; at = [a for a in k["atlar"] if not a.get("kosmaz") and str(a["no"]) in so]
            if len(at) < 4 or not k.get("saat"): continue
            x = A[(A.hipodrom == h["id"]) & (A.kosu == k["kosu"])]
            if x.empty: continue
            post = dk(k["saat"]); x = x.assign(t=x.saat.map(dk))
            e = x[x.t <= post - 45]; s = x[x.t < post]                       # agf_zaman yalnız DEĞİŞEN atları yazar → her at için kesimden önceki son değer
            if e.empty or s.empty or s.t.max() < post - 25: continue          # S: son anlık görüntü koşudan ≤25 dk önce olmalı
            def vek(df):
                df = df.sort_values("t").groupby("no").agf.last(); return np.array([df.get(a["no"], np.nan) for a in at], float)
            pe, ps = vek(e), vek(s)
            try:
                z = np.array([a["z6"] for a in at], float); g = np.array([so[str(a["no"])]["g"] for a in at], float)
                sira = np.array([so[str(a["no"])].get("sira") or 99 for a in at])
            except (KeyError, TypeError): continue
            if np.isnan(pe).any() or np.isnan(ps).any() or (pe <= 0).any() or (ps <= 0).any() or (g <= 1).any() or np.isnan(z).any() or not (sira == 1).any(): continue
            w = int(np.argmax(sira == 1)); pk = 1 / g
            def L(p, mod):
                p = p / p.sum(); s_ = G["w0_g1"] * np.log(p) + (z if mod else 0); s_ = s_ - s_.max(); return -(s_[w] - np.log(np.exp(s_).sum()))
            R.append(dict(gun=gun, BE=L(pe, 1), BS=L(ps, 1), BK=L(pk, 1), ME=L(pe, 0), MS=L(ps, 0), MK=L(pk, 0), fark=post - e.t.max()))
D = pd.DataFrame(R); print("koşu", len(D), "gün", D.gun.nunique(), "| E ile koşu arası medyan dk", D.fark.median(), "(düzeltme 21:10: değişen-at biçimi ileri doldurma)")
def ga(a, b):
    d = D[a] - D[b]; S = d.groupby(D.gun).sum(); N = D.groupby("gun").size(); ug = S.index.values; bs = []
    for _ in range(4000):
        s = rng.choice(ug, len(ug)); bs.append(S[s].sum() / N[s].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return f"{d.mean():+.4f} [{lo:+.4f}; {hi:+.4f}]"
print("ortalama kayıp: Benter E/S/K", D.BE.mean().round(4), D.BS.mean().round(4), D.BK.mean().round(4), "| piyasa E/S/K", D.ME.mean().round(4), D.MS.mean().round(4), D.MK.mean().round(4))
for a, b, ad in (("BS", "BE", "Benter: son AGF − erken AGF"), ("BK", "BS", "Benter: kapanış − son AGF"), ("MS", "ME", "Piyasa: son − erken"), ("MK", "MS", "Piyasa: kapanış − son AGF"),
                 ("BE", "ME", "erken: Benter − piyasa"), ("BS", "MS", "son: Benter − piyasa"), ("BK", "MK", "kapanış: Benter − piyasa")):
    print(f"   {ad:28s} {ga(a, b)}")
