"""T211: gün içi kapı yanlılığı. Ön kayıt: hipotez_defteri T211."""
import os, sys, json
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "h", "exec"), _ns)
d, np, pd = _ns["d"], _ns["np"], _ns["pd"]
d = d[~d.kosmadi.fillna(False).astype(bool)].copy()
dol = d.st.notna().mean(); print("st doluluk", dol, flush=True)
if dol < 0.9: json.dump({"durdu": "st doluluk %.3f" % dol}, open(os.path.join(KOK, "data", "analiz", "t211.json"), "w")); sys.exit()
d = d[d.st.notna() & (d.p_piyasa > 0)].copy(); d["st"] = pd.to_numeric(d.st, errors="coerce"); d = d[d.st.notna()]
d["n"] = d.groupby(["tarih", "hipodrom", "kosu"]).st.transform("count"); d = d[d.n >= 5]
d["g"] = (d.st - 1) / (d.n - 1).clip(lower=1); d["eg"] = d.p_piyasa * d.g
R = d.groupby(["tarih", "hipodrom", "kosu"]).agg(eg=("eg", "sum"), gw=("g", lambda s: np.nan), n=("n", "first")).reset_index()
W = d[d.kazandi.astype(float) == 1].groupby(["tarih", "hipodrom", "kosu"]).g.first().rename("gw")
R = R.drop(columns="gw").merge(W, on=["tarih", "hipodrom", "kosu"], how="left"); R["dev"] = R.gw - R.eg
R = R.sort_values(["tarih", "hipodrom", "kosu"]); B = {}
for (t, h), g in R.groupby(["tarih", "hipodrom"]):
    for i, (k, dv) in enumerate(zip(g.kosu, g.dev)):
        prev = g.dev.iloc[:i].dropna()
        if len(prev) >= 3: B[(t, h, k)] = float(prev.mean())
d["B"] = [B.get((t, h, k), np.nan) for t, h, k in zip(d.tarih, d.hipodrom, d.kosu)]; d = d[d.B.notna()].copy()
d["x"] = d.B * (d.g - 0.5); d["off"] = np.log(d.p_piyasa); d["win"] = d.kazandi.astype(float)
d["rid2"] = d.groupby(["tarih", "hipodrom", "kosu"]).ngroup(); d = d.sort_values("rid2")
d = d[d.groupby("rid2").win.transform("sum") == 1]
rng = np.random.default_rng(2110)
def fit(df, w_r=None):
    ridx = df.rid2.values; u, ri = np.unique(ridx, return_inverse=True); nr = len(u)
    x = df.x.values; off = df.off.values; win = df.win.values; w = np.ones(nr) if w_r is None else w_r[ri_map(df)]
    b = 0.0
    for _ in range(8):
        e = np.exp(off + b * x); S = np.bincount(ri, e, nr); m1 = np.bincount(ri, e * x, nr) / S; m2 = np.bincount(ri, e * x * x, nr) / S
        xw = np.bincount(ri, win * x, nr); sc = (w * (xw - m1)).sum(); he = (w * (m2 - m1 ** 2)).sum()
        b += sc / max(he, 1e-12)
    ll0 = None
    return b
def ri_map(df): return None
def prep(df):
    u, ri = np.unique(df.rid2.values, return_inverse=True); return dict(ri=ri, nr=len(u), x=df.x.values, off=df.off.values, win=df.win.values,
        gun=pd.Series(df.tarih.values).groupby(ri).first().values)
def beta(P, w=None):
    ri, nr, x, off, win = P["ri"], P["nr"], P["x"], P["off"], P["win"]; w = np.ones(nr) if w is None else w; b = 0.0
    xw = np.bincount(ri, win * x, nr)
    for _ in range(8):
        e = np.exp(off + b * x); S = np.bincount(ri, e, nr); m1 = np.bincount(ri, e * x, nr) / S; m2 = np.bincount(ri, e * x * x, nr) / S
        b += (w * (xw - m1)).sum() / max((w * (m2 - m1 ** 2)).sum(), 1e-12)
    return b
def nll_gain(P, b):
    ri, nr, x, off, win = P["ri"], P["nr"], P["x"], P["off"], P["win"]
    def ll(bb): e = np.exp(off + bb * x); S = np.bincount(ri, e, nr); return (np.bincount(ri, win * (off + bb * x), nr) - np.log(S)).sum()
    return (ll(b) - ll(0.0)) / nr
def run(df, ad):
    P = prep(df); b = beta(P); u, inv = np.unique(P["gun"], return_inverse=True); nd = len(u); out = []
    for _ in range(2000):
        cnt = np.bincount(rng.integers(0, nd, nd), minlength=nd); out.append(beta(P, cnt[inv].astype(float)))
    r = {"n_kosu": P["nr"], "beta": float(b), "GA95": [float(v) for v in np.percentile(out, [2.5, 97.5])], "nll_kazanc_kosu": float(nll_gain(P, b))}
    print(ad, json.dumps(r), flush=True); return r
yil = pd.to_datetime(d.tarih).dt.year.values; res = {}
res["tum"] = run(d, "tum"); res["2023-24"] = run(d[yil <= 2024], "2023-24"); res["2025-26"] = run(d[yil >= 2025], "2025-26")
res["kosu>=6"] = run(d[d.kosu >= 6], "kosu>=6")
agir = d.pist.astype(str).str.lower().str.contains("ağır|agir|çamur|camur|yumuşak|yumusak")
res["agir_pist"] = run(d[agir], "agir_pist"); res["normal_pist"] = run(d[~agir], "normal_pist")
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t211.json"), "w"), indent=1, ensure_ascii=False)
