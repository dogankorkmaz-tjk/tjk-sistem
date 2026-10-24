"""Benter-G1 gölge modeli (24 Ekim 2026): kapanış piyasası (ofset) + form/dinlenme/kilo/handikap/jokey özellikleri.
Koşul içi çok terimli logit. egit(): tüm sonuç geçmişiyle katsayıları data/analiz/g1_katsayi.json'a yazar.
tahmin(r, t): tek koşu DataFrame'i (at, jokey, kilo, hnd, p_piyasa) için olasılık. Geçmiş = t gününden önceki data/sonuclar."""
import csv, datetime as dt, glob, gzip, json, math, os
import numpy as np
from scipy.optimize import minimize
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOL = os.path.join(KOK, "data", "analiz", "g1_katsayi.json")
FN = ["f3", "f10", "ovr", "dinlen", "kilo", "hnd", "jok", "athj", "ilk"]
_ST = {"son": None}


def _fl(x, d=None):
    try:
        v = float(x)
        return d if v != v else v
    except Exception:
        return d


def _satirlar():
    for f in sorted(glob.glob(os.path.join(KOK, "data", "sonuclar", "*.csv.gz"))):
        yield from csv.DictReader(gzip.open(f, "rt", encoding="utf-8"))


def _oz(H, J, AJ, ok, pm, gun):
    n = len(ok)
    kil = np.array([_fl(r["kilo"], np.nan) for r in ok]); hnd = np.array([_fl(r["hnd"], np.nan) for r in ok])
    kil = np.zeros(n) if np.all(np.isnan(kil)) else np.nan_to_num(kil - np.nanmean(kil))
    hnd = np.zeros(n) if np.all(np.isnan(hnd)) else np.nan_to_num(hnd - np.nanmean(hnd))
    X = np.zeros((n, 9))
    for i, r in enumerate(ok):
        h = H.get(r["at"], []); j = J.get(r["jokey"], [0, 0.0]); aj = AJ.get((r["at"], r["jokey"]), [0, 0.0])
        def m(k, prior, w):
            l = h[-k:]; return (sum(x[1] for x in l) + prior * w) / (len(l) + w)
        X[i] = [m(3, .5, 2) - .5, m(10, .5, 3) - .5, sum(x[2] for x in h[-10:]) / (len(h[-10:]) + 3),
                math.log(1 + min(120, gun - h[-1][0])) / 4 if h else 0.0, kil[i] / 3, hnd[i] / 10,
                j[1] / (j[0] + 30), aj[1] / (aj[0] + 5), 1.0 if not h else 0.0]
    return X


def _gecmis(rows_iter, onceki=None):
    """rows_iter: satırlar. onceki: bu tarihten (dahil değil) öncesini kullan. Döner (H,J,AJ)."""
    K = {}
    for r in rows_iter:
        if onceki and r["tarih"] >= onceki:
            continue
        K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
    H, J, AJ = {}, {}, {}
    for key in sorted(K):
        ok = [r for r in K[key] if r["kosmadi"] != "True" and _fl(r["ganyan"], 0) > 1 and _fl(r["sira"], 0) > 0]
        n = len(ok)
        if n < 4:
            continue
        inv = np.array([1 / _fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum()
        gun = dt.date.fromisoformat(key[0]).toordinal()
        w = [i for i, r in enumerate(ok) if r["sira"] == "1"]
        if len(w) != 1:
            continue
        for i, r in enumerate(ok):
            pct = 1 - (_fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == w[0] else 0.0
            H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
            j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
            a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
    return H, J, AJ


def egit(l2=30.0):
    rows = list(_satirlar()); K = {}
    for r in rows:
        K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
    H, J, AJ = {}, {}, {}; R = []
    for key in sorted(K):
        ok = [r for r in K[key] if r["kosmadi"] != "True" and _fl(r["ganyan"], 0) > 1 and _fl(r["sira"], 0) > 0]
        n = len(ok)
        if n < 4:
            continue
        inv = np.array([1 / _fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
        w = [i for i, r in enumerate(ok) if r["sira"] == "1"]
        if len(w) != 1:
            continue
        R.append((np.log(pm), _oz(H, J, AJ, ok, pm, gun), w[0]))
        for i, r in enumerate(ok):
            pct = 1 - (_fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == w[0] else 0.0
            H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
            j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
            a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
    M = max(len(x[0]) for x in R); N = len(R)
    LM = np.full((N, M), -1e9); XX = np.zeros((N, M, 9)); W = np.zeros(N, int)
    for k, (lm, X, w) in enumerate(R):
        LM[k, :len(lm)] = lm; XX[k, :len(lm)] = X; W[k] = w

    def f(th):
        a, b = th[0], th[1:]
        s = a * LM + XX @ b; s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True)
        idx = np.arange(N); L = -np.log(p[idx, W] + 1e-12).sum() + l2 * (b @ b)
        d = p.copy(); d[idx, W] -= 1
        return L, np.concatenate([[(d * LM.clip(-50, 0)).sum()], np.einsum("nm,nmk->k", d, XX) + 2 * l2 * b])
    th = minimize(f, np.r_[1.0, np.zeros(9)], jac=True, method="L-BFGS-B").x
    out = {"alfa": float(th[0]), "b": [float(x) for x in th[1:]], "fn": FN, "n_kosu": N,
           "son_tarih": max(k[0] for k in K), "egitim": dt.date.today().isoformat()}
    json.dump(out, open(YOL, "w"), indent=1); return out


def tahmin(r, t):
    """r: DataFrame (at, jokey, kilo, hnd, p_piyasa; kosmadi/sira önemsiz). t: datetime.date. None dönebilir."""
    if not os.path.exists(YOL) or len(r) < 4:
        return None
    anahtar = t.isoformat()
    if _ST["son"] != anahtar:
        _ST["son"] = anahtar; _ST["h"] = _gecmis(_satirlar(), anahtar)
    H, J, AJ = _ST["h"]; c = json.load(open(YOL))
    ok = [{"at": x.at, "jokey": x.jokey, "kilo": getattr(x, "kilo", None), "hnd": getattr(x, "hnd", None)} for x in r.itertuples()]
    X = _oz(H, J, AJ, ok, None, t.toordinal())
    p = np.asarray(r.p_piyasa, float); s = c["alfa"] * np.log(np.clip(p, 1e-9, 1)) + X @ np.array(c["b"])
    s -= s.max(); e = np.exp(s); return e / e.sum()


# ---- G1-S: ilk 3 sıra + sıra üsleri ile eğitilmiş varyant (egzotik bahisler için, 24 Ekim 2026) ----
YOL3 = os.path.join(KOK, "data", "analiz", "g1s_katsayi.json")


def egit3(l2=30.0, adim=5):
    """İlk 5 sıra (varsa) patlatılmış logit + sıra üsleri g2..g5. Egzotik (≤3 sıra) ve tabela/sıralı 5'li gölgeleri aynı katsayıları kullanır."""
    K = {}
    for r in _satirlar():
        K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
    H, J, AJ = {}, {}, {}; R = []
    for key in sorted(K):
        ok = [r for r in K[key] if r["kosmadi"] != "True" and _fl(r["ganyan"], 0) > 1 and _fl(r["sira"], 0) > 0]
        n = len(ok)
        if n < 6:
            continue
        ok.sort(key=lambda r: _fl(r["sira"]))
        if [_fl(r["sira"]) for r in ok[:adim]] != [float(i) for i in range(1, adim + 1)]:
            continue
        inv = np.array([1 / _fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
        R.append((np.log(pm), _oz(H, J, AJ, ok, pm, gun)))
        for i, r in enumerate(ok):
            pct = 1 - (_fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == 0 else 0.0
            H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
            j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
            a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
    N = len(R); M = max(len(x[0]) for x in R); LM = np.full((N, M), -1e9); XX = np.zeros((N, M, 9))
    for k, (lm, X) in enumerate(R):
        LM[k, :len(lm)] = lm; XX[k, :len(lm)] = X
    idx = np.arange(N); ng = adim - 1

    def f(t):
        a, b, gam = t[0], t[1:10], np.r_[1.0, t[10:10 + ng]]; s = a * LM + XX @ b
        mask = LM > -1e8; ds = np.zeros_like(s); dg = np.zeros(ng); L = l2 * (b @ b)
        for j in range(adim):
            z = np.where(mask, gam[j] * s, -1e30); z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
            L += -np.log(p[idx, j] + 1e-12).sum(); d = p.copy(); d[idx, j] -= 1; ds += gam[j] * d
            if j:
                dg[j - 1] = (d * np.where(mask, s, 0)).sum()
            mask[idx, j] = False
        g = np.zeros(10 + ng); g[0] = (ds * LM.clip(-50, 0)).sum(); g[1:10] = np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * b; g[10:] = dg
        return L, g
    t0 = np.zeros(10 + ng); t0[0] = 1; t0[10:] = 1
    t = minimize(f, t0, jac=True, method="L-BFGS-B").x
    out = {"alfa": float(t[0]), "b": [float(x) for x in t[1:10]], "gam": [1.0] + [float(x) for x in t[10:]], "g2": float(t[10]), "g3": float(t[11]),
           "n_kosu": N, "egitim": dt.date.today().isoformat()}
    json.dump(out, open(YOL3, "w"), indent=1); return out


def z6(atlar, t):
    """Egzotik gölge (G1-S) için at başına puan X·b (alfa*log(p) ayrı eklenir). atlar: {no, at, jokey, kg, hk, agf...}. Veri eksikse None."""
    try:
        from . import g1v3 as _V3; c3 = _V3.yukle()           # G1-S v3 (24 Ekim 2026): varsa ana puan bu
    except Exception as e:
        print("v3 yükleme hatası:", repr(e)); c3 = None
    if c3:
        return _V3.z6(atlar, t, c3)
    if not os.path.exists(YOL3):
        return None
    at = [a for a in atlar if a.get("agf") and not a.get("kosmaz")]
    if len(at) < 5:
        return None
    anahtar = t.isoformat()
    if _ST["son"] != anahtar:
        _ST["son"] = anahtar; _ST["h"] = _gecmis(_satirlar(), anahtar)
    H, J, AJ = _ST["h"]; c = json.load(open(YOL3))
    ok = [{"at": a["at"], "jokey": a["jokey"], "kilo": a.get("kg"), "hnd": a.get("hk")} for a in at]
    X = _oz(H, J, AJ, ok, None, t.toordinal()); z = X @ np.array(c["b"])
    if os.path.exists(YOLG):                                   # galop (idman) özellikleri: G1-S'nin parçası (v2, 24 Ekim 2026 11:30)
        try:
            cg = json.load(open(YOLG)); F = (np.array([galop_f(a["at"], t) for a in at]) - np.array(cg["mu"])) / np.array(cg["sd"])
            z = z + F @ np.array(cg["b"])
        except Exception as e:
            print("galop z hatası:", repr(e))
    return {a["no"]: float(v) for a, v in zip(at, z)}


def z6_doldur(obj):
    """Başlamamış koşuların atlarına z6 (G1-S puanı) ekler; egzotik, tabela ve sıralı 5'li gölgeleri bunu kullanır. Eksikse sessizce geçer."""
    try:
        t = dt.date.fromisoformat(obj["tarih"])
        _c3 = None
        try:
            from . import g1v3 as _V3; _c3 = _V3.yukle()
        except Exception as e:
            print("v3 yükleme hatası:", repr(e))
        c2 = None
        if _c3:
            obj["w0_g1"] = _c3["alfa"]; obj["a_g1"] = [round(x, 4) for x in _c3["gam"]]; obj["g1_surum"] = "v3"
            ii = _c3["i_lp2"]; c2 = _c3["wJ"][ii] / _c3["sdJ"][ii]; obj["lp2_g1"] = round(c2, 6)      # canlı mod: z6b = z6 - c2*log(p_agf)^2; tarayıcı güncel oranla w0*l + c2*l^2 + z6b hesaplar
        elif os.path.exists(YOL3):
            c = json.load(open(YOL3)); obj["w0_g1"] = c["alfa"]; obj["a_g1"] = [round(x, 4) for x in c["gam"]]; obj["g1_surum"] = "v2"
        for h in obj["hipodromlar"]:
            for k in h["kosular"]:
                if k.get("sonuc") or all(a.get("z6") is not None and (c2 is None or a.get("z6b") is not None) for a in k.get("atlar", []) if a.get("agf") and not a.get("kosmaz")):
                    continue
                zz = z6(k.get("atlar", []), t)
                if zz:
                    at_ = [a for a in k["atlar"] if a.get("agf") and not a.get("kosmaz")]; tot_ = sum(a["agf"] for a in at_)
                    for a in k["atlar"]:
                        if a["no"] in zz:
                            a["z6"] = round(zz[a["no"]], 4)
                            if c2 is not None:
                                a["z6b"] = round(zz[a["no"]] - c2 * math.log(max(a["agf"] / tot_, 1e-6)) ** 2, 4)
    except Exception as e:
        print("z6 doldurma hatası:", repr(e))


# ---- Galop (idman) özellikleri: G1-S'nin bir parçası (24 Ekim 2026, ön kayıtlı test: data/analiz/ozellik_galop.py) ----
YOLG = os.path.join(KOK, "data", "analiz", "g1s_galop.json")
GFN = ["say30", "gun", "sprint", "rel_son", "rel_en", "yog", "yok"]
_GT = {"t": None}


def _nrm(s):
    return str(s or "").upper().translate(str.maketrans("İıŞşĞğÜüÖöÇç", "IISSGGUUOOCC")).strip()


def _galop():
    if _GT["t"] is None:
        import pandas as pd
        fs = sorted(glob.glob(os.path.join(KOK, "data", "galop", "*.csv.gz")))
        if not fs:
            _GT["t"] = {}
            return _GT["t"]
        G = pd.concat([pd.read_csv(f) for f in fs])
        G["atn"] = G["at"].map(_nrm); G["itd"] = pd.to_datetime(G.it); G["p400"] = pd.to_numeric(G.p400, errors="coerce")
        G["rel"] = (G.p400 - G.groupby(["it", "tur"]).p400.transform("median")).clip(-4, 4)
        G["yog"] = G.durum.isin(["Çalışarak", "Hafif Çalışarak"]).astype(float); G["spr"] = (G.tur == "Sprint").astype(float)
        _GT["t"] = {a: x.sort_values("itd") for a, x in G.groupby("atn")}
    return _GT["t"]


def galop_f(ad, t):
    """t: datetime.date. Yarış gününden ÖNCEKİ 30 gün. Döner 7 özellik (GFN)."""
    import pandas as pd
    x = _galop().get(_nrm(ad)); tt = pd.Timestamp(t); f = [0.0, 30.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    if x is not None:
        y = x[(x.itd < tt) & (x.itd >= tt - pd.Timedelta(days=30))]
        if len(y):
            f = [float(len(y)), float((tt - y.itd.max()).days), float(y.spr.sum()), float(y.rel.iloc[-1]) if y.rel.notna().iloc[-1] else 0.0,
                 float(y.rel.min()) if y.rel.notna().any() else 0.0, float(y.yog.mean()), 0.0]
    return f


def egit_galop(l2=20.0, bas="2026-02-01"):
    """G1-S ofsetli (alfa*log p + X b), galop katsayıları ridge ile 2026-02+ koşularda; galop tablosu 1 Ocak 2026'dan başlar."""
    if not os.path.exists(YOL3) or not glob.glob(os.path.join(KOK, "data", "galop", "*.csv.gz")):
        return None
    c3 = json.load(open(YOL3)); b1 = np.array(c3["b"]); al = c3["alfa"]
    K = {}
    for r in _satirlar():
        K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
    H, J, AJ = {}, {}, {}; S0, FF, W = [], [], []
    for key in sorted(K):
        ok = [r for r in K[key] if r["kosmadi"] != "True" and _fl(r["ganyan"], 0) > 1 and _fl(r["sira"], 0) > 0]
        n = len(ok)
        if n < 4:
            continue
        inv = np.array([1 / _fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
        w = [i for i, r in enumerate(ok) if r["sira"] == "1"]
        if len(w) != 1:
            continue
        if key[0] >= bas:
            X = _oz(H, J, AJ, ok, pm, gun); d = dt.date.fromisoformat(key[0])
            S0.append(al * np.log(pm) + X @ b1); FF.append(np.array([galop_f(r["at"], d) for r in ok])); W.append(w[0])
        for i, r in enumerate(ok):
            pct = 1 - (_fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == w[0] else 0.0
            H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
            j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
            a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
    N = len(W); M = max(len(s) for s in S0); S = np.full((N, M), -1e9); F = np.zeros((N, M, 7))
    for k in range(N):
        S[k, :len(S0[k])] = S0[k]; F[k, :len(S0[k])] = FF[k]
    msk = S > -1e8; mu = F[msk].mean(0); sd = F[msk].std(0) + 1e-9; Z = (F - mu) / sd; idx = np.arange(N); Wa = np.array(W)

    def f(b):
        s = S + Z @ b; s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True); d = p.copy(); d[idx, Wa] -= 1
        return -np.log(p[idx, Wa] + 1e-12).sum() + l2 * (b @ b), np.einsum("nm,nmk->k", d, Z) + 2 * l2 * b
    b = minimize(f, np.zeros(7), jac=True, method="L-BFGS-B").x
    out = {"b": [float(x) for x in b], "mu": [float(x) for x in mu], "sd": [float(x) for x in sd], "n_kosu": N, "bas": bas, "egitim": dt.date.today().isoformat(), "fn": GFN}
    json.dump(out, open(YOLG, "w"), indent=1); return out
