"""T187 adım C: G1-S'in işaretlediği 'piyasa yanılıyor' atları (p>=0.06 ve p/pm>=1.3) düz 1 TL ganyan ROI. Ön kayıt: hipotez_defteri T187. Ay-ay ileri-yürüyüş (2025-03→), T185 ile aynı iskelet."""
import os, sys, random, math
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
def skor(r, t, bg=None):
    s = t[0] * r["lm"] + r["X"] @ t[1:10]
    if bg is not None and r["F"] is not None: s = s + ((r["F"] - bg[1]) / bg[2]) @ bg[0]
    return s
def sm(s): e = np.exp(s - s.max()); return e / e.sum()
def oran(key):
    ok = [r for r in K[key] if r["kosmadi"] != "True" and g1._fl(r["ganyan"], 0) > 1 and g1._fl(r["sira"], 0) > 0]
    ok.sort(key=lambda r: g1._fl(r["sira"])); return [g1._fl(r["ganyan"]) for r in ok]
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2025-03"]; B = []
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te: continue
    t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1) if a >= "2026-04" else None
    for r in te:
        p = sm(skor(r, t1, bg)); pm = np.exp(r["lm"]); od = oran(r["key"])
        for i in range(len(p)): B.append((r["gun"], a, float(p[i]), float(pm[i]), od[i], 1.0 if i == 0 else 0.0))
    print(a, len(te), flush=True)
print("at-koşu", len(B))
random.seed(11); gun = sorted({b[0] for b in B}); G = {g: [] for g in gun}
for b in B: G[b[0]].append(b)
def rap(ad, f):
    S = [b for b in B if f(b)]
    if not S: print(ad, "yok"); return
    gg = {g: [b for b in G[g] if f(b)] for g in gun}; gd = [g for g in gun if gg[g]]
    def roi(Gs): n = sum(len(gg[g]) for g in Gs); return sum(b[5] * b[4] for g in Gs for b in gg[g]) / n - 1
    bs = [roi([random.choice(gd) for _ in gd]) for _ in range(1500)]
    mp = np.mean([b[2] * b[4] for b in S]) - 1; pmb = np.mean([b[3] * b[4] for b in S]) - 1
    print(f"{ad}: n={len(S)} kazanan {int(sum(b[5] for b in S))} (model beklenen {sum(b[2] for b in S):.1f}, piyasa beklenen {sum(b[3] for b in S):.1f}) ROI {roi(gd):+.1%} [{np.percentile(bs,2.5):+.1%};{np.percentile(bs,97.5):+.1%}]  model-beklenen ROI {mp:+.1%}", flush=True)
print("\n=== ADIM C ===")
for q in (1.3, 1.2, 1.5):
    rap(f"p>=0.06 & p/pm>={q}" + (" (ANA)" if q == 1.3 else " (duyarlılık)"), lambda b, q=q: b[2] >= 0.06 and b[2] / b[3] >= q)
rap("referans: pm>=0.06 tüm atlar", lambda b: b[3] >= 0.06)
for ay in sorted({b[1] for b in B}):
    pass
rap("ANA, yalnız 2026 (G1-S v3 dönemi öncesi dahil)", lambda b: b[1] >= "2026-01" and b[2] >= 0.06 and b[2] / b[3] >= 1.3)
