"""Benter-K (GÖLGE, 6 Kasım 2026, kullanıcı kararı): T155 birleşik aday modeli, üretimde ileriye dönük takip için.
Model = G1-S v3 (Benter) + video olay (T142 OV) + düzeltilmiş video şeridi (T149 V2) + yarış-günü sahipli soy/yaş (T146 SYG)
        + sıraya özgü δ (T154: adım j≥1 puanı γ_j·(s + P·δ)). Galop ikinci aşaması Benter'deki gibi.
Karar/ön kayıt: hipotez_defteri 2026-11-06 12:30 (T154), 12:45 (T155); gölge kaydı 2026-11-06 15:00.
Ana model DEĞİŞMEZ: Benter (z6) olduğu gibi kalır; bu modül yalnız ek alanlar yazar (zk, zkd, zk6; obj w0_k, a_k).
Özellik kodu data/analiz/t152_ozellik.py ile birebir (doğrulama: data/analiz/g1k_dogrula.py)."""
import datetime as dt, glob, gzip, json, os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from . import g1 as G

KOK = G.KOK
YOL = os.path.join(KOK, "data", "analiz", "g1k_katsayi.json")
PF = ["f_t2_d", "f_t2_a", "f_t2_k", "f_t3_a", "f_t3_e", "f_t3_d", "f_s6top3", "f_hpct3", "f_st", "f_kilo", "f_hnd", "f_yas", "f_elo_m"]   # δ özellikleri (T154 ön kaydı)
OZ = {"OV": ["ov_gain", "ov_fin", "ov_tot", "ov_flop", "ov_unl", "ov_var"],
      "V2": ["v2_lead_frac", "v2_top3_frac", "v2_mean_rank", "v2_early_rank", "v2_late_rank", "v2_vol", "v2_fade", "v2_lead_lost", "v2_var"],
      "SYG": ["e_fm", "e_ff", "e_br", "e_ow", "e_bmb", "e_bpist", "age_g", "age_g3", "age_gf"]}
EK = OZ["OV"] + OZ["V2"] + OZ["SYG"]


def yukle():
    return json.load(open(YOL)) if os.path.exists(YOL) else None


# ---------- özellikler (t152_ozellik.py ile aynı algoritma) ----------
def _video():
    S = []
    for f in glob.glob(os.path.join(KOK, "data", "video_seyir", "20*.json")):
        b = os.path.basename(f)[:-5].split("_")
        if len(b) != 3:
            continue
        try:
            j = json.load(open(f))
        except Exception:
            continue
        if j.get("okuyucu") != "rakam1":
            continue
        nums = [int(x) for x in j.get("numaralar") or []]; n = len(nums)
        oz = j.get("ozet") or {}
        z = [x["sira"] for x in j.get("zaman") or [] if x.get("sira")]
        kapi = list(j.get("numaralar") or [])[:j.get("kutu", 10)]
        while z and z[0] == kapi:
            z.pop(0)
        L = len(z); k = j.get("kutu", 10); arka = (k + 1 + n) / 2.0
        for no in nums:
            o = oz.get(str(no)) or {}
            row = [b[0], b[1], int(b[2]), no, o.get("erken"), o.get("orta"), o.get("gec"), o.get("son")]
            if L >= 15 and n >= 2:
                r = np.array([(fr.index(no) + 1) if no in fr else arka for fr in z], float); a_, c_ = L // 3, 2 * L // 3
                row += [(r == 1).mean(), (r <= 3).mean(), (r.mean() - 1) / (n - 1), (r[:a_].mean() - 1) / (n - 1), (r[c_:].mean() - 1) / (n - 1),
                        np.abs(np.diff(r)).mean() / (n - 1), float((r[c_ - L // 3:] == 1).any()), r[:a_].mean()]
            else:
                row += [np.nan] * 8
            S.append(row)
    return pd.DataFrame(S, columns=["tarih", "hipodrom", "kosu", "no", "erken", "orta", "gec", "son", "lead_frac", "top3_frac", "mean_rank", "early_rank",
                                    "late_rank", "vol", "led_late", "early_abs"]).drop_duplicates(["tarih", "hipodrom", "kosu", "no"])


def _ayoz():
    """Resmî API arşivinden (data/atyarisi) at düzeyi soy/yetiştirici/doğum (t146_hazirla.py ile aynı alanlar). Sahip burada KULLANILMAZ (yarış günü d.sahip)."""
    R = []
    for f in sorted(glob.glob(os.path.join(KOK, "data", "atyarisi", "*.json.gz"))):
        try:
            j = json.load(gzip.open(f))
        except Exception:
            continue
        t = os.path.basename(f)[:10]
        for hip, rs in (j.get("program") or {}).items():
            if hip == "karma":
                continue
            for r in rs or []:
                for x in r.get("horses", []) or []:
                    p = x.get("parents") or {}; g = lambda k: ((p.get(k) or {}).get("name"))
                    R.append((t, hip, r.get("number"), x.get("number"), g("father"), g("fatherOfMother"), g("fatherOfFather"), (x.get("breeder") or {}).get("name"), x.get("birthdateEpoch")))
    A = pd.DataFrame(R, columns=["tarih", "hipodrom", "kosu", "no", "baba", "annebaba", "babababa", "yetistirici", "dogum"])
    A = A.dropna(subset=["kosu", "no"]); A["kosu"] = A.kosu.astype(int); A["no"] = A.no.astype(int)
    return A.drop_duplicates(["tarih", "hipodrom", "kosu", "no"])


def _onceki3(d, cols, out):
    d = d.sort_values(["at", "tarih", "kosu"]); g = d.groupby("at", sort=False)
    for c, n in zip(cols, out):
        d[n] = g[c].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    return d


def _grup(d, grup, V=None, A=None):
    d = d.copy(); d["_i"] = np.arange(len(d))
    if grup in ("OV", "V2"):
        d = d.merge(V, on=["tarih", "hipodrom", "kosu", "no"], how="left")
        sira = pd.to_numeric(d.sira, errors="coerce")
        if grup == "OV":
            d["_g"] = d.orta - d.gec; d["_f"] = d.gec - d.son; d["_t"] = d.erken - d.son
            d["_flop"] = np.where(d.orta.notna(), ((d.son - d.orta) >= 3).astype(float), np.nan)
            d["_unl"] = np.where(d.orta.notna(), (((d.orta - d.gec) >= 2) & (d.son >= d.gec)).astype(float), np.nan)
            out = OZ["OV"][:5]; d = _onceki3(d, ["_g", "_f", "_t", "_flop", "_unl"], out)
            d["ov_var"] = d.ov_gain.notna().astype(float)
        else:
            d["fade"] = np.where(d.early_abs.notna(), ((d.early_abs <= 2) & (sira >= 4)).astype(float), np.nan)
            d["lead_lost"] = np.where(d.early_abs.notna(), ((d.led_late == 1) & (sira >= 3)).astype(float), np.nan)
            src = ["lead_frac", "top3_frac", "mean_rank", "early_rank", "late_rank", "vol", "fade", "lead_lost"]
            out = ["v2_" + c for c in src]; d = _onceki3(d, src, out); d["v2_var"] = d.v2_lead_frac.notna().astype(float)
        for n in out:
            d[n] = d[n].fillna(0.0)
    else:   # SYG
        d = d.merge(A[["tarih", "hipodrom", "kosu", "no", "baba", "annebaba", "babababa", "yetistirici", "dogum"]].rename(columns={"baba": "baba_a"}),
                    on=["tarih", "hipodrom", "kosu", "no"], how="left")
        d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
        n_at = d.groupby(["tarih", "hipodrom", "kosu"]).no.transform("count")
        d["res"] = pd.to_numeric(d.kazandi, errors="coerce").fillna(0) - 1.0 / n_at
        mes = pd.to_numeric(d.mesafe, errors="coerce"); d["mb"] = pd.cut(mes, [0, 1399, 1799, 2199, 9999], labels=False).astype("float")
        d["yz"] = np.where(d.pist.astype(str).str.lower().str.contains("çim|cim"), "c", "k")
        d["k_baba_mb"] = np.where(d.baba_a.notna(), d.baba_a.astype(str) + "|" + d.mb.astype(str), None)
        d["k_baba_pist"] = np.where(d.baba_a.notna(), d.baba_a.astype(str) + "|" + d.yz, None)

        def enc(col, shrink=50.0):
            k = d[col].where(d[col].notna(), None)
            g = d.assign(_k=k).dropna(subset=["_k"]).groupby(["_k", "tarih"]).res.agg(["sum", "count"]).reset_index().sort_values(["_k", "tarih"])
            g["cs"] = g.groupby("_k")["sum"].cumsum() - g["sum"]; g["cn"] = g.groupby("_k")["count"].cumsum() - g["count"]; g["v"] = g.cs / (g.cn + shrink)
            return d[["tarih"]].assign(_k=k).merge(g[["_k", "tarih", "v"]], on=["_k", "tarih"], how="left")["v"].fillna(0.0).values
        S = []
        for col, name in (("annebaba", "e_fm"), ("babababa", "e_ff"), ("yetistirici", "e_br"), ("sahip", "e_ow"), ("k_baba_mb", "e_bmb"), ("k_baba_pist", "e_bpist")):
            d[name] = enc(col); S.append(name)
        yr = (pd.to_datetime(d.tarih) - pd.to_datetime(d.dogum, unit="s")).dt.days / 365.25; yas = pd.to_numeric(d.yas, errors="coerce")
        d["age_g"] = yr.fillna(yr.median()); d["age_g3"] = d.age_g * (yas <= 3).astype(float); d["age_gf"] = (d.age_g - d.age_g.round()) * (yas <= 3).astype(float)
        S += ["age_g", "age_g3", "age_gf"]
        key = [d.tarih, d.hipodrom, d.kosu]
        for c in S:
            d[c] = d[c] - d.groupby(key)[c].transform("mean")
    return d.sort_values("_i").drop(columns=["_i"]).reset_index(drop=True)


def ozellik_ekle(d, V=None, A=None):
    """d (hazirla + MS + Elo; geçmiş + bugün) → aynı satır sırasıyla EK sütunları eklenmiş kopya."""
    V = _video() if V is None else V; A = _ayoz() if A is None else A
    d = d.reset_index(drop=True).copy()
    for g in ("OV", "V2", "SYG"):
        x = _grup(d, g, V, A); assert len(x) == len(d) and (x.no.values == d.no.values).all(), g
        for c in OZ[g]:
            d[c] = x[c].values
    return d


# ---------- puan ----------
def zk(d, c):
    """Benter-K özelliklerinin doğrusal kısmı (f_lp2 HARİÇ; o AGF'den eklenir) ve δ katkısı P·δ (standartlaştırılmış)."""
    fe = c["featJ"]; mu = np.array(c["muJ"]); sd = np.array(c["sdJ"]); w = np.array(c["wJ"])
    keep = [i for i, f in enumerate(fe) if f != "f_lp2"]
    X = np.nan_to_num(d[[fe[i] for i in keep]].values.astype(float))
    lin = ((X - mu[keep]) / sd[keep]) @ w[keep]
    ip = [fe.index(f) for f in c["PF"]]; P = (np.nan_to_num(d[c["PF"]].values.astype(float)) - mu[ip]) / sd[ip]
    return lin, P @ np.array(c["delta"])


def doldur(obj):
    """Başlamamış koşulara zk6 (Benter-K tam puanı, AGF ile; alfa·log p hariç) yazar; obj'ye w0_k, a_k. Hata olursa sessizce geçer."""
    try:
        c = yukle()
        if not c:
            return
        from . import g1v3 as _V3
        t = dt.date.fromisoformat(obj["tarih"]); obj["w0_k"] = c["alfa"]; obj["a_k"] = [round(x, 4) for x in c["gam"]]
        for h in obj["hipodromlar"]:
            for k in h["kosular"]:
                if k.get("sonuc") or not k.get("atlar"):
                    continue
                at = [a for a in k["atlar"] if a.get("agf") and not a.get("kosmaz")]
                if len(at) < 5 or any(a.get("zk") is None for a in at):
                    continue
                zz = _V3.z6([{**a, "zj": a["zk"]} for a in k["atlar"]], t, c)
                if zz:
                    for a in k["atlar"]:
                        if a["no"] in zz:
                            a["zk6"] = round(zz[a["no"]], 4)
    except Exception as e:
        print("Benter-K doldurma hatası:", repr(e))


# ---------- eğitim ----------
def _steps2(s, sp, gam, nstep=5):
    N = len(s); idx = np.arange(N); mask = s > -1e8; L = 0.0; ds = np.zeros_like(s); dsp = np.zeros_like(s); dg = np.zeros(nstep - 1)
    for j in range(nstep):
        b = s if j == 0 else sp; g = 1.0 if j == 0 else gam[j]
        z = np.where(mask, g * b, -1e30); z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
        L += -np.log(p[idx, j] + 1e-12).sum(); d = p.copy(); d[idx, j] -= 1
        if j == 0:
            ds += d
        else:
            ds += g * d; dsp += g * d; dg[j - 1] = (d * np.where(mask, b, 0)).sum()
        mask[idx, j] = False
    return L, ds, dsp, dg


def egit(l2=30.0, lj=50.0, adim=5, bas_galop="2026-02-01", l2g=20.0, d=None):
    """g1v3.egit ile aynı veri/hedef + EK özellikler + sıraya özgü δ. Katsayılar → data/analiz/g1k_katsayi.json."""
    from . import golge as GL
    from .ozellik import hazirla
    from .calistir import yukle_model
    from . import elo as EL
    M = yukle_model(); FEAT = M["feat"] + GL.EK + GL.LPEK
    if d is None:
        d = GL.MS.ekle(hazirla(GL._oku("temiz"), GL._oku("program"), M)); d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
        d = EL.ekle(d)
    d = ozellik_ekle(d); FEAT = FEAT + EL.EXTRA_FEAT + EK; NJ = len(FEAT); ip = [FEAT.index(f) for f in PF]; K = len(ip)
    JD = {}
    for key, g in d.groupby(["tarih", "hipodrom", "kosu"], sort=False):
        JD[key] = (g.no.astype(int).values, np.nan_to_num(g[FEAT].values.astype(float)))
    Kk = {}
    for r in G._satirlar():
        Kk.setdefault((r["tarih"], r["hipodrom"], int(r["kosu"])), []).append(r)
    H, J, AJ = {}, {}, {}; R = []
    for key in sorted(Kk):
        ok = [r for r in Kk[key] if r["kosmadi"] != "True" and G._fl(r["ganyan"], 0) > 1 and G._fl(r["sira"], 0) > 0]
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
    msk = LM > -1e8; mu = XJ[msk].mean(0); sd = XJ[msk].std(0) + 1e-9; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0); P = Z[..., ip]

    def f(t):
        dl = t[10 + NJ + adim - 1:]
        s = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9); sp = np.where(msk, s + P @ dl, -1e9)
        L, ds, dsp, dg = _steps2(s, sp, np.r_[1.0, t[10 + NJ:10 + NJ + adim - 1]], adim)
        g = np.r_[(ds * LM.clip(-50, 0)).sum(), np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], np.einsum("nm,nmk->k", ds, Z) + 2 * lj * t[10:10 + NJ], dg,
                  np.einsum("nm,nmk->k", dsp, P) + 2 * lj * dl]
        return L + l2 * (t[1:10] @ t[1:10]) + lj * (t[10:10 + NJ] @ t[10:10 + NJ]) + lj * (dl @ dl), g
    t0 = np.zeros(10 + NJ + adim - 1 + K); t0[0] = 1; t0[10 + NJ:10 + NJ + adim - 1] = 1
    t = minimize(f, t0, jac=True, method="L-BFGS-B", options={"maxiter": 400}).x
    S0 = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9)
    out = {"alfa": float(t[0]), "b": [float(x) for x in t[1:10]], "gam": [1.0] + [float(x) for x in t[10 + NJ:10 + NJ + adim - 1]], "featJ": FEAT,
           "muJ": [float(x) for x in mu], "sdJ": [float(x) for x in sd], "wJ": [float(x) for x in t[10:10 + NJ]], "i_lp2": FEAT.index("f_lp2"),
           "PF": PF, "delta": [float(x) for x in t[10 + NJ + adim - 1:]], "n_kosu": N, "egitim": dt.date.today().isoformat(), "model": "Benter-K (T155 gölge)"}
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


if __name__ == "__main__":
    o = egit(); print("Benter-K eğitildi:", o["n_kosu"], "koşu; δ", [round(x, 3) for x in o["delta"]], "; galop", bool(o.get("galop")))
