"""T209: sıralı beşlide 4.-5. sıra sürpriz kalibrasyonu. Ön kayıt: hipotez_defteri T209. Actions: t209.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json, math
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d, M, O, _fit, skorla, EK, LPEK, np, pd = [_ns[k] for k in ("d", "M", "O", "_fit", "skorla", "EK", "LPEK", "np", "pd")]
from tjk import elo as EL
from tjk import besli as BS
d = EL.ekle(d); d["rid"] = d.groupby(O.K).ngroup()
E = M["feat"] + EK + LPEK + EL.EXTRA_FEAT
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str); RACES = []
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q3"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True)
    th, mu, sd, nk = _fit(tr, E, M.get("lam", 100.0)); te["p_E"] = skorla(te, E, th, mu, sd)
    for _, g in te.groupby(O.K):
        s = pd.to_numeric(g.sira, errors="coerce").values
        if not (g.p_piyasa.values > 0).all(): continue
        if len(g) < 7: continue
        pos = {}
        ok = True
        for r in range(1, 6):
            w = np.where(s == r)[0]
            if len(w) != 1: ok = False; break
            pos[r] = int(w[0])
        if not ok: continue
        p = g.p_E.values / g.p_E.values.sum(); pm = g.p_piyasa.values
        rk = (-pm).argsort().argsort() + 1    # piyasa sırası (1 = favori)
        RACES.append(dict(n=len(g), q=kq, tarih=str(g.tarih.iloc[0]), p=p, rk=rk, fin=[pos[r] for r in range(1, 6)]))
    print(kq, len(RACES), flush=True)
G0 = [1.0, 0.8018, 0.6804, 0.5958, 0.5307]
rng = np.random.default_rng(2081); BB = 10000
test = [R for R in RACES if R["q"] >= "2026Q1"]
KAT = [("7-11", 7, 11), ("12-13", 12, 13), ("14-15", 14, 15), (">=16", 16, 99)]
FW = {"12-13": 56, "14-15": 43, ">=16": 29}
res = {"n_test": len(test)}; OUT = {}
for ad, lo, hi in KAT:
    kos = [R for R in test if lo <= R["n"] <= hi]
    idx = rng.choice(len(kos), size=min(800, len(kos)), replace=False) if kos else []
    OUT[ad] = {"n_havuz": len(kos), "n": len(idx)}
    for B in (48, 96, 150):
        isab = []; bek = []
        for i in idx:
            R = kos[i]; kp = BS.kupon_g(list(R["p"]), B, G0)
            if kp is None: continue
            sets, pr = kp; isab.append(float(all(R["fin"][k] in sets[k] for k in range(5)))); bek.append(float(pr))
        isab = np.array(isab); bek = np.array(bek); m = len(isab)
        bi = rng.integers(0, m, (BB, m)); ratio = isab[bi].sum(1) / np.maximum(bek[bi].sum(1), 1e-9)
        OUT[ad][f"B{B}"] = {"n": m, "isabet": int(isab.sum()), "beklenen": float(bek.sum()), "oran": float(isab.sum() / bek.sum()), "GA95": [float(x) for x in np.percentile(ratio, [2.5, 97.5])], "isab_oran": float(isab.mean()), "bek_oran": float(bek.mean())}
        print(ad, B, json.dumps(OUT[ad][f"B{B}"]), flush=True)
# ileri karışım ağırlıklı
for B in (48, 96, 150):
    w = {a: FW[a] for a in FW}; tw = sum(w.values())
    ib = sum(w[a] / tw * OUT[a][f"B{B}"]["isab_oran"] for a in w); be = sum(w[a] / tw * OUT[a][f"B{B}"]["bek_oran"] for a in w)
    OUT[f"karisim_B{B}"] = {"isab_oran": ib, "bek_oran": be, "oran": ib / be}
    print("karisim", B, OUT[f"karisim_B{B}"], flush=True)
res["T"] = OUT
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t209.json"), "w"), indent=1, ensure_ascii=False)
