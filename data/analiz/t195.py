"""T195: at başına Plackett-Luce 'görünmeyen güç' (zamanla sönümlü, aylık yeniden fit, sızıntısız) Jason+Elo üstüne bilgi katıyor mu?
Ön kayıt: hipotez_defteri T195. Actions: t195.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json, time
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
import numpy as np, pandas as pd
from scipy.optimize import minimize
from tjk import elo as EL
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d, M, O = _ns["d"], _ns["M"], _ns["O"]
_fit, skorla, EK, LPEK = _ns["_fit"], _ns["skorla"], _ns["EK"], _ns["LPEK"]
d = EL.ekle(d); d["rid"] = d.groupby(O.K).ngroup()           # Elo özellikleri (G1-S v3 ile aynı), sıra korunur
LAM, YARI, ASAMA = 1.0, 365.0, 4                              # ön kayıt: önsel kesinliği 1,0; yarı ömür 365 gün; ilk 4 sıra
hid = pd.factorize(d["at"].astype(str))[0]; H = int(hid.max()) + 1
sira = pd.to_numeric(d.sira, errors="coerce").fillna(0).values; rk = np.where(sira > 0, sira, 99).astype(int)
lp = d.lp.values.astype(float); rid = d.rid.values; gun = pd.to_datetime(d.tarih).values.astype("datetime64[D]").astype(int)
tarih = d.tarih.astype(str).values

def fit_pl(idx, off, T0, th0):
    r_ = rid[idx]; o = np.argsort(r_, kind="stable"); idx = idx[o]; r_ = r_[o]
    st = np.r_[0, np.nonzero(np.diff(r_))[0] + 1]; n = len(idx); seg = np.repeat(np.arange(len(st)), np.diff(np.r_[st, n]))
    h = hid[idx]; rkk = rk[idx]; of = (lp[idx] if off else np.zeros(n))
    w = 0.5 ** ((T0 - np.maximum.reduceat(gun[idx], st)) / YARI)       # yarış ağırlığı
    stages = []
    for k in range(1, ASAMA + 1):
        win = (rkk == k); nw = np.add.reduceat(win.astype(int), st); ok = (nw == 1)
        stages.append((rkk >= k, win & ok[seg], ok))
    def f(th):
        s = th[h] + of; ll = 0.0; g = np.zeros(n)
        for mem, wsel, ok in stages:
            sk = np.where(mem, s, -np.inf); mx = np.maximum.reduceat(sk, st); mx = np.where(np.isfinite(mx), mx, 0.0)
            e = np.exp(sk - mx[seg]); Z = np.add.reduceat(e, st); Zs = np.where(Z > 0, Z, 1.0)
            va = ok & (Z > 0)
            ll += (w[va] * (np.add.reduceat(np.where(wsel, s, 0.0), st)[va] - (np.log(Zs) + mx)[va])).sum()
            g += (w * va)[seg] * (wsel - e / Zs[seg])
        grad = -np.bincount(h, weights=g, minlength=H) + LAM * th
        return -ll + 0.5 * LAM * (th @ th), grad
    r = minimize(f, th0.copy(), jac=True, method="L-BFGS-B", options={"maxiter": 120})
    return r.x

aylar = sorted(d.tarih.str[:7].unique()); aylar = [a for a in aylar if a >= "2023-07"]
f_pl = np.zeros(len(d)); f_plm = np.zeros(len(d)); th_a = np.zeros(H); th_b = np.zeros(H); t0 = time.time()
for a in aylar:
    bas = a + "-01"; tr = np.nonzero(tarih < bas)[0]; te = np.nonzero(d.tarih.astype(str).str.startswith(a).values)[0]
    if len(tr) < 5000 or len(te) == 0: continue
    T0 = int(np.datetime64(bas, "D").astype(int))
    th_a = fit_pl(tr, False, T0, th_a); th_b = fit_pl(tr, True, T0, th_b)
    f_pl[te] = th_a[hid[te]]; f_plm[te] = th_b[hid[te]]
    print(a, "fit", round(time.time() - t0), "sn", flush=True)
d["f_pl"] = f_pl - pd.Series(f_pl).groupby(d.rid.values).transform("mean").values
d["f_plm"] = f_plm - pd.Series(f_plm).groupby(d.rid.values).transform("mean").values
print("std f_pl", float(d.f_pl.std()), "f_plm", float(d.f_plm.std()), "korelasyon f_pl~f_elo", float(d.f_pl.corr(d.f_elo)), "f_plm~f_elo", float(d.f_plm.corr(d.f_elo)), flush=True)
if os.environ.get("T195_DEBUG"): sys.exit(0)

base = M["feat"] + EK + LPEK; E = base + EL.EXTRA_FEAT
kollar = {"J": base, "E": E, "EP": E + ["f_pl"], "EM": E + ["f_plm"], "P": base + ["f_pl"]}
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str); rows = []
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q3"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup()
    for ad, feat in kollar.items():
        th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0)); te["p_" + ad] = skorla(te, feat, th, mu, sd)
    w = te[te.kazandi == 1]; o = {"tarih": w.tarih.values}
    for ad in kollar: o[ad] = (np.log(w["p_" + ad]) - np.log(w.p_piyasa)).values
    rows.append(pd.DataFrame(o)); print(kq, len(w), {a: round(float(rows[-1][a].mean()), 5) for a in kollar}, flush=True)
R = pd.concat(rows, ignore_index=True); R["yari"] = np.where(R.tarih <= "2025-12-31", "2025H2", "2026")
rng = np.random.default_rng(1950)
def ga(v, tarih, lo, hi, B=20000):
    g = pd.Series(np.asarray(v)).groupby(np.asarray(tarih)).agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values
    n = len(s); idx = rng.integers(0, n, (B, n)); m = s[idx].sum(1) / c[idx].sum(1)
    return [float(s.sum() / c.sum()), float(np.percentile(m, lo)), float(np.percentile(m, hi))]
res = {}
for ad, ref, bonf in (("EP", "E", True), ("EM", "E", True), ("P", "J", False), ("E", "J", False)):
    dd = R[ad] - R[ref]; lo, hi = (1.25, 98.75) if bonf else (2.5, 97.5)
    res[f"{ad}-{ref}"] = {"tum": ga(dd, R.tarih, lo, hi), "2025H2": ga(dd[R.yari == "2025H2"], R.tarih[R.yari == "2025H2"], lo, hi)[0], "2026": ga(dd[R.yari == "2026"], R.tarih[R.yari == "2026"], lo, hi)[0]}
    print(ad, "-", ref, {k: ([round(x, 5) for x in v] if isinstance(v, list) else round(v, 5)) for k, v in res[f"{ad}-{ref}"].items()}, flush=True)
def ok(k): r = res[k]; return r["tum"][1] > 0 and r["2025H2"] > 0 and r["2026"] > 0
print("KARAR: PL gücü (saf)", "ADAY" if ok("EP-E") else "YOK", "| PL gücü (piyasa ofsetli)", "ADAY" if ok("EM-E") else "YOK", "(bilgi: P−J ve E−J)")
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t195.json"), "w"), indent=1)
