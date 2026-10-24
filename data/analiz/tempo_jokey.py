"""Tempo × jokey testi (ön kayıt: hipotez_defteri 2026-10-24 10:45). Veri: data/atyarisi/*.json.gz (sonuc).
tempo τ = kazananın ilk (mesafe-800 m) hızı / son 800 m hızı; log τ, mesafe bandı x pist içinde z-skorlanır (yüksek = erken hızlı/ön yüklü, düşük = sprint bitiş).
Model: koşul içi çok terimli logit, ofset = log(kapanış ganyanı marjsız olasılığı); jokey başına tempo eğimi (ridge). Güvenilirlik: çift/tek günlere bölüp eğimlerin korelasyonu.
Çalıştırma: python3 data/analiz/tempo_jokey.py"""
import glob, gzip, json, os, re, math, collections
import numpy as np
from scipy.optimize import minimize
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def sn(x):
    m = re.fullmatch(r"(?:(\d+)\.)?(\d+)\.(\d\d)", str(x or "").strip())
    return (int(m[1] or 0) * 60 + int(m[2]) + int(m[3]) / 100) if m else None
R = []
for f in sorted(glob.glob(os.path.join(KOK, "data", "atyarisi", "*.json.gz"))):
    d = json.load(gzip.open(f, "rt", encoding="utf-8")); gun = os.path.basename(f)[:10]
    for hip, yar in (d.get("sonuc") or {}).items():
        for r in yar or []:
            try:
                D = int(r["distance"]); L = sn(str(r.get("last800", "")).split("-")[0])
                hs = [h for h in r["horses"] if h.get("order") and h.get("ganyan") and isinstance(h.get("jockey"), dict) and h.get("status", True)]
                w = [h for h in hs if h["order"] == 1]
                if len(w) != 1 or not L or len(hs) < 5: continue
                T = sn(w[0].get("degree"))
                if not T or T <= L + 5: continue
                tau = math.log(((D - 800) / (T - L)) / (800 / L))
                inv = np.array([1 / float(h["ganyan"]) for h in hs]); p = inv / inv.sum()
                R.append(dict(gun=gun, D=D, pist=r.get("raceCourseType"), tau=tau, lp=np.log(p), w=[h["order"] for h in hs].index(1), jok=[h["jockey"]["name"] for h in hs], hip=hip))
            except Exception:
                continue
print("koşu", len(R), "gün", len({r["gun"] for r in R}))
g = collections.defaultdict(list)
for r in R: g[(r["pist"], r["D"] // 400)].append(r["tau"])
for r in R:
    v = g[(r["pist"], r["D"] // 400)]; r["z"] = (r["tau"] - np.mean(v)) / (np.std(v) + 1e-9) if len(v) >= 20 else 0.0
print("tau sd (log):", round(float(np.std([r["tau"] for r in R])), 4), "| z kullanılan koşu:", sum(1 for r in R if r["z"] != 0.0))
def slopes(rows, minb=20, l2=8.0):
    cnt = collections.Counter(j for r in rows for j in r["jok"]); J = sorted(j for j, c in cnt.items() if c >= minb); ix = {j: i for i, j in enumerate(J)}
    def f(th):
        a, b = th[0], th[1:]; L = 0.0; g_ = np.zeros_like(th)
        for r in rows:
            x = np.array([b[ix[j]] * r["z"] if j in ix else 0.0 for j in r["jok"]]); s = a * r["lp"] + x; s -= s.max(); e = np.exp(s); p = e / e.sum()
            L -= np.log(p[r["w"]] + 1e-12); d = p.copy(); d[r["w"]] -= 1
            g_[0] += (d * r["lp"]).sum()
            for k, j in enumerate(r["jok"]):
                if j in ix: g_[1 + ix[j]] += d[k] * r["z"]
        L += l2 * (b @ b); g_[1:] += 2 * l2 * b
        return L, g_
    th = minimize(f, np.r_[1.0, np.zeros(len(J))], jac=True, method="L-BFGS-B").x
    return {j: th[1 + i] for j, i in ix.items()}, cnt
gunler = sorted({r["gun"] for r in R}); A = [r for r in R if gunler.index(r["gun"]) % 2 == 0]; B = [r for r in R if gunler.index(r["gun"]) % 2 == 1]
sa, ca = slopes(A); sb, cb = slopes(B); ortak = [j for j in sa if j in sb]
print("her yarıda ≥20 biniş olan jokey:", len(ortak))
if len(ortak) >= 8:
    x = np.array([sa[j] for j in ortak]); y = np.array([sb[j] for j in ortak]); print("eğim korelasyonu (çift vs tek gün): %.3f" % np.corrcoef(x, y)[0, 1])
    print("eğim yorumu: z yüksek = erken hızlı/ön yüklü koşu (geriden gelene avantaj). Geriden gelen jokey ⇒ POZİTİF eğim beklenir; öncü ⇒ NEGATİF:")
    for j in sorted(ortak, key=lambda j: sa[j] + sb[j])[:6] + sorted(ortak, key=lambda j: sa[j] + sb[j])[-6:]:
        print(f"  {j:22s} A {sa[j]:+.3f} B {sb[j]:+.3f} (biniş {ca[j]}+{cb[j]})")
    for j in ortak:
        if "ABİŞ" in j.upper() or "ABIS" in j.upper(): print("  >>", j, sa[j], sb[j])
