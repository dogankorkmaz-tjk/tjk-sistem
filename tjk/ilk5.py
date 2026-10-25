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
_KB = json.load(open(os.path.join(KOK, "data", "analiz", "ilk5_birlesim_katsayilar.json"), encoding="utf-8"))
_K3 = json.load(open(os.path.join(KOK, "data", "analiz", "ilk5_katsayilar_v3.json"), encoding="utf-8")); TH3 = np.array(_K3["th"])


def _asc(x):
    import unicodedata
    return unicodedata.normalize("NFKD", str(x).replace("İ", "I").replace("ı", "i")).encode("ascii", "ignore").decode().lower().strip()


def _havuz_oku(tarih):
    """data/muh/<gün>.json -> {(hipodrom_ascii, kosu): {'si':..,'ik':..}} (tjk.muhtemeller son AÇIK/KAPALI durum)"""
    yol = os.path.join(KOK, "data", "muh", tarih + ".json")
    try: D = json.load(open(yol, encoding="utf-8"))
    except Exception: return {}
    return {(_asc(v.get("hipodrom", k.rsplit("-", 1)[0])), int(v.get("kosu"))): v["havuz"] for k, v in D.items() if v.get("havuz")}


def _havuz_ozellik(at, hv):
    """at: koşu atları (sırayla); hv: {'si','ik'} -> (log s2n, log sqn) dizileri"""
    ix = {int(a["no"]): i for i, a in enumerate(at)}; n = len(at); s2 = np.zeros(n); sq = np.zeros(n)
    for a, b, G in hv["si"]: s2[ix[int(b)]] += 1 / float(G)
    for a, b, G in hv["ik"]: sq[ix[int(a)]] += 1 / float(G); sq[ix[int(b)]] += 1 / float(G)
    f = lambda v: np.log((v + 1e-3 * v.mean()) / (v + 1e-3 * v.mean()).sum())
    return f(s2), f(sq)


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


def _sm(v):
    e = np.exp(v - v.max()); return e / e.sum()


def _egz_kayip(at, X3, hv, idx):
    """sıralı ikili / ikili ilk-22: yeniden kalibre havuz (P) ve model×havuz birleşimi (C) log-kaybı. Döner {tur: [toplamP, toplamC, adet]}"""
    n = len(at); ix = {int(a["no"]): i for i, a in enumerate(at)}
    p1 = _sm(X3 @ TH3[0]); Q = np.zeros((n, n)); s2 = X3 @ TH3[1]
    for a in range(n):
        rs = [j for j in range(n) if j != a]; p2 = _sm(s2[rs])
        for k, b in enumerate(rs): Q[a, b] = p1[a] * p2[k]
    o = {}
    for tur in ("si", "ik"):
        kb = _KB[tur]; tp = tc = 0.0; m = 0
        for a, b, G in hv[tur]:
            a_, b_, G = ix[int(a)], ix[int(b)], float(G)
            if tur == "si": hit = (a_ == idx[0] and b_ == idx[1]); q3 = Q[a_, b_]
            else: hit = ({a_, b_} == {idx[0], idx[1]}); q3 = Q[a_, b_] + Q[b_, a_]
            lq = math.log(min(max((1 / G) * kb["taban"], 1e-6), 0.999)); l3 = math.log(min(max(q3, 1e-6), 0.999)); y = float(hit)
            zp = kb["P"][0] + kb["P"][1] * lq; zc = kb["C"][0] + kb["C"][1] * l3 + kb["C"][2] * lq
            tp += float(np.logaddexp(0, zp) - y * zp); tc += float(np.logaddexp(0, zc) - y * zc); m += 1
        o[tur] = [round(tp, 5), round(tc, 5), m]
    return o


def _kupon_yeni(BS, S, B):
    """S: (5,n) sıra başına skor; besli.kupon_g'yi bu sıra ağırlıklarıyla çalıştırır (_W geçici olarak değiştirilir, her durumda geri alınır)."""
    W = [list(np.exp(S[k] - S[k].max())) for k in range(5)]; T = [sum(w) for w in W]
    p = W[0] / T[0]; orig = BS._W
    BS._W = lambda p_, G=None: (W, T)
    try:
        return BS.kupon_g(list(p), B)
    finally:
        BS._W = orig


def _kupon_karsilastir(BS, o, at, lg, S, idx):
    """5'li kupon: mevcut G1-S (a_g1 üsleri) ve yeni sıra ağırlıkları, 48/96/150 geçerli kombinasyon bütçesi. Döner {B: [mevcut(pred,cost,hit), yeni(...)]}"""
    out = {}
    for B in (48, 96, 150):
        r = []
        for kp in (BS.kupon_g(list(np.exp(lg)), B, o["a_g1"]), _kupon_yeni(BS, S, B)):
            if not kp: r = None; break
            sets, pr = kp; hit = all(idx[j] in sets[j] for j in range(5))
            r.append([round(float(pr), 5), BS.gecerli_say(sets), bool(hit)])
        if r: out[str(B)] = r
    return out


def olc():
    """BASLA sonrası biten koşularda: Jason-Harville, mevcut G1-S (a_g1 üsleri), yeni D+ ; 2.–5. sıra NLL (nats/koşu)."""
    satir = []; kpy = os.path.join(KOK, "data", "ilk5", "kupon_onbellek.json"); os.makedirs(os.path.dirname(kpy), exist_ok=True)
    try: KP = json.load(open(kpy, encoding="utf-8"))
    except Exception: KP = {}
    from . import besli as BS
    for y in sorted(glob.glob(os.path.join(SITE, "gun", "*.json"))):
        o = json.load(open(y, encoding="utf-8"))
        if o["tarih"] < BASLA or o.get("w0_aday") is None or not o.get("a_g1"):
            continue
        hvz = _havuz_oku(o["tarih"])
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
                y3 = float("nan")
                hv = hvz.get((_asc(h["id"]), int(k["kosu"])))
                if hv:
                    try:
                        f2, fq = _havuz_ozellik(at, hv); X3 = np.hstack([X, f2[:, None], fq[:, None]])
                        y3 = sum(_nll_sira(np.array([X3 @ TH3[s_] for s_ in range(5)]), idx)[1:])
                    except Exception:
                        y3 = float("nan")
                kk = f'{o["tarih"]}|{h["id"]}|{k["kosu"]}'
                if kk not in KP:
                    try:
                        Sx = np.array([X3 @ TH3[s_] for s_ in range(5)]) if not np.isnan(y3) else yeni
                        KP[kk] = {"v": 3 if not np.isnan(y3) else 2, "k": _kupon_karsilastir(BS, o, at, lg, Sx, idx)}
                        if not np.isnan(y3):
                            try: KP[kk]["egz"] = _egz_kayip(at, X3, hv, idx)
                            except Exception as e2: KP[kk]["egz_hata"] = repr(e2)[:80]
                    except Exception as e:
                        KP[kk] = {"hata": repr(e)[:80]}
                satir.append((o["tarih"], h["id"], k["kosu"], sum(_nll_sira(har, idx)[1:]), sum(_nll_sira(mev, idx)[1:]), sum(_nll_sira(yeni, idx)[1:]), y3))
    d = pd.DataFrame(satir, columns=["tarih", "hip", "kosu", "harville", "mevcut", "yeni", "yeni3"])
    out = {"not": "2.–5. sıra negatif log-olabilirlik toplamı (düşük iyi). fark = mevcut − yeni (+ yeni daha iyi). Ön-kayıt: 25 Ekim 2026.", "kosu": int(len(d))}
    if len(d):
        out["ort"] = {c: round(float(d[c].mean()), 4) for c in ("harville", "mevcut", "yeni")}
        f = d.mevcut - d.yeni; g = d.groupby("tarih"); s = pd.DataFrame({"sum": (f.groupby(d.tarih)).sum(), "n": g.size()}); rng = np.random.default_rng(1); b = []
        for _ in range(2000):
            t = s.iloc[rng.integers(0, len(s), len(s))]; b.append(t["sum"].sum() / t["n"].sum())
        out["fark"] = round(float(f.mean()), 4); out["ga"] = [round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]; out["gun"] = int(d.tarih.nunique())
    json.dump(KP, open(kpy, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    kup = {}
    for kk, v in KP.items():
        for B, r in (v.get("k") or {}).items():
            a = kup.setdefault(B, {"kosu": 0, "pred": [0.0, 0.0], "isabet": [0, 0], "maliyet": [0, 0]})
            a["kosu"] += 1
            for j in (0, 1): a["pred"][j] += r[j][0]; a["isabet"][j] += int(r[j][2]); a["maliyet"][j] += r[j][1]
    out["kupon_5li"] = {B: {"kosu": a["kosu"], "mevcut": {"tutma_beklenen": round(a["pred"][0], 3), "tutan": a["isabet"][0], "ort_kombinasyon": round(a["maliyet"][0] / a["kosu"], 1)}, "yeni": {"tutma_beklenen": round(a["pred"][1], 3), "tutan": a["isabet"][1], "ort_kombinasyon": round(a["maliyet"][1] / a["kosu"], 1)}} for B, a in kup.items()}
    eg = {}
    for kk, v in KP.items():
        for tur, (tp, tc, m) in (v.get("egz") or {}).items():
            a = eg.setdefault(tur, {"gun": {}, "kosu": 0, "bahis": 0})
            g_ = a["gun"].setdefault(kk.split("|")[0], [0.0, 0.0, 0]); g_[0] += tp; g_[1] += tc; g_[2] += m; a["kosu"] += 1; a["bahis"] += m
    out["egz"] = {}
    for tur, a in eg.items():
        sm_ = pd.DataFrame(a["gun"], index=["P", "C", "n"]).T; rng = np.random.default_rng(3); b = []
        for _ in range(2000):
            t = sm_.iloc[rng.integers(0, len(sm_), len(sm_))]; b.append((t.P.sum() - t.C.sum()) / t.n.sum())
        out["egz"][tur] = {"kosu": a["kosu"], "bahis": a["bahis"], "kayip_P": round(float(sm_.P.sum() / sm_.n.sum()), 5), "kayip_C": round(float(sm_.C.sum() / sm_.n.sum()), 5),
                           "fark_P_eksi_C": round(float((sm_.P.sum() - sm_.C.sum()) / sm_.n.sum()), 6), "ga": [round(float(np.percentile(b, 2.5)), 6), round(float(np.percentile(b, 97.5)), 6)]}
    d3 = d.dropna(subset=["yeni3"])
    if len(d3):
        out["v3"] = {"kosu": int(len(d3)), "ort": {c: round(float(d3[c].mean()), 4) for c in ("mevcut", "yeni", "yeni3")}}
        for ad, a_, b_ in (("fark3_mevcut", d3.mevcut, d3.yeni3), ("fark3_v2", d3.yeni, d3.yeni3)):
            f = a_ - b_; ss = pd.DataFrame({"sum": f.groupby(d3.tarih).sum(), "n": d3.groupby("tarih").size()}); rng = np.random.default_rng(2); b = []
            for _ in range(2000):
                t = ss.iloc[rng.integers(0, len(ss), len(ss))]; b.append(t["sum"].sum() / t["n"].sum())
            out["v3"][ad] = [round(float(f.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
    json.dump(out, open(os.path.join(SITE, "ilk5_golge.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out
