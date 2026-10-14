"""Gölge (aday) model "Jason" (dondurulmuş v1: "Bolton", Bolton ve Chapman 1986'nın çok terimli logit yarış modelinin anısına): model_v1.json dondurulmuş kalır, aday her gece yeni veriyle yeniden eğitilir ve canlıda paralel skorlanır.
Bahis oynanmaz, kupon yapılmaz; yalnızca aynı koşularda v1 ve piyasayla karşılaştırılır (docs/data/golge.json).
Aday, bir koşunun GÜNÜNDEN ÖNCEKİ günün sonuna kadar eğitilmiştir; tahmin sabah JSON'a yazılır, sonradan değişmez."""
import os, json, glob
import numpy as np, pandas as pd
from scipy.optimize import minimize
from . import ortak as O
from .ozellik import hazirla
from . import mesafe as MS

EK = ["f_dp150_m", "f_jgen100", "f_fig3"]
LPEK = ["f_lp2"]   # piyasaya bağlı terim: form puanına (z2) girmez, s = w0·lp + lp2_a·lp² + z2 olarak ayrı uygulanır   # Jason'un Bolton'dan fazladan kullandığı özellikler (mesafe uyumu, jokey artığı)

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data")
SITE = os.path.join(KOK, "docs", "data")
YOL = os.path.join(VERI, "model_aday.json")
YOL_K = os.path.join(VERI, "model_aday_k.json")
YOL_S = os.path.join(VERI, "model_aday_s.json")
KAPI = ["f_kapi"]   # Jason-K: Jason + kapı yanlılığı (12 Ekim 2026, ikinci gölge model; Jason değişmedi)


def yukle():
    return json.load(open(YOL, encoding="utf-8")) if os.path.exists(YOL) else None


def yukle_k():
    return json.load(open(YOL_K, encoding="utf-8")) if os.path.exists(YOL_K) else None


def yukle_s():
    return json.load(open(YOL_S, encoding="utf-8")) if os.path.exists(YOL_S) else None


def kapi_ekle(d):
    """f_kapi: (hipodrom, mesafe, pist, kapı grubu iç/orta/dış) için KESİNLİKLE önceki günlerin ortalama bitiş artığı (30 ağırlıklı önsel).
    d: MS.ekle çıktısı (mesafe/pist dolu)."""
    d = d.copy()
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    res = (((rk - 1) / (d.n_at - 1).clip(lower=1)) - d.pct).clip(-1, 1); res[d.yeni.values] = np.nan
    d["_res"] = res.values
    rel = (d.st - 1) / (d.n_at - 1).clip(lower=1)
    kg = np.where(d.st <= 3, "ic", np.where(rel > 0.66, "dis", "orta")).astype(object)
    d["_anah"] = d.hipodrom.astype(str) + "|" + d.mesafe.astype(str) + "|" + d.pist.astype(str) + "|" + kg
    d["f_kapi"] = MS._onceki_ort(d, "_anah", "_res", 30.0)
    d.loc[d.mesafe.isna() | d.st.isna(), "f_kapi"] = 0.0
    return d.drop(columns=["_res", "_anah"])


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
    d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2          # piyasa olasılığının log-karesi: favori/uzun şanslı eğriliği
    feat = M["feat"] + EK + LPEK
    tr = d[(d.tarih <= son) & d.kazandi.notna() & d.lp.notna()].copy()
    th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
    A = {"surum": "aday", "ad": "Jason", "egitim_son_tarih": son, "egitim_koşu": nk, "feat": feat, "cins": M["cins"],
         "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th], "lam": M.get("lam", 100.0),
         "lp2_a": float(th[1 + feat.index("f_lp2")] / sd["f_lp2"])}
    json.dump(A, open(YOL, "w", encoding="utf-8"), ensure_ascii=False)
    print("aday model eğitildi:", son, "| koşu", nk, "| w0", round(th[0], 3))
    return A


def egit_k(son=None):
    """Jason-K: Jason özellikleri + f_kapi; aynı eğitim kuralı, ayrı dosya (data/model_aday_k.json). Jason'a dokunmaz."""
    from .calistir import yukle_model
    M = yukle_model()
    son = son or (O.tr_simdi().date() - pd.Timedelta(days=1).to_pytimedelta()).isoformat()
    d = kapi_ekle(MS.ekle(hazirla(_oku("temiz"), _oku("program"), M)))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    feat = M["feat"] + EK + LPEK + KAPI
    tr = d[(d.tarih <= son) & d.kazandi.notna() & d.lp.notna()].copy()
    th, mu, sd, nk = _fit(tr, feat, M.get("lam", 100.0))
    A = {"surum": "aday_k", "ad": "Jason-K", "egitim_son_tarih": son, "egitim_koşu": nk, "feat": feat, "cins": M["cins"],
         "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th], "lam": M.get("lam", 100.0),
         "lp2_a": float(th[1 + feat.index("f_lp2")] / sd["f_lp2"])}
    json.dump(A, open(YOL_K, "w", encoding="utf-8"), ensure_ascii=False)
    print("Jason-K eğitildi:", son, "| koşu", nk, "| w_kapi", round(th[1 + feat.index("f_kapi")], 4))
    return A


def _blok(rid):
    st = np.r_[0, np.nonzero(np.diff(rid))[0] + 1]; n = len(rid)
    return st, np.repeat(np.arange(len(st)), np.diff(np.r_[st, n]))


def _fit_s(tr, feat, lam, th0, a0):
    """Jason-S: tüm ilk-5 sırası üzerinde Plackett-Luce; ağırlıklar paylaşımlı, sıra başına ölçek a2..a5 serbest."""
    X0 = tr[feat]; mu, sd = X0.mean(), X0.std(ddof=0); X = ((X0 - mu) / sd).values; lp = tr.lp.values
    st, seg = _blok(tr.rid.values); sr = tr.sr.values; nf = X.shape[1]
    mk = [((sr >= k) | (sr <= 0)) for k in range(1, 6)]; ch = [(sr == k) for k in range(1, 6)]

    def f(par):
        w0, w, a = par[0], par[1:1 + nf], np.r_[1.0, par[1 + nf:]]
        sv = w0 * lp + X @ w; ll = 0.0; gs = np.zeros(len(sv)); ga = np.zeros(4)
        for k in range(5):
            z = a[k] * sv; m = np.where(mk[k], z, -1e18); mx = np.maximum.reduceat(m, st)
            e = np.exp(m - mx[seg]) * mk[k]; Z = np.add.reduceat(e, st); p = e / Z[seg]
            ll += z[ch[k]].sum() - (np.log(Z) + mx).sum()
            g = ch[k].astype(float) - p; gs += a[k] * g
            if k > 0: ga[k - 1] = (sv * g).sum()
        gr = -np.r_[(gs * lp).sum(), X.T @ gs, ga]; gr[1:1 + nf] += lam * w
        return -ll + 0.5 * lam * (w @ w), gr
    r = minimize(f, np.r_[th0, a0[1:]], jac=True, method="L-BFGS-B", options={"maxiter": 300})
    return r.x[:1 + nf], np.r_[1.0, r.x[1 + nf:]], mu, sd


def egit_s(son=None):
    """Jason-S: Jason özellikleri, ilk-5 sırasıyla eğitilmiş (data/model_aday_s.json). Jason'a dokunmaz."""
    from .calistir import yukle_model
    M = yukle_model()
    son = son or (O.tr_simdi().date() - pd.Timedelta(days=1).to_pytimedelta()).isoformat()
    d = MS.ekle(hazirla(_oku("temiz"), _oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    feat = M["feat"] + EK + LPEK
    d = d[d.temiz & d.kazandi.notna() & d.lp.notna() & (d.tarih.astype(str) <= son)].copy()
    d = d.sort_values(O.K + ["no"]).reset_index(drop=True); d["rid"] = d.groupby(O.K).ngroup()
    d["sr"] = pd.to_numeric(d.sira, errors="coerce").fillna(0)
    ok = d.groupby("rid").sr.apply(lambda x: all((x == k).sum() == 1 for k in range(1, 6)))
    tr = d[d.rid.map(ok)].copy().reset_index(drop=True); tr["rid"] = tr.groupby(O.K).ngroup()
    th0, _, _, _ = _fit(tr.assign(kazandi=(tr.sr == 1).astype(float)), feat, M.get("lam", 100.0))
    th, a, mu, sd = _fit_s(tr, feat, M.get("lam", 100.0), th0, np.array([1, 0.80, 0.69, 0.69, 0.69]))
    A = {"surum": "aday_s", "ad": "Jason-S", "egitim_son_tarih": son, "egitim_koşu": int(tr.rid.nunique()), "feat": feat, "cins": M["cins"],
         "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th], "lam": M.get("lam", 100.0),
         "lp2_a": float(th[1 + feat.index("f_lp2")] / sd["f_lp2"]), "a": [float(x) for x in a]}
    json.dump(A, open(YOL_S, "w", encoding="utf-8"), ensure_ascii=False)
    print("Jason-S eğitildi:", son, "| koşu", A["egitim_koşu"], "| a", np.round(a, 3))
    return A


def z2(d, A):
    """hazirla çıktısındaki satırlar için aday modelin form puanı."""
    feat = [f for f in A["feat"] if f not in LPEK]; mu, sd = pd.Series(A["mu"]), pd.Series(A["sd"]); w = np.array(A["w"])
    return ((d[feat] - mu[feat]) / sd[feat]).values @ w[1:1 + len(feat)]


def skor():
    """Günlük JSON'lardaki sonuçlanmış koşularda piyasa / v1 / aday log-kaybı (yalnız üçü de varsa)."""
    L = []; LK = []   # LK: Jason-K eksi Jason, kazanan log-olasılığı farkı
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
                if "pm3" in v:
                    LK.append(np.log(v["pm3"]) - np.log(v["pp"]) - (np.log(v["pm2"]) - np.log(v["pp"])))
    out = {"guncelleme": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "kosu": len(L), "ad_v1": "Bolton", "ad_aday": "Jason"}
    A = yukle()
    out["aday_egitim_son"] = A["egitim_son_tarih"] if A else None
    if L:
        a = np.array([(x[3], x[4], x[5]) for x in L])
        d1 = a[:, 1] - a[:, 0]; d2 = a[:, 2] - a[:, 0]; dd = a[:, 2] - a[:, 1]
        se = lambda x: float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None
        out.update({"v1_kazanc": float(d1.mean()), "v1_se": se(d1), "aday_kazanc": float(d2.mean()), "aday_se": se(d2),
                    "aday_eksi_v1": float(dd.mean()), "aday_eksi_v1_se": se(dd), "gun": len({x[0] for x in L})})
    if LK:
        x = np.array(LK); out.update({"k_eksi_jason": float(x.mean()), "k_eksi_jason_se": float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None, "k_kosu": len(x)})
    os.makedirs(SITE, exist_ok=True)
    json.dump(out, open(os.path.join(SITE, "golge.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return out
