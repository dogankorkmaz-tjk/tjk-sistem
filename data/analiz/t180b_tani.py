"""T180 tanı: tahmin edicinin makullüğü (ön kayıtlı sonucu değiştirmez)."""
import io, contextlib, importlib.util, numpy as np
spec = importlib.util.spec_from_file_location("t179", "data/analiz/t179_altili_kural.py"); t = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(t)
for k in ("F192", "D192", "K65"):
    sz = []; X = []; Xc = []
    for s in t.S:
        sec = t.KUR[k](s["ay"]); sz.append([len(x) for x in sec])
        r = []
        for j in range(6):
            w = s["kaz"][j][0]; pa = s["ay"][j][w][1]; r.append((w in sec[j]) / max(pa, 1e-6))
        X.append(r); Xc.append(np.minimum(r, 15))
    sz = np.array(sz); X = np.array(X); Xc = np.array(Xc)
    print(k, "ort.|S_j|", np.round(sz.mean(0), 2), "\n   m_j", np.round(X.mean(0), 2), "\n   m_j (üst sınır 15)", np.round(Xc.mean(0), 2),
          "\n   en büyük tek X / ayak", np.round(X.max(0), 1), "\n   adil piyasa beklentisi: m_j ≈ |S_j|; ROI ≈ 0,69")
