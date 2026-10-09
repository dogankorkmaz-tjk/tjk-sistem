"""Gölge (aday) model "Jason" (dondurulmuş v1: "Bolton", Bolton ve Chapman 1986'nın çok terimli logit yarış modelinin anısına): model_v1.json dondurulmuş kalır, aday her gece yeni veriyle yeniden eğitilir ve canlıda paralel skorlanır.
Bahis oynanmaz, kupon yapılmaz; yalnızca aynı koşularda v1 ve piyasayla karşılaştırılır (docs/data/golge.json).
Aday, bir koşunun GÜNÜNDEN ÖNCEKİ günün sonuna kadar eğitilmiştir; tahmin sabah JSON'a yazılır, sonradan değişmez."""
import os, json, glob
import numpy as np, pandas as pd
from scipy.optimize import minimize
from . import ortak as O
from .ozellik import hazirla

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data")
SITE = os.path.join(KOK, "docs", "data")
YOL = os.path.join(VERI, "model_aday.json")


def yukle():
    return json.load(open(YOL, encoding="utf-8")) if os.path.exists(YOL) else None


def _oku(a):
    return pd.concat([pd.read_csv(p, low_memory=False) for p in sorted(glob.glob(os.path.join(VERI, a, "*.csv.gz")))], ignore_index=True)


def _fit(d, feat, lam=100.0):
    d = d.sort_values(O.K + ["no"]).reset_index(drop=True)
    d["rid"] = d.groupby(O.K).ngroup()
    mu, sd = d[feat].mean(), d[feat].std(ddof=0)
    X = ((d[feat] - mu) / sd).values; lp = d.lp.values; y = d.kazandi.values.astype(float)
    rid = d.rid.values; st = np.r_[0, np.nonzero(np.diff(rid))[0] + 1]; n = len(d)
    seg = np.repeat(np.arange(len(st)), np.diff(np.r_[st, n]))

    def f(th):
        w0, w = th[0], th[1:]
        s = w0 * lp + X @ w
        m = np.maximum.reduceat(s, st); e = np.exp(s - m[seg]); Z = np.add.reduceat(e, st); p = e / Z[seg]
        ll = (y * s).sum() - (np.log(Z) + m).sum()
        g = y - p
        gr = -np.r_[(g * lp).sum(), X.T @ g]; gr[1:] += lam * w
        return -ll + 0.5 * lam * (w @ w), gr
    r = minimize(f, np.r_[1.0, np.zeros(X.shape[1])], jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return r.x, mu, sd, int(d.rid.nunique())


def egit(son=None):
    """Adayı `son` tarihine (varsayılan: dün) kadar olan sonuçlarla yeniden eğitir -> data/model_aday.json."""
    from .calistir import yukle_model
    M = yukle_model()
    son = son or (O.tr_simdi().date() - pd.Timedelta(days=1).to_pytimedelta()).isoformat()
    d = hazirla(_oku("temiz"), _oku("program"), M)
    tr = d[(d.tarih <= son) & d.kazandi.notna() & d.lp.notna()].copy()
    th, mu, sd, nk = _fit(tr, M["feat"], M.get("lam", 100.0))
    A = {"surum": "aday", "ad": "Jason", "egitim_son_tarih": son, "egitim_koşu": nk, "feat": M["feat"], "cins": M["cins"],
         "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th], "lam": M.get("lam", 100.0)}
    json.dump(A, open(YOL, "w", encoding="utf-8"), ensure_ascii=False)
    print("aday model eğitildi:", son, "| koşu", nk, "| w0", round(th[0], 3))
    return A


def z2(d, A):
    """hazirla çıktısındaki satırlar için aday modelin form puanı."""
    feat = A["feat"]; mu, sd = pd.Series(A["mu"]), pd.Series(A["sd"]); w = np.array(A["w"])
    return ((d[feat] - mu[feat]) / sd[feat]).values @ w[1:]


def skor():
    """Günlük JSON'lardaki sonuçlanmış koşularda piyasa / v1 / aday log-kaybı (yalnız üçü de varsa)."""
    L = []
    for y in sorted(glob.glob(os.path.join(SITE, "gun", "*.json"))):
        o = json.load(open(y, encoding="utf-8"))
        for h in o["hipodromlar"]:
            for k in h["kosular"]:
                s = k.get("sonuc")
                if not s:
                    continue
                kz = [v for v in s.values() if v.get("sira") == 1]
                if len(kz) != 1 or "pm2" not in kz[0]:
                    continue
                v = kz[0]
                L.append((o["tarih"], h["id"], k["kosu"], np.log(v["pp"]), np.log(v["pm"]), np.log(v["pm2"])))
    out = {"guncelleme": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "kosu": len(L), "ad_v1": "Bolton", "ad_aday": "Jason"}
    A = yukle()
    out["aday_egitim_son"] = A["egitim_son_tarih"] if A else None
    if L:
        a = np.array([(x[3], x[4], x[5]) for x in L])
        d1 = a[:, 1] - a[:, 0]; d2 = a[:, 2] - a[:, 0]; dd = a[:, 2] - a[:, 1]
        se = lambda x: float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None
        out.update({"v1_kazanc": float(d1.mean()), "v1_se": se(d1), "aday_kazanc": float(d2.mean()), "aday_se": se(d2),
                    "aday_eksi_v1": float(dd.mean()), "aday_eksi_v1_se": se(dd), "gun": len({x[0] for x in L})})
    os.makedirs(SITE, exist_ok=True)
    json.dump(out, open(os.path.join(SITE, "golge.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return out
