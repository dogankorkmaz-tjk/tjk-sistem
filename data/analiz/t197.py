"""T197: 'ilk3 sürpriz' etiketi (i3b/i3p>=1,15) etiketli atların kazanma/ilk-3 oranı. Ön kayıt: hipotez_defteri T197."""
import json, glob, os, itertools
import numpy as np
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G_PIY = [1, .87, .74]
def piyasa(g):
    ham = [1 / x for x in g]; top = sum(ham); grp = [-1] * len(g)
    if top > 1.5:
        for o in sorted(set(g)):
            idx = [i for i, x in enumerate(g) if x == o]; n = len(idx); r = 0
            while n - r > 1 and top > 1.5: top -= 1 / o; r += 1
            if r:
                for i in idx: ham[i] = (n - r) / n / o
            if top <= 1.5: break
    s = sum(ham); return np.array([x / s for x in ham])
def modelp(pp, z, w0, lp2):
    l = np.log(np.maximum(pp, 1e-6)); s = w0 * l + lp2 * l * l + z; e = np.exp(s - s.max()); return e / e.sum()
def harville(p, G):
    n = len(p); top = np.zeros((n, 2)); W = [p ** G[r] for r in range(3)]
    def rec(sira, kalan, prob):
        if sira == 3: return
        t = sum(W[sira][j] for j in kalan)
        for i in kalan:
            q = prob * W[sira][i] / t
            for r in range(sira, 3):
                if r == 0: top[i, 0] += q
                if r == 2: top[i, 1] += q
            rec(sira + 1, [j for j in kalan if j != i], q)
    rec(0, list(range(n)), 1.0); return top[:, 1]
R = []
for f in sorted(glob.glob(os.path.join(KOK, "docs", "data", "gun", "*.json"))):
    d = json.load(open(f)); gun = d["tarih"]
    if d.get("w0_g1") is None: continue
    for h in d["hipodromlar"]:
        for k in h["kosular"]:
            s = k.get("sonuc")
            if not s: continue
            at = [a for a in k["atlar"] if str(a["no"]) in s and (s[str(a["no"])].get("g") or 0) > 0]
            if len(at) < 5 or any(a.get("z6") is None for a in at) or len(at) > 16: continue
            g = [s[str(a["no"])]["g"] for a in at]; pp = piyasa(g)
            pg = modelp(pp, np.array([a["z6"] for a in at]), d["w0_g1"], d.get("lp2_g1") or 0.0)
            G = d.get("a_g1") or [1, .8, .69]
            i3b = harville(pg, G[:3]); i3p = harville(pp, G_PIY)
            for j, a in enumerate(at):
                sr = s[str(a["no"])].get("sira")
                R.append((gun, h["id"], k["kosu"], a["no"], pp[j], pg[j], i3p[j], i3b[j], 1.0 if sr == 1 else 0.0, 1.0 if (sr is not None and sr <= 3) else 0.0))
import pandas as pd
D = pd.DataFrame(R, columns=["gun", "hip", "kosu", "no", "pp", "pg", "i3p", "i3b", "kaz", "ilk3"]); D["f3"] = D.i3b / D.i3p; D["etiket"] = D.f3 >= 1.15
print("gün", D.gun.nunique(), "koşu", D.groupby(["gun", "hip", "kosu"]).ngroups, "at", len(D), "etiketli", int(D.etiket.sum()))
rng = np.random.default_rng(1970)
def ga(x, B=20000):
    g = x.groupby(D.loc[x.index, "gun"]).agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values; n = len(s); idx = rng.integers(0, n, (B, n)); m = s[idx].sum(1) / c[idx].sum(1)
    return float(s.sum() / c.sum()), np.percentile(m, [2.5, 97.5])
out = {}
for ad, sec in (("etiketli", D.etiket), ("etiketsiz", ~D.etiket)):
    S = D[sec]; r = {"n": len(S), "kazanma": float(S.kaz.mean()), "ort_pp": float(S.pp.mean()), "ort_pg": float(S.pg.mean()), "ilk3": float(S.ilk3.mean()), "ort_i3p": float(S.i3p.mean()), "ort_i3b": float(S.i3b.mean())}
    for nm, a, b in (("kaz−pp", S.kaz, S.pp), ("kaz−pg", S.kaz, S.pg), ("ilk3−i3p", S.ilk3, S.i3p), ("ilk3−i3b", S.ilk3, S.i3b)):
        m, c = ga(a - b); r[nm] = [m, float(c[0]), float(c[1])]
    out[ad] = r; print(ad, json.dumps({k: (np.round(v, 4).tolist() if isinstance(v, list) else round(v, 4)) for k, v in r.items()}), flush=True)
K = D.groupby(["gun", "hip", "kosu"]); sayi = K.etiket.sum(); kz = K.apply(lambda g: float((g.etiket & (g.kaz == 1)).any())); bekl = K.apply(lambda g: float(1 - np.prod(1 - g.pg[g.etiket])))
print(f"koşu: {len(sayi)}; ≥1 etiketli at olan: {int((sayi>0).sum())} ({(sayi>0).mean():.1%}); ortalama etiketli/koşu {sayi.mean():.2f}")
print(f"≥1 etiketli at olan koşularda etiketlilerden biri kazandı: {kz[sayi>0].mean():.1%} (modelin beklentisi {bekl[sayi>0].mean():.1%}; piyasa beklentisi {K.apply(lambda g: float(1-np.prod(1-g.pp[g.etiket])))[sayi>0].mean():.1%})")
e = out["etiketli"]["kaz−pp"]
print("KARAR:", "GERÇEK (etiket piyasadan iyi seçiyor)" if e[1] > 0 else ("AYIRT EDİLEMEZ" if e[0] > 0 else "YOK"))
json.dump(out, open(os.path.join(KOK, "data", "analiz", "t197.json"), "w"), indent=1)
