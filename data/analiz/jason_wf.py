"""Jason ileri-yürüyüş yeniden üretimi: her ay için o aydan önceki verilerle eğit, ay içi z2 ve Jason olasılığı pj üret. Çıktı: /tmp/claude-0/jason_wf.pkl"""
import sys, numpy as np, pandas as pd, time
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
feat = M["feat"] + GL.EK + GL.LPEK; out = []
for ay in ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[(d.tarih <= son) & d.kazandi.notna() & d.lp.notna()].copy()
    th, mu, sd, nk = GL._fit(tr, feat, M.get("lam", 100.0))
    A = {"feat": feat, "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th]}
    lp2a = float(th[1 + feat.index("f_lp2")] / sd["f_lp2"])
    te = d[d.tarih.str[:7] == ay].copy()
    if te.empty: continue
    te["z2"] = GL.z2(te, A)
    s = th[0] * te.lp.values + lp2a * te.lp.values ** 2 + te.z2.values
    te["s"] = s; m = te.groupby(["tarih", "hipodrom", "kosu"]).s.transform("max"); e = np.exp(te.s - m); te["pj"] = e / e.groupby([te.tarih, te.hipodrom, te.kosu]).transform("sum")
    out.append(te[["tarih", "hipodrom", "kosu", "no", "z2", "pj", "p_piyasa", "ganyan", "kazandi"]]); print(ay, nk, round(time.time() - t0), "sn", flush=True)
pd.concat(out).to_pickle("/tmp/claude-0/jason_wf.pkl"); print("bitti")
