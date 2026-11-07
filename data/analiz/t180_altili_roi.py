"""T180: altılı kuralları için ayak bazlı ROI tahmini (ön kayıt hipotez_defteri)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "data/analiz")
import importlib.util, io, contextlib
spec = importlib.util.spec_from_file_location("t179", "data/analiz/t179_altili_kural.py")
t = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(t)
S, KUR = t.S, t.KUR; rng = np.random.default_rng(180)
print("tam altılı:", len(S), "gün:", len({s['gun'] for s in S}))
X = {k: [] for k in KUR}; N = {k: [] for k in KUR}; G = []
for s in S:
    G.append(s["gun"])
    for k, fn in KUR.items():
        sec = fn(s["ay"]); n = t.ozet(s["ay"], sec)["kombinasyon"]; xs = []
        for j in range(6):
            w = s["kaz"][j][0]; pa = s["ay"][j][w][1]
            xs.append((1.0 if w in sec[j] else 0.0) / max(pa, 1e-6))
        X[k].append(xs); N[k].append(1.0 / n)
G = np.array(G); X = {k: np.array(v) for k, v in X.items()}; N = {k: np.array(v) for k, v in N.items()}
def roi(k, idx): return 0.69 * np.prod(X[k][idx].mean(0)) * N[k][idx].mean()
gs = np.unique(G); gi = {g: np.where(G == g)[0] for g in gs}
B = []
for _ in range(3000):
    idx = np.concatenate([gi[g] for g in rng.choice(gs, len(gs))]); B.append({k: roi(k, idx) for k in KUR})
al = np.arange(len(S))
print(f"{'kural':5} {'ROI_tahmin':>11} {'%95 aralık':>20} {'ort.komb':>9}")
for k in KUR:
    v = [b[k] for b in B]; lo, hi = np.percentile(v, [2.5, 97.5])
    print(f"{k:5} {roi(k, al):11.2f} [{lo:8.2f};{hi:9.2f}] {1/N[k].mean():9.1f}")
print("=== Fark (kural − F192) ve maliyet")
for k in KUR:
    if k == "F192": continue
    d = [b[k] - b["F192"] for b in B]; lo, hi = np.percentile(d, [2.5, 97.5])
    print(f"  {k:5}: {roi(k, al) - roi('F192', al):+7.2f} [{lo:+7.2f};{hi:+8.2f}] | maliyet ×{(1/N[k].mean())/(1/N['F192'].mean()):.2f}")
print("=== Ödeme modeli doğrulaması: gerçek altılı ödemesi / (0,69/Π p_AGF(kazanan))")
o = []
for s in S:
    if s["odeme"] == s["odeme"]:
        pr = 0.69 / np.prod([s["ay"][j][s["kaz"][j][0]][1] for j in range(6)]); o.append(s["odeme"] / pr)
print(f"  n {len(o)}  medyan oran {np.median(o):.2f}  geometrik ort {np.exp(np.mean(np.log(o))):.2f}  [%10 {np.percentile(o,10):.2f}; %90 {np.percentile(o,90):.2f}]")
print("=== Ayak başına ortalama değer m_j (F192 | D192 | K65)")
for k in ("F192", "D192", "K65"): print(" ", k, np.round(X[k].mean(0), 2))
