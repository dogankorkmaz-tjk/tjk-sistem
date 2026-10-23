"""Özellik grubu 1 walk-forward testi. Çalıştırma: python3 data/analiz/ozellik_g1.py"""
import glob, gzip, csv, math, os, random, datetime as dt
import numpy as np
from scipy.optimize import minimize
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rows = []
for f in sorted(glob.glob(os.path.join(KOK, "data", "sonuclar", "*.csv.gz"))):
    rows += list(csv.DictReader(gzip.open(f, "rt", encoding="utf-8")))
K = {}
for r in rows:
    K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
def fl(x, d=None):
    try: return float(x)
    except: return d
FN = ["f3", "f10", "ovr", "dinlen", "kilo", "hnd", "jok", "athj", "ilk"]
H = {}      # at -> list (tarih ordinal, pct, win-p)
J = {}      # jokey -> [n, sum(win-p)]
AJ = {}
races = []
for key in sorted(K):
    rs = K[key]; gun = dt.date.fromisoformat(key[0]).toordinal()
    ok = [r for r in rs if r["kosmadi"] != "True" and fl(r["ganyan"], 0) > 1 and fl(r["sira"], 0) > 0]
    n = len(ok)
    if n < 4: continue
    inv = np.array([1 / fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum()
    kil = np.array([fl(r["kilo"], np.nan) for r in ok]); hnd = np.array([fl(r["hnd"], np.nan) for r in ok])
    kil = np.nan_to_num(kil - np.nanmean(kil)) if not np.all(np.isnan(kil)) else np.zeros(n)
    hnd = np.nan_to_num(hnd - np.nanmean(hnd)) if not np.all(np.isnan(hnd)) else np.zeros(n)
    X = np.zeros((n, len(FN)))
    for i, r in enumerate(ok):
        h = H.get(r["at"], []); j = J.get(r["jokey"], [0, 0.0]); aj = AJ.get((r["at"], r["jokey"]), [0, 0.0])
        def m(lst, k, idx, prior, w):
            l = lst[-k:]; return (sum(x[idx] for x in l) + prior * w) / (len(l) + w)
        X[i, 0] = m(h, 3, 1, 0.5, 2) - 0.5
        X[i, 1] = m(h, 10, 1, 0.5, 3) - 0.5
        X[i, 2] = sum(x[2] for x in h[-10:]) / (len(h[-10:]) + 3)
        X[i, 3] = math.log(1 + min(120, gun - h[-1][0])) / 4 if h else 0.0
        X[i, 4] = kil[i] / 3; X[i, 5] = hnd[i] / 10
        X[i, 6] = j[1] / (j[0] + 30)
        X[i, 7] = aj[1] / (aj[0] + 5)
        X[i, 8] = 1.0 if not h else 0.0
    w = [i for i, r in enumerate(ok) if r["sira"] == "1"]
    if len(w) != 1: continue
    races.append(dict(gun=key[0], ay=key[0][:7], lm=np.log(pm), X=X, w=w[0]))
    for i, r in enumerate(ok):          # güncelle (yarış sonrası)
        pct = 1 - (fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == w[0] else 0.0
        H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
        j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
        aj = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); aj[0] += 1; aj[1] += win - pm[i]
print("koşu", len(races))
M = max(len(r["lm"]) for r in races)
def pack(rl, cols):
    N = len(rl); LM = np.full((N, M), -1e9); XX = np.zeros((N, M, len(cols))); W = np.zeros(N, int)
    for k, r in enumerate(rl):
        n = len(r["lm"]); LM[k, :n] = r["lm"]; XX[k, :n] = r["X"][:, cols]; W[k] = r["w"]
    return LM, XX, W
def nll(th, LM, XX, W, l2, ret_g=True):
    a, b = th[0], th[1:]
    s = a * LM + XX @ b if XX.shape[2] else a * LM
    s = s - s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True)
    N = len(W); idx = np.arange(N)
    L = -np.log(p[idx, W] + 1e-12).sum() + l2 * (b @ b)
    if not ret_g: return L
    d = p.copy(); d[idx, W] -= 1
    g = np.concatenate([[(d * LM.clip(-50, 0)).sum()], np.einsum("nm,nmk->k", d, XX) + 2 * l2 * b]) if XX.shape[2] else np.array([(d * LM.clip(-50, 0)).sum()])
    return L, g
def fit(rl, cols, l2=30.0):
    LM, XX, W = pack(rl, cols); th0 = np.zeros(1 + len(cols)); th0[0] = 1
    return minimize(nll, th0, args=(LM, XX, W, l2), jac=True, method="L-BFGS-B").x
def loss(th, rl, cols):
    LM, XX, W = pack(rl, cols); return np.array([nll(th, LM[i:i+1], XX[i:i+1], W[i:i+1], 0, False) for i in range(len(rl))])
SETS = {"piyasa+alfa": [], "form": [0, 1, 2, 3, 8], "form+kilo/hnd": [0, 1, 2, 3, 4, 5, 8], "jokey": [6, 7], "hepsi": list(range(9))}
aylar = sorted({r["ay"] for r in races}); test_aylar = [a for a in aylar if a >= "2025-01"]
res = {k: [] for k in SETS}; pure = []; gunler = []
for a in test_aylar:
    tr = [r for r in races if r["ay"] < a]; te = [r for r in races if r["ay"] == a]
    pure += [-r["lm"][r["w"]] for r in te]; gunler += [r["gun"] for r in te]
    for k, cols in SETS.items():
        th = fit(tr, cols); res[k] += list(loss(th, te, cols))
pure = np.array(pure); gunler = np.array(gunler); ug = sorted(set(gunler)); random.seed(3)
gi = {g: np.where(gunler == g)[0] for g in ug}
print(f"test: {len(pure)} koşu, {len(ug)} gün; saf piyasa {pure.mean():.4f}")
for k in SETS:
    L = np.array(res[k]); d = L - pure; bs = []
    for _ in range(1500):
        idx = np.concatenate([gi[random.choice(ug)] for _ in ug]); bs.append(d[idx].mean())
    print(f"{k:16s} {L.mean():.4f}  fark {d.mean():+.4f}  GA [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")
th = fit(races, SETS["hepsi"]); print("tüm veriyle katsayılar: alfa %.3f" % th[0], {FN[i]: round(v, 3) for i, v in enumerate(th[1:])})
