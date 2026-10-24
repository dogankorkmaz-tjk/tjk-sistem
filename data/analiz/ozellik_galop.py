"""Galop (idman) özellik grubu testi. Ön kayıt: hipotez_defteri 2026-10-24 11:20. Çalıştırma: python3 data/analiz/ozellik_galop.py"""
import glob, os, sys, random, datetime as dt, collections
import numpy as np, pandas as pd
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import g1
KOK = g1.KOK
def nrm(s): return str(s or "").upper().translate(str.maketrans("İıŞşĞğÜüÖöÇç", "IISSGGUUOOCC")).replace("İ", "I").strip()
G = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(KOK, "data", "galop", "*.csv.gz"))])
G["atn"] = G["at"].map(nrm); G["itd"] = pd.to_datetime(G.it)
G["p400"] = pd.to_numeric(G.p400, errors="coerce")
G["rel"] = (G.p400 - G.groupby(["it", "tur"]).p400.transform("median")).clip(-4, 4)
G["yog"] = G.durum.isin(["Çalışarak", "Hafif Çalışarak"]).astype(float)
G["spr"] = (G.tur == "Sprint").astype(float)
gr = {a: x.sort_values("itd") for a, x in G.groupby("atn")}
print("galop at:", len(gr), "satır:", len(G), G.it.min(), G.it.max())
rows = list(g1._satirlar()); K = {}
for r in rows: K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
H, J, AJ = {}, {}, {}; R = []; esles = [0, 0]
for key in sorted(K):
    ok = [r for r in K[key] if r["kosmadi"] != "True" and g1._fl(r["ganyan"], 0) > 1 and g1._fl(r["sira"], 0) > 0]
    n = len(ok)
    if n < 4: continue
    inv = np.array([1 / g1._fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
    w = [i for i, r in enumerate(ok) if r["sira"] == "1"]
    if len(w) != 1: continue
    if key[0] >= "2026-02-01":
        X = g1._oz(H, J, AJ, ok, pm, gun); F = np.zeros((n, 6)); t = pd.Timestamp(key[0])
        for i, r in enumerate(ok):
            x = gr.get(nrm(r["at"])); f = [0.0, 30.0, 0.0, 0.0, 0.0, 0.0]; yok = 1.0
            if x is not None:
                y = x[(x.itd < t) & (x.itd >= t - pd.Timedelta(days=30))]
                if len(y):
                    yok = 0.0; f = [float(len(y)), float((t - y.itd.max()).days), float(y.spr.sum()), float(y.rel.iloc[-1]) if y.rel.notna().iloc[-1] else 0.0, float(y.rel.min()) if y.rel.notna().any() else 0.0, float(y.yog.mean())]
            F[i] = f; esles[0] += 1 - yok; esles[1] += 1
        F = np.c_[F, [0.0] * n]; F[:, 6] = [1.0 if (F[i, 0] == 0) else 0.0 for i in range(n)]
        R.append(dict(gun=key[0], ay=key[0][:7], lm=np.log(pm), X=X, F=F, w=w[0]))
    for i, r in enumerate(ok):
        pct = 1 - (g1._fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == w[0] else 0.0
        H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
        j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
        a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
print("2026-02+ koşu:", len(R), "| son-30-gün galopu olan at oranı: %.3f" % (esles[0] / esles[1]))
cf = __import__("json").load(open(g1.YOL)); b1 = np.array(cf["b"]); al = cf["alfa"]
M = max(len(r["lm"]) for r in R)
def pack(rl):
    N = len(rl); S0 = np.full((N, M), -1e9); FF = np.zeros((N, M, 7)); W = np.zeros(N, int)
    for k, r in enumerate(rl):
        n = len(r["lm"]); S0[k, :n] = al * r["lm"] + r["X"] @ b1; FF[k, :n] = r["F"]; W[k] = r["w"]
    return S0, FF, W
def fit(rl, l2=20.0):
    S0, FF, W = pack(rl); mu = FF[S0 > -1e8].mean(0); sd = FF[S0 > -1e8].std(0) + 1e-9; Z = (FF - mu) / sd; idx = np.arange(len(W))
    def f(b):
        s = S0 + Z @ b; s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True)
        d = p.copy(); d[idx, W] -= 1
        return -np.log(p[idx, W] + 1e-12).sum() + l2 * (b @ b), np.einsum("nm,nmk->k", d, Z) + 2 * l2 * b
    return minimize(f, np.zeros(7), jac=True, method="L-BFGS-B").x, mu, sd
def loss(rl, b, mu, sd):
    S0, FF, W = pack(rl); Z = (FF - mu) / sd; s = S0 + Z @ b; s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True)
    return -np.log(p[np.arange(len(W)), W] + 1e-12)
aylar = sorted({r["ay"] for r in R}); L0, L1, gun = [], [], []
for a in aylar:
    if a < "2026-04": continue
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if len(tr) < 300 or not te: continue
    b, mu, sd = fit(tr); L1 += list(loss(te, b, mu, sd)); L0 += list(loss(te, np.zeros(7), mu, sd)); gun += [r["gun"] for r in te]
    if a == aylar[-1] or a == "2026-10": print("son ay katsayılar", dict(zip(["say30", "gun", "sprint", "rel_son", "rel_en", "yog", "yok"], np.round(b, 3))))
L0, L1, gun = np.array(L0), np.array(L1), np.array(gun); d = L1 - L0; ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}; random.seed(2)
bs = [d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(2000)]
print(f"test {len(d)} koşu, {len(ug)} gün; G1 log-kayıp {L0.mean():.4f}; G1+galop {L1.mean():.4f}; fark {d.mean():+.4f} GA [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")
