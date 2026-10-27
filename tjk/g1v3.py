"""G1-S v3 (24 Ekim 2026): G1 özellikleri + Jason'ın 38 özelliği + galop, ortak eğitim (ön kayıt/test: data/analiz/entegre_v3.py, hipotez_defteri 12:45 ve v3 doğrulama).
egit(): tüm geçmişle katsayıları data/analiz/g1v3_katsayi.json'a yazar. z6 puanı = X·b (G1) + zj (Jason özellik doğrusal kısmı, calistir'de at başına) + lp² terimi (AGF'den) + galop.
Canlıda g1.z6 bu dosya varsa v3'ü kullanır; zj eksikse o koşu için G1-S puanı üretilmez."""
import datetime as dt, glob, json, os
import numpy as np
from scipy.optimize import minimize
from . import g1 as G

KOK = G.KOK
YOL = os.path.join(KOK, "data", "analiz", "g1v3_katsayi.json")


def yukle():
    return json.load(open(YOL)) if os.path.exists(YOL) else None


def zj(d, c):
    """d: live satırlar (hazirla+MS.ekle). Jason özellik doğrusal kısmı (f_lp2 HARİÇ; o AGF'den z6'da eklenir)."""
    fe = c["featJ"]; mu = np.array(c["muJ"]); sd = np.array(c["sdJ"]); w = np.array(c["wJ"]); i2 = c["i_lp2"]
    X = np.nan_to_num(d[[f for f in fe if f != "f_lp2"]].values.astype(float))
    keep = [i for i, f in enumerate(fe) if f != "f_lp2"]
    return ((X - mu[keep]) / sd[keep]) @ w[keep]


def ze(d, c):
    """Elo (rakip gücü) özelliklerinin zj'ye katkısı (T27 ileri gölge: z6 - ze = Elo'suz puan). Elo özelliği modelde yoksa 0."""
    fe = c["featJ"]; ix = [i for i, f in enumerate(fe) if f in ("f_elo", "f_rak3")]
    if not ix or any(fe[i] not in d.columns for i in ix):
        return np.zeros(len(d))
    mu = np.array(c["muJ"]); sd = np.array(c["sdJ"]); w = np.array(c["wJ"])
    X = np.nan_to_num(d[[fe[i] for i in ix]].values.astype(float))
    return ((X - mu[ix]) / sd[ix]) @ w[ix]


def z6(atlar, t, c):
    """At başına tam v3 puanı (alfa·log p hariç). atlar: no, at, jokey, kg, hk, agf, zj. zj eksikse None."""
    at = [a for a in atlar if a.get("agf") and not a.get("kosmaz")]
    if len(at) < 5 or any(a.get("zj") is None for a in at):
        return None
    anahtar = t.isoformat()
    if G._ST["son"] != anahtar:
        G._ST["son"] = anahtar; G._ST["h"] = G._gecmis(G._satirlar(), anahtar)
    H, J, AJ = G._ST["h"]
    ok = [{"at": a["at"], "jokey": a["jokey"], "kilo": a.get("kg"), "hnd": a.get("hk")} for a in at]
    X = G._oz(H, J, AJ, ok, None, t.toordinal()); z = X @ np.array(c["b"])
    z = z + np.array([a["zj"] for a in at])
    tot = sum(a["agf"] for a in at); lp = np.log(np.maximum(np.array([a["agf"] / tot for a in at]), 1e-6))
    z = z + ((lp ** 2 - c["muJ"][c["i_lp2"]]) / c["sdJ"][c["i_lp2"]]) * c["wJ"][c["i_lp2"]]
    if c.get("galop"):
        try:
            cg = c["galop"]; F = (np.array([G.galop_f(a["at"], t) for a in at]) - np.array(cg["mu"])) / np.array(cg["sd"]); z = z + F @ np.array(cg["b"])
        except Exception as e:
            print("galop z hatası:", repr(e))
    return {a["no"]: float(v) for a, v in zip(at, z)}


def _steps(s, gam, nstep=5):
    N = len(s); idx = np.arange(N); mask = s > -1e8; out = []; ds = np.zeros_like(s); dg = np.zeros(nstep - 1)
    for j in range(nstep):
        z = np.where(mask, gam[j] * s, -1e30); z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
        out.append(-np.log(p[idx, j] + 1e-12).sum()); d = p.copy(); d[idx, j] -= 1; ds += gam[j] * d
        if j:
            dg[j - 1] = (d * np.where(mask, s, 0)).sum()
        mask[idx, j] = False
    return sum(out), ds, dg


def egit(l2=30.0, lj=50.0, adim=5, bas_galop="2026-02-01", l2g=20.0):
    from . import golge as GL
    from .ozellik import hazirla
    from .calistir import yukle_model
    M = yukle_model(); FEAT = M["feat"] + GL.EK + GL.LPEK; NJ = len(FEAT)
    d = GL.MS.ekle(hazirla(GL._oku("temiz"), GL._oku("program"), M)); d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    from . import elo as EL                                    # rakip gücü (Elo) özellikleri, 28 Ekim 2026 (T27, ön kayıtlı ablasyon iki dönemde geçti)
    d = EL.ekle(d); FEAT = FEAT + EL.EXTRA_FEAT; NJ = len(FEAT)
    JD = {}
    for key, g in d.groupby(["tarih", "hipodrom", "kosu"], sort=False):
        JD[key] = (g.no.astype(int).values, np.nan_to_num(g[FEAT].values.astype(float)))
    K = {}
    for r in G._satirlar():
        K.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
    H, J, AJ = {}, {}, {}; R = []
    for key in sorted(K):
        ok = [r for r in K[key] if r["kosmadi"] != "True" and G._fl(r["ganyan"], 0) > 1 and G._fl(r["sira"], 0) > 0]
        if len(ok) < 6:
            continue
        ok.sort(key=lambda r: G._fl(r["sira"]))
        if [G._fl(r["sira"]) for r in ok[:adim]] != [float(i) for i in range(1, adim + 1)]:
            continue
        n = len(ok); inv = np.array([1 / G._fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); gun = dt.date.fromisoformat(key[0]).toordinal()
        q = JD.get(key); nos = [int(G._fl(r["no"], 0)) for r in ok]
        if q is not None:
            ix = {nn: i for i, nn in enumerate(q[0])}
            if all(nn in ix for nn in nos):
                F = np.array([G.galop_f(r["at"], dt.date.fromisoformat(key[0])) for r in ok]) if key[0] >= bas_galop else None
                R.append(dict(lm=np.log(pm), X=G._oz(H, J, AJ, ok, pm, gun), XJ=q[1][[ix[nn] for nn in nos]], F=F))
        for i, r in enumerate(ok):
            pct = 1 - (G._fl(r["sira"]) - 1) / (n - 1); win = 1.0 if i == 0 else 0.0
            H.setdefault(r["at"], []).append((gun, pct, win - pm[i]))
            j = J.setdefault(r["jokey"], [0, 0.0]); j[0] += 1; j[1] += win - pm[i]
            a = AJ.setdefault((r["at"], r["jokey"]), [0, 0.0]); a[0] += 1; a[1] += win - pm[i]
    N = len(R); Mx = max(len(r["lm"]) for r in R)
    LM = np.full((N, Mx), -1e9); XX = np.zeros((N, Mx, 9)); XJ = np.zeros((N, Mx, NJ)); FF = np.zeros((N, Mx, 7)); gv = np.zeros(N, bool)
    for k, r in enumerate(R):
        m = len(r["lm"]); LM[k, :m] = r["lm"]; XX[k, :m] = r["X"]; XJ[k, :m] = r["XJ"]
        if r["F"] is not None:
            FF[k, :m] = r["F"]; gv[k] = True
    msk = LM > -1e8; mu = XJ[msk].mean(0); sd = XJ[msk].std(0) + 1e-9; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0)

    def f(t):
        s = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9); L, ds, dg = _steps(s, np.r_[1.0, t[10 + NJ:10 + NJ + adim - 1]], adim)
        g = np.r_[(ds * LM.clip(-50, 0)).sum(), np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], np.einsum("nm,nmk->k", ds, Z) + 2 * lj * t[10:10 + NJ], dg]
        return L + l2 * (t[1:10] @ t[1:10]) + lj * (t[10:10 + NJ] @ t[10:10 + NJ]), g
    t0 = np.zeros(10 + NJ + adim - 1); t0[0] = 1; t0[10 + NJ:] = 1
    t = minimize(f, t0, jac=True, method="L-BFGS-B", options={"maxiter": 400}).x
    S0 = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9)
    out = {"alfa": float(t[0]), "b": [float(x) for x in t[1:10]], "gam": [1.0] + [float(x) for x in t[10 + NJ:]], "featJ": FEAT, "muJ": [float(x) for x in mu], "sdJ": [float(x) for x in sd],
           "wJ": [float(x) for x in t[10:10 + NJ]], "i_lp2": FEAT.index("f_lp2"), "n_kosu": N, "egitim": dt.date.today().isoformat()}
    # galop ikinci aşama (ofset = v3 aşama 1)
    sel = np.where(gv)[0]
    if len(sel) > 200:
        S = S0[sel]; F = FF[sel]; mk = S > -1e8; fmu = F[mk].mean(0); fsd = F[mk].std(0) + 1e-9; Zg = (F - fmu) / fsd; n2 = len(sel); idx = np.arange(n2)

        def fg(b):
            s = np.where(mk, S + Zg @ b, -1e9); s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True); dd = p.copy(); dd[idx, 0] -= 1
            return -np.log(p[idx, 0] + 1e-12).sum() + l2g * (b @ b), np.einsum("nm,nmk->k", dd, Zg) + 2 * l2g * b
        b = minimize(fg, np.zeros(7), jac=True, method="L-BFGS-B").x
        out["galop"] = {"b": [float(x) for x in b], "mu": [float(x) for x in fmu], "sd": [float(x) for x in fsd], "n_kosu": int(n2), "bas": bas_galop}
    json.dump(out, open(YOL, "w"), indent=1)
    return out
