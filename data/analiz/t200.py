"""T200: altılıda AGF + piyasasız model (PM0) karışımı. Ön kayıt: hipotez_defteri T200. Actions: t200.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json, glob
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d, M, O, _fit, skorla, EK, LPEK, np, pd = [_ns[k] for k in ("d", "M", "O", "_fit", "skorla", "EK", "LPEK", "np", "pd")]
from tjk import elo as EL
d = EL.ekle(d)
E = M["feat"] + EK + LPEK + EL.EXTRA_FEAT
feat0 = [c for c in dict.fromkeys(E) if c not in LPEK and c != "f_lp2"]
print("PM0 özellik sayısı", len(feat0), "çıkarılan", [c for c in E if c in LPEK or c == "f_lp2"], flush=True)
tr2a = lambda s: str(s).translate(O.TR).lower()
d["hip"] = d.hipodrom.map(tr2a)
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str); parts = []
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q1"]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()].assign(lp=0.0)
    fk = [c for c in feat0 if tr[c].std(ddof=0) > 0]
    th, mu, sd, nk = _fit(tr, fk, M.get("lam", 100.0))
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup(); te["lp"] = 0.0
    te["p0"] = skorla(te, fk, th, mu, sd); parts.append(te[["tarih", "hip", "kosu", "no", "kazandi", "p0"]]); print(kq, len(te), flush=True)
P = pd.concat(parts, ignore_index=True)
Z = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "zengin", "*.csv.gz")))])[["tarih", "hipodrom", "kosu", "no", "agf_son"]]
Z["hip"] = Z.hipodrom.map(tr2a); P = P.merge(Z[["tarih", "hip", "kosu", "no", "agf_son"]], on=["tarih", "hip", "kosu", "no"], how="left")
K3 = ["tarih", "hip", "kosu"]
ok = P.groupby(K3).agf_son.transform(lambda s: s.notna().all() and s.sum() > 50); P = P[ok].copy()
P["a"] = P.agf_son.clip(lower=0.01); P["a"] = P.a / P.groupby(K3).a.transform("sum"); P["p0"] = P.p0 / P.groupby(K3).p0.transform("sum")
G = {k: g.reset_index(drop=True) for k, g in P.groupby(K3)}
Od = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))])
Od = Od[Od.tur.str.startswith("6'LI GANYAN")].drop_duplicates(["tarih", "hipodrom", "kosu"])
AL = []
for r in Od.itertuples():
    legs = [G.get((r.tarih, tr2a(r.hipodrom), k)) for k in range(r.kosu - 5, r.kosu + 1)]
    if any(g is None for g in legs) or any(g.kazandi.sum() < 1 for g in legs): continue
    AL.append({"t": r.tarih, "h": tr2a(r.hipodrom), "k": r.kosu, "legs": legs, "devir": "DEVİR" in r.tur, "tutar": float(r.tutar)})
print("altılı", len(AL), "2025:", sum(x["t"] < "2026" for x in AL), "2026:", sum(x["t"] >= "2026" for x in AL), flush=True)
def mix(a, p0, w):
    l = (1 - w) * np.log(a) + w * np.log(np.maximum(p0, 1e-9)); e = np.exp(l - l.max()); return e / e.sum()
GR = np.round(np.arange(0, 1.0001, 0.05), 2)
def llw(rows, w): return np.mean([np.log(mix(g.a.values, g.p0.values, w)[g.kazandi.values == 1].sum() / max(g.kazandi.sum(), 1) * 1.0 + 1e-12) for g in rows])
tr25 = [x for x in AL if x["t"] < "2026"]
wc = float(GR[int(np.argmax([llw([g for x in tr25 for g in x["legs"]], w) for w in GR]))])
wl = [float(GR[int(np.argmax([llw([x["legs"][j] for x in tr25], w) for w in GR]))]) for j in range(6)]
print("w (2025 fit) tek:", wc, "ayak başına:", wl, flush=True)
def kur(q, B):
    n = len(q); S = [[int(np.argmax(q[j]))] for j in range(n)]
    while True:
        C = np.prod([len(s) for s in S]); best = None
        for j in range(n):
            m = len(S[j])
            if C * (m + 1) / m > B: continue
            Pj = q[j][S[j]].sum()
            for i in range(len(q[j])):
                if i in S[j]: continue
                sc = np.log((Pj + q[j][i]) / Pj) / np.log((m + 1) / m)
                if best is None or sc > best[0]: best = (sc, j, i)
        if best is None: return S
        S[best[1]].append(best[2])
ARMS = {"A": lambda g, j: g.a.values, "BC": lambda g, j: mix(g.a.values, g.p0.values, wc), "BL": lambda g, j: mix(g.a.values, g.p0.values, wl[j])}
rows = []
for x in AL:
    r = {"t": x["t"], "h": x["h"], "k": x["k"], "gun": x["t"] + x["h"], "yil": "2025" if x["t"] < "2025-12-32" and x["t"] < "2026" else "2026"}
    for ad, f in ARMS.items():
        q = [f(g, j) for j, g in enumerate(x["legs"])]
        for j, g in enumerate(x["legs"]): r[f"ll_{ad}_{j}"] = float(np.log(q[j][g.kazandi.values == 1].sum() / g.kazandi.sum()))
        for B in (64, 256):
            S = kur(q, B); cost = int(np.prod([len(s) for s in S])); hits = [bool(g.kazandi.values[S[j]].any()) for j, g in enumerate(x["legs"])]
            r[f"cost_{ad}_{B}"] = cost; r[f"hit_{ad}_{B}"] = int(sum(hits)); r[f"all_{ad}_{B}"] = int(all(hits)); r[f"pay_{ad}_{B}"] = x["tutar"] if (all(hits) and not x["devir"]) else 0.0
    rows.append(r)
D = pd.DataFrame(rows); D.to_csv(os.path.join(KOK, "data", "analiz", "t200_altili.csv"), index=False)
rng = np.random.default_rng(2000)
def boot(df, f, B=5000, lo=2.5, hi=97.5):
    gs = df.groupby("gun"); idx = {k: v.index.values for k, v in gs}; keys = list(idx); n = len(keys); out = []
    for _ in range(B):
        sel = np.concatenate([idx[keys[i]] for i in rng.integers(0, n, n)]); out.append(f(df.loc[sel]))
    return [float(f(df)), *map(float, np.percentile(out, [lo, hi]))]
res = {}
for yil in ("2025", "2026"):
    X = D[D.yil == yil].reset_index(drop=True)
    for ad in ("BC", "BL"):
        fll = lambda df, ad=ad: float(np.mean([(df[f"ll_{ad}_{j}"] - df[f"ll_A_{j}"]).mean() for j in range(6)]))
        res[f"{yil}_ll_{ad}-A"] = boot(X, fll, lo=1.25, hi=98.75) if yil == "2026" else [fll(X)]
        for j in range(6): res[f"{yil}_ll_{ad}-A_ayak{j+1}"] = float((X[f"ll_{ad}_{j}"] - X[f"ll_A_{j}"]).mean())
        for B in (64, 256):
            res[f"{yil}_tutan_{ad}-A_B{B}"] = boot(X, lambda df, ad=ad, B=B: float((df[f"hit_{ad}_{B}"] - df[f"hit_A_{B}"]).mean()), B=3000, lo=1.25, hi=98.75) if yil == "2026" else [float((X[f"hit_{ad}_{B}"] - X[f"hit_A_{B}"]).mean())]
    for ad in ARMS:
        for B in (64, 256):
            res[f"{yil}_betim_{ad}_B{B}"] = {"altili": len(X), "tutan_ayak": float(X[f"hit_{ad}_{B}"].mean()), "6/6": int(X[f"all_{ad}_{B}"].sum()), "ROI": float(X[f"pay_{ad}_{B}"].sum() / X[f"cost_{ad}_{B}"].sum()), "maliyet": float(X[f"cost_{ad}_{B}"].mean())}
for k, v in res.items(): print(k, json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else np.round(v, 4).tolist())
def karar(ad):
    a = res[f"2026_ll_{ad}-A"]; ok1 = a[1] > 0; ok2 = all(res[f"2026_tutan_{ad}-A_B{B}"][0] > 0 for B in (64, 256)); return "ADAY" if (ok1 and ok2) else "yok"
print("KARAR BL:", karar("BL"), "| BC:", karar("BC"), "| w tek", wc, "w_j", wl)
res["karar"] = {"BL": karar("BL"), "BC": karar("BC")}; res["w"] = {"tek": wc, "ayak": wl}
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t200.json"), "w"), indent=1, ensure_ascii=False)
