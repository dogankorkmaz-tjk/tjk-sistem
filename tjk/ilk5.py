"""İlk-5 gölge katman v2 (ön-kayıt: data/analiz/hipotez_defteri.md, 25 Ekim 2026): D + dinlenme + Jason ek özellikleri, sıraya özel katsayı.
Üretimdeki kuponlara/olasılıklara DOKUNMAZ; yalnız sabah x5 özelliklerini yazar ve biten koşularda mevcut (G1-S) ile yeni sıra olasılıklarını log-olabilirlikle karşılaştırır.
Katsayılar: data/analiz/ilk5_katsayilar_v2.json (dondurulmuş). Çıktı: docs/data/ilk5_golge.json"""
import os, json, glob, math
import numpy as np
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(KOK, "docs", "data")
BASLA = "2026-10-25"
_K = json.load(open(os.path.join(KOK, "data", "analiz", "ilk5_katsayilar_v2.json"), encoding="utf-8"))
TH = np.array(_K["th"]); MS = _K["ek_mu_sd"]


def ozellik(d2, temiz, tarih):
    """d2: hazirla+MS.ekle çıktısı (yeni satırlar). Dönen: {(hipodrom,kosu,no): [f_dp150_m, f_jgen100, f_fig3, dinlenme_gün(-1=ilk)]} (ham)."""
    son = temiz.dropna(subset=["at"]).groupby("at").tarih.max()
    t0 = pd.Timestamp(str(tarih)[:10]); o = {}
    for r in d2[d2.yeni].itertuples():
        s = son.get(r.at); gun = -1 if s is None or pd.isna(s) else (t0 - pd.Timestamp(str(s)[:10])).days
        o[(r.hipodrom, int(r.kosu), int(r.no))] = [round(float(getattr(r, c)), 5) if pd.notna(getattr(r, c)) else 0.0 for c in ("f_dp150_m", "f_jgen100", "f_fig3")] + [int(gun)]
    return o


def _x(a, lj, lm):
    dp, jg, fg, gun = a["x5"]
    ilk = 1.0 if gun < 0 else 0.0; rest = math.log1p(min(max(gun, 7), 150)) if gun >= 0 else math.log1p(30)
    z = lambda v, k: (v - MS[k][0]) / MS[k][1]
    return [lj, lm, rest, ilk, z(dp, "f_dp150_m"), z(jg, "f_jgen100"), z(fg, "f_fig3")]


def _nll_sira(S, sira_idx):
    """S: (5,n) sıra başına skor; sira_idx: atların bitiş sırasına göre indeksleri (ilk 5). 2.–5. sıra NLL toplamı + 1. sıra."""
    kalan = list(range(S.shape[1])); out = []
    for s in range(5):
        sc = S[s][kalan]; m = sc.max(); lz = m + math.log(np.exp(sc - m).sum())
        out.append(-(S[s][sira_idx[s]] - lz)); kalan.remove(sira_idx[s])
    return out


def olc():
    """BASLA sonrası biten koşularda: Jason-Harville, mevcut G1-S (a_g1 üsleri), yeni D+ ; 2.–5. sıra NLL (nats/koşu)."""
    satir = []
    for y in sorted(glob.glob(os.path.join(SITE, "gun", "*.json"))):
        o = json.load(open(y, encoding="utf-8"))
        if o["tarih"] < BASLA or o.get("w0_aday") is None or not o.get("a_g1"):
            continue
        for h in o["hipodromlar"]:
            for k in h["kosular"]:
                s = k.get("sonuc")
                if not s: continue
                at = [a for a in k["atlar"] if str(a["no"]) in s and s[str(a["no"])].get("g") and a.get("agf") and a.get("x5") and a.get("z2") is not None and a.get("z6") is not None]
                if len(at) < 6 or len(at) != len([a for a in k["atlar"] if s.get(str(a["no"]))]): continue
                sr = [s[str(a["no"])]["sira"] for a in at]
                if sorted(sr)[:6] != [1, 2, 3, 4, 5, 6]: continue
                tot = sum(a["agf"] for a in at); pp = np.array([a["agf"] / tot for a in at]); lpp = np.log(np.maximum(pp, 1e-6))
                sj = o["w0_aday"] * lpp + o.get("lp2_aday", 0.0) * lpp ** 2 + np.array([a["z2"] for a in at]); lj = sj - sj.max(); lj = lj - np.log(np.exp(lj).sum())
                sg = o["w0_g1"] * lpp + np.array([a["z6"] for a in at]); lg = sg - sg.max(); lg = lg - np.log(np.exp(lg).sum())
                pg_ = np.array([1 / s[str(a["no"])]["g"] for a in at]); lm = np.log(pg_ / pg_.sum())
                X = np.array([_x(a, lj[i], lm[i]) for i, a in enumerate(at)])
                idx = list(np.argsort(sr)[:5])
                yeni = np.array([X @ TH[s_] for s_ in range(5)]); mev = np.array([o["a_g1"][s_] * lg for s_ in range(5)]); har = np.array([lj for _ in range(5)])
                satir.append((o["tarih"], h["id"], k["kosu"], sum(_nll_sira(har, idx)[1:]), sum(_nll_sira(mev, idx)[1:]), sum(_nll_sira(yeni, idx)[1:])))
    d = pd.DataFrame(satir, columns=["tarih", "hip", "kosu", "harville", "mevcut", "yeni"])
    out = {"not": "2.–5. sıra negatif log-olabilirlik toplamı (düşük iyi). fark = mevcut − yeni (+ yeni daha iyi). Ön-kayıt: 25 Ekim 2026.", "kosu": int(len(d))}
    if len(d):
        out["ort"] = {c: round(float(d[c].mean()), 4) for c in ("harville", "mevcut", "yeni")}
        f = d.mevcut - d.yeni; g = d.groupby("tarih"); s = pd.DataFrame({"sum": (f.groupby(d.tarih)).sum(), "n": g.size()}); rng = np.random.default_rng(1); b = []
        for _ in range(2000):
            t = s.iloc[rng.integers(0, len(s), len(s))]; b.append(t["sum"].sum() / t["n"].sum())
        out["fark"] = round(float(f.mean()), 4); out["ga"] = [round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]; out["gun"] = int(d.tarih.nunique())
    json.dump(out, open(os.path.join(SITE, "ilk5_golge.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out
