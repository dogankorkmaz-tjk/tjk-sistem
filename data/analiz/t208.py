"""T208: sıralı beşlide 4.-5. sıra sürpriz kalibrasyonu. Ön kayıt: hipotez_defteri T208. Actions: t208.yml. Betik sonuca bakılarak ayarlanmaz."""
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
        RACES.append(dict(q=kq, tarih=str(g.tarih.iloc[0]), p=p, rk=rk, fin=[pos[r] for r in range(1, 6)]))
    print(kq, len(RACES), flush=True)
G0 = [1.0, 0.8018, 0.6804, 0.5958, 0.5307]
def cond(p, g, used):
    w = np.power(np.maximum(p, 1e-9), g); w = w.copy(); w[list(used)] = 0.0; return w / w.sum()
def ll_pos(R, r, g):          # r = 2..5, g = üs
    used = R["fin"][:r - 1]; q = cond(R["p"], g, used); return math.log(max(q[R["fin"][r - 1]], 1e-12))
rng = np.random.default_rng(2080); BB = 10000
def boot(vals, gun):
    vals = np.asarray(vals, float); u, inv = np.unique(gun, return_inverse=True)
    S = np.bincount(inv, weights=vals); C = np.bincount(inv); n = len(u); idx = rng.integers(0, n, (BB, n)); m = S[idx].sum(1) / C[idx].sum(1)
    return float(vals.mean()), [float(x) for x in np.percentile(m, [2.5, 97.5])], [float(x) for x in np.percentile(m, [1.25, 98.75])]
gun = np.array([R["tarih"] for R in RACES]); res = {"n_kosu": len(RACES)}
# A) kalibrasyon
A = {}
for r in range(2, 6):
    sur_f = []; sur_e = []
    top = {k: ([], []) for k in (1, 2, 3)}
    for R in RACES:
        q = cond(R["p"], G0[r - 1], R["fin"][:r - 1]); w = R["fin"][r - 1]
        sur = R["rk"] >= 6
        sur_f.append(float(sur[w])); sur_e.append(float(q[sur].sum()))
        o = np.argsort(-q)
        for k in (1, 2, 3): top[k][0].append(float(w in o[:k])); top[k][1].append(float(q[o[:k]].sum()))
    f = np.array(sur_f) - np.array(sur_e); m, ga95, gab = boot(f, gun)
    A[f"r{r}"] = {"surpriz_gozlenen": float(np.mean(sur_f)), "surpriz_beklenen": float(np.mean(sur_e)), "fark": m, "GA95": ga95, "GA_97_5tek": [float(np.percentile(f, 0))] if False else None}
    A[f"r{r}"]["GA_ana"] = [float(x) for x in boot(f, gun)[1]]
    for k in (1, 2, 3):
        ff = np.array(top[k][0]) - np.array(top[k][1]); mm, g95, _ = boot(ff, gun); A[f"r{r}"][f"top{k}"] = {"gozlenen": float(np.mean(top[k][0])), "beklenen": float(np.mean(top[k][1])), "fark": mm, "GA95": g95}
    print("A", r, json.dumps(A[f"r{r}"], ensure_ascii=False), flush=True)
res["A"] = A
dag = {}
for r in (4, 5):
    rr = np.array([R["rk"][R["fin"][r - 1]] for R in RACES]); dag[f"r{r}"] = {"1-3": float((rr <= 3).mean()), "4-5": float(((rr >= 4) & (rr <= 5)).mean()), "6-8": float(((rr >= 6) & (rr <= 8)).mean()), ">=9": float((rr >= 9).mean())}
res["dagilim_piyasa_sirasi"] = dag
# B) yeniden kalibrasyon (ileri-yürüyüş)
GRID = np.round(np.arange(0.30, 1.0001, 0.01), 2)
Q = sorted(set(R["q"] for R in RACES)); testq = [q for q in Q if q >= "2026Q1"]; dif = []; dgun = []; P1 = {}
for kq in testq:
    egit = [R for R in RACES if R["q"] < kq]; test = [R for R in RACES if R["q"] == kq]
    if len(egit) < 500: continue
    g1 = [1.0]
    for r in range(2, 6):
        sk = [sum(ll_pos(R, r, g) for R in egit) for g in GRID]; g1.append(float(GRID[int(np.argmax(sk))]))
    P1[kq] = g1
    for R in test:
        dif.append(sum(ll_pos(R, r, g1[r - 1]) - ll_pos(R, r, G0[r - 1]) for r in range(2, 6))); dgun.append(R["tarih"])
m, ga95, _ = boot(dif, np.array(dgun)); res["B"] = {"n_test": len(dif), "P1_ustler": P1, "kazanc_P1_P0": m, "GA95": ga95}
print("B", json.dumps(res["B"], ensure_ascii=False), flush=True)
# C) kupon bilgi
test = [R for R in RACES if R["q"] >= "2026Q1"]; idx = rng.choice(len(test), size=min(1000, len(test)), replace=False)
g1s = P1.get(testq[-1], G0)
def kup(R, G):
    kp = BS.kupon_g(list(R["p"]), 48, G)
    if kp is None: return None
    sets, pr = kp; fin = R["fin"]; tam = all(fin[k] in sets[k] for k in range(5)); ort = sum(fin[k] in sets[k] for k in range(5)); return int(tam), ort, pr
C = {}
for ad, G in (("P0", G0), ("P1_son", g1s)):
    out = [kup(test[i], G) for i in idx]; out = [o for o in out if o]
    C[ad] = {"koşu": len(out), "tam_isabet": int(sum(o[0] for o in out)), "ort_tutan_sira": float(np.mean([o[1] for o in out])), "ort_beklenen_tutma": float(np.mean([o[2] for o in out]))}
    print("C", ad, json.dumps(C[ad]), flush=True)
res["C"] = C
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t208.json"), "w"), indent=1, ensure_ascii=False)
