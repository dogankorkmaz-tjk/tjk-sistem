"""Kapı ve konum arayışı testi (ön kayıt: hipotez_defteri 2026-10-24 11:05). Veri: data/atyarisi sonuc (start=kapı)."""
import glob, gzip, json, os, collections
import numpy as np
from scipy.optimize import minimize
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = []
for f in sorted(glob.glob(os.path.join(KOK, "data", "atyarisi", "*.json.gz"))):
    d = json.load(gzip.open(f, "rt", encoding="utf-8")); gun = os.path.basename(f)[:10]
    for hip, yar in (d.get("sonuc") or {}).items():
        for r in yar or []:
            try:
                D = int(r["distance"]); hs = [h for h in r["horses"] if h.get("order") and h.get("ganyan") and h.get("start") and isinstance(h.get("jockey"), dict)]
                if len(hs) < 6 or sum(1 for h in hs if h["order"] == 1) != 1: continue
                n = max(h["start"] for h in hs)
                inv = np.array([1 / float(h["ganyan"]) for h in hs]); p = inv / inv.sum()
                dis = np.array([(h["start"] - 1) / max(n - 1, 1) for h in hs])            # 0 = iç, 1 = en dış kapı
                R.append(dict(gun=gun, D=D, band=0 if D < 1400 else 1 if D < 1800 else 2, lp=np.log(p), out=dis, w=[h["order"] for h in hs].index(1), jok=[h["jockey"]["name"] for h in hs]))
            except Exception:
                continue
print("koşu", len(R), "gün", len({r["gun"] for r in R}))
def fit(rows, per_band, l2=1.0):
    def f(t):
        a = t[0]; b = t[1:4] if per_band else np.repeat(t[1], 3); L = 0.0; g = np.zeros_like(t)
        for r in rows:
            bb = b[r["band"]]; s = a * r["lp"] + bb * r["out"]; s -= s.max(); e = np.exp(s); p = e / e.sum()
            L -= np.log(p[r["w"]] + 1e-12); d = p.copy(); d[r["w"]] -= 1; g[0] += (d * r["lp"]).sum()
            gb = (d * r["out"]).sum()
            if per_band: g[1 + r["band"]] += gb
            else: g[1] += gb
        return L, g
    t = minimize(f, np.r_[1.0, np.zeros(3 if per_band else 1)], jac=True, method="L-BFGS-B").x
    return t
t = fit(R, True); print("alfa %.3f; dış kapı katsayısı (iç→en dış, logit): kısa(<1400) %+.3f | orta %+.3f | uzun(≥1800) %+.3f" % (t[0], t[1], t[2], t[3]))
# standart hata (kaba): bootstrap gün
import random; random.seed(1); gl = sorted({r["gun"] for r in R}); by = collections.defaultdict(list)
for r in R: by[r["gun"]].append(r)
bs = []
for _ in range(60):
    rows = [x for g in [random.choice(gl) for _ in gl] for x in by[g]]; bs.append(fit(rows, True)[1:4])
bs = np.array(bs); print("bootstrap %95 aralığı:", [(round(float(np.percentile(bs[:, i], 2.5)), 3), round(float(np.percentile(bs[:, i], 97.5)), 3)) for i in range(3)])
# jokey x dış kapı eğimi
def slopes(rows, minb=20, l2=8.0):
    cnt = collections.Counter(j for r in rows for j in r["jok"]); J = sorted(j for j, c in cnt.items() if c >= minb); ix = {j: i for i, j in enumerate(J)}
    def f(th):
        a, b = th[0], th[1:]; L = 0.0; g = np.zeros_like(th)
        for r in rows:
            x = np.array([b[ix[j]] * o if j in ix else 0.0 for j, o in zip(r["jok"], r["out"])]); s = a * r["lp"] + t[1 + r["band"]] * r["out"] + x; s -= s.max(); e = np.exp(s); p = e / e.sum()
            L -= np.log(p[r["w"]] + 1e-12); d = p.copy(); d[r["w"]] -= 1; g[0] += (d * r["lp"]).sum()
            for k, (j, o) in enumerate(zip(r["jok"], r["out"])):
                if j in ix: g[1 + ix[j]] += d[k] * o
        L += l2 * (b @ b); g[1:] += 2 * l2 * b
        return L, g
    th = minimize(f, np.r_[1.0, np.zeros(len(J))], jac=True, method="L-BFGS-B").x
    return {j: th[1 + i] for j, i in ix.items()}, cnt
gun = sorted({r["gun"] for r in R}); A = [r for r in R if gun.index(r["gun"]) % 2 == 0]; B = [r for r in R if gun.index(r["gun"]) % 2 == 1]
sa, ca = slopes(A); sb, cb = slopes(B); ort = [j for j in sa if j in sb]
x = np.array([sa[j] for j in ort]); y = np.array([sb[j] for j in ort])
print("jokey sayısı (her yarıda ≥20 biniş):", len(ort), "| eğim korelasyonu (çift vs tek gün): %.3f" % np.corrcoef(x, y)[0, 1])
for j in sorted(ort, key=lambda j: sa[j] + sb[j])[::-1][:5] + sorted(ort, key=lambda j: sa[j] + sb[j])[:5]:
    print(f"  {j:22s} A {sa[j]:+.2f} B {sb[j]:+.2f} (biniş {ca[j]}+{cb[j]})")
