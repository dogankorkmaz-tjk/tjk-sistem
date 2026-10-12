"""Uzman (sıralı-aşama) model deneyi: her aşama (1..5. sıra) için ayrı koşullu logit.
Aşama k: koşuda 1..k-1. sırayı alan atlar çıkarılır, kalanlar arasından k. sırayı alan at hedeftir.
Karşılaştırma (2026 sınaması, eğitim <= 2025-12-31):  piyasa (Harville üstel) | Jason-kazanma + Harville üstel | Uzman (aşamaya özel).
Ölçü: aşama başına koşu başına koşullu log-olasılık kazancı (nat), piyasa üstel taban çizgisine göre."""
import os, sys, json
import numpy as np, pandas as pd
from . import golge as G, ortak as O, mesafe as MS
from .ozellik import hazirla

G_P = [1, 0.87, 0.74, 0.74, 0.74]
G_M = [1, 0.80, 0.69, 0.69, 0.69]
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def veri():
    from .calistir import yukle_model
    M = yukle_model()
    d = MS.ekle(hazirla(G._oku("temiz"), G._oku("program"), M))
    d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
    return d, M


def asama_verisi(d, k):
    """k. aşama: 1..k-1. sıradakiler çıkarılır; hedef = k. sıra."""
    x = d[d.sira.notna() & d.lp.notna()].copy()
    x = x[x.sira >= k]
    x["kazandi"] = (x.sira == k).astype(int)
    n = x.groupby(O.K).kazandi.transform("sum")
    return x[n == 1]


def skorla(x, feat, th, mu, sd):
    X = ((x[feat] - mu) / sd).values
    return th[0] * x.lp.values + X @ th[1:]


def kosul_ll(x, s):
    """Her koşu için hedef atın koşullu log-olasılığı (softmax)."""
    x = x.assign(_s=s)
    m = x.groupby(O.K)._s.transform("max"); e = np.exp(x._s - m)
    z = e.groupby([x[c] for c in O.K]).transform("sum")
    p = e / z
    return np.log(p[x.kazandi == 1].values), x[x.kazandi == 1].index


def deney(bolum="2025-12-31", asamalar=(1, 2, 3, 4, 5)):
    d, M = veri()
    feat0 = list(M["feat"]); feat1 = feat0 + G.EK + G.LPEK
    out = {}
    egit = d[d.tarih <= bolum]; sinav = d[d.tarih > bolum]
    # Jason-kazanma modeli (aşama 1) — Harville üstel ile 2..5'e taşınır
    xtr1 = asama_verisi(egit, 1)
    th1, mu1, sd1, _ = G._fit(xtr1, feat1, M.get("lam", 100.0))
    for k in asamalar:
        xtr = asama_verisi(egit, k); xte = asama_verisi(sinav, k)
        if len(xte) == 0:
            continue
        # taban: piyasa lp'sinin üstel ağırlığı
        s_p = G_P[k - 1] * xte.lp.values
        ll_p, ix = kosul_ll(xte, s_p)
        # Jason-kazanma + üstel
        s_j = G_M[k - 1] * skorla(xte, feat1, th1, mu1, sd1)
        ll_j, _ = kosul_ll(xte, s_j)
        # Uzman: aşamaya özel model
        th, mu, sd, nk = G._fit(xtr, feat1, M.get("lam", 100.0))
        s_u = skorla(xte, feat1, th, mu, sd)
        ll_u, _ = kosul_ll(xte, s_u)
        def ozet(a):
            g = a - ll_p
            return {"kazanc": round(float(g.mean()), 4), "se": round(float(g.std(ddof=1) / np.sqrt(len(g))), 4)}
        out[k] = {"koşu": int(len(ll_p)), "jason_us": ozet(ll_j), "uzman": ozet(ll_u),
                  "uzman_eksi_jason": {"kazanc": round(float((ll_u - ll_j).mean()), 4), "se": round(float((ll_u - ll_j).std(ddof=1) / np.sqrt(len(ll_u))), 4)},
                  "w0": round(float(th[0]), 3), "egitim_koşu": nk}
        print(k, out[k], flush=True)
    return out


if __name__ == "__main__":
    r = deney()
    json.dump(r, open(os.path.join(KOK, "data", "analiz", "deney_uzman.json"), "w"), ensure_ascii=False, indent=1)


def _ornekle(S, N, rng):
    """S: (5, n) aşama skorları. Aşama k'da kalanlar arasından softmax(S[k]) ile çek; ilk-2/3/5 üyelik sayıları döner."""
    n = S.shape[1]; cnt = np.zeros((3, n)); Ks = (2, 3, 5)
    E = np.exp(S - S.max(axis=1, keepdims=True))
    for _ in range(N):
        kal = np.ones(n, bool)
        for pos in range(5):
            w = np.where(kal, E[pos], 0.0); j = rng.choice(n, p=w / w.sum()); kal[j] = False
            for q, kk in enumerate(Ks):
                if pos < kk: cnt[q, j] += 1
    return cnt / N


def kume_deneyi(bolum="2025-12-31", N=300, maks_kosu=2500):
    d, M = veri()
    feat0 = list(M["feat"]); feat1 = feat0 + G.EK + G.LPEK
    egit = d[d.tarih <= bolum]; sinav = d[(d.tarih > bolum) & d.sira.notna() & d.lp.notna()].copy()
    th1, mu1, sd1, _ = G._fit(asama_verisi(egit, 1), feat1, M.get("lam", 100.0))
    uz = [G._fit(asama_verisi(egit, k), feat1, M.get("lam", 100.0)) for k in range(1, 6)]
    sinav["sj"] = skorla(sinav, feat1, th1, mu1, sd1)
    for k in range(5):
        th, mu, sd, _ = uz[k]; sinav[f"su{k}"] = skorla(sinav, feat1, th, mu, sd)
    rng = np.random.default_rng(11); acc = {m: {k: [0, 0, 0] for k in (2, 3, 5)} for m in ("Piyasa", "Jason", "Uzman")}
    gruplar = [g for _, g in sinav.groupby(O.K) if len(g) >= 6]
    if maks_kosu and len(gruplar) > maks_kosu:
        gruplar = [gruplar[i] for i in rng.choice(len(gruplar), maks_kosu, replace=False)]
    for g in gruplar:
        sira = g.sira.values
        S = {"Piyasa": np.array([G_P[k] * g.lp.values for k in range(5)]),
             "Jason": np.array([G_M[k] * g.sj.values for k in range(5)]),
             "Uzman": np.array([g[f"su{k}"].values for k in range(5)])}
        for m, s in S.items():
            c = _ornekle(s, N, rng)
            for q, kk in enumerate((2, 3, 5)):
                sec = np.argsort(-c[q])[:kk]; hit = int((sira[sec] <= kk).sum())
                a = acc[m][kk]; a[0] += hit; a[1] += 1; a[2] += int(hit == kk)
    out = {}
    for kk in (2, 3, 5):
        out[kk] = {m: {"koşu": acc[m][kk][1], "ort_isabet": round(acc[m][kk][0] / acc[m][kk][1], 3), "tam_oran": round(acc[m][kk][2] / acc[m][kk][1], 3)} for m in acc}
        print(kk, out[kk], flush=True)
    return out


ESIK = {"SIRALI İKİLİ": 0.00306, "İKİLİ": 0.00596, "ÜÇLÜ BAHİS": 0.00141}
BIRIM = {"SIRALI İKİLİ": 1.0, "İKİLİ": 1.0, "ÜÇLÜ BAHİS": 2.0}


def _kombo_olas(S):
    """S: (3,n) aşama skorları -> (ordered pair P[i,j], ordered triple P[i,j,k])."""
    E = np.exp(S - S.max(axis=1, keepdims=True)); n = E.shape[1]
    P1 = E[0] / E[0].sum()
    P2 = E[1][None, :] / (E[1].sum() - E[1][:, None]); P2[np.arange(n), np.arange(n)] = 0
    P12 = P1[:, None] * P2
    den = E[2].sum() - E[2][:, None] - E[2][None, :]
    P3 = (E[2][None, None, :] / np.maximum(den[:, :, None], 1e-12))
    idx = np.arange(n); P3[idx, idx, :] = 0; P3[idx, :, idx] = 0; P3[:, idx, idx] = 0
    return P12, P12[:, :, None] * P3


def egzotik_geri_donus(bolum="2025-12-31", oran=1.15, maks_kosu=None):
    d, M = veri()
    feat1 = list(M["feat"]) + G.EK + G.LPEK
    egit = d[d.tarih <= bolum]; sinav = d[(d.tarih > bolum) & d.sira.notna() & d.lp.notna()].copy()
    th1, mu1, sd1, _ = G._fit(asama_verisi(egit, 1), feat1, M.get("lam", 100.0))
    uz = [G._fit(asama_verisi(egit, k), feat1, M.get("lam", 100.0)) for k in range(1, 4)]
    sinav["sj"] = skorla(sinav, feat1, th1, mu1, sd1)
    for k in range(3):
        th, mu, sd, _ = uz[k]; sinav[f"su{k}"] = skorla(sinav, feat1, th, mu, sd)
    import glob as gl
    od = pd.concat([pd.read_csv(f) for f in sorted(gl.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))], ignore_index=True)
    od = od[od.tur.isin(ESIK) & (od.tarih > bolum)]
    ok = {(r.tarih, r.hipodrom, r.kosu, r.tur): (r.kombo, float(r.tutar)) for r in od.itertuples()}
    acc = {m: {t: {"koşu": 0, "kombo": 0, "harcama": 0.0, "kazanc": 0.0, "isabet": 0} for t in ESIK} for m in ("Jason", "Uzman")}
    n_k = 0
    for key, g in sinav.groupby(O.K):
        if len(g) < 4: continue
        tarih, hip, kosu = key
        if not any((tarih, hip, kosu, t) in ok for t in ESIK): continue
        n_k += 1
        no = g.no.astype(int).astype(str).values
        Sp = np.array([G_P[k] * g.lp.values for k in range(3)])
        Sm = {"Jason": np.array([G_M[k] * g.sj.values for k in range(3)]), "Uzman": np.array([g[f"su{k}"].values for k in range(3)])}
        P12p, P123p = _kombo_olas(Sp)
        for m, S in Sm.items():
            P12, P123 = _kombo_olas(S)
            for tur in ESIK:
                if (tarih, hip, kosu, tur) not in ok: continue
                if tur == "ÜÇLÜ BAHİS":
                    pm_, pp_ = P123, P123p
                elif tur == "SIRALI İKİLİ":
                    pm_, pp_ = P12, P12p
                else:
                    pm_, pp_ = P12 + P12.T, P12p + P12p.T
                msk = (pp_ >= ESIK[tur]) & (pm_ / np.maximum(pp_, 1e-12) >= oran)
                if tur == "İKİLİ":
                    msk = np.triu(msk, 1)
                sec = np.argwhere(msk)
                if len(sec) == 0: continue
                kombo, tutar = ok[(tarih, hip, kosu, tur)]
                parca = kombo.split("/")
                gizli = "/".join(no[list(c)] for c in sec[:0]) if False else None
                kaz = 0.0; hit = False
                for c in sec:
                    ad = [no[i] for i in c]
                    if tur == "İKİLİ":
                        hit_c = sorted(ad) == sorted(parca)
                    else:
                        hit_c = ad == parca
                    if hit_c:
                        kaz += tutar; hit = True
                a = acc[m][tur]; a["koşu"] += 1; a["kombo"] += len(sec); a["harcama"] += len(sec) * BIRIM[tur]; a["kazanc"] += kaz; a["isabet"] += int(hit)
        if maks_kosu and n_k >= maks_kosu: break
    out = {"koşu": n_k, "oran": oran}
    for m in acc:
        out[m] = {t: {**a, "geri_donus": round(a["kazanc"] / a["harcama"], 3) if a["harcama"] else None, "harcama": round(a["harcama"], 1), "kazanc": round(a["kazanc"], 1)} for t, a in acc[m].items()}
    print(json.dumps(out, ensure_ascii=False, indent=1), flush=True)
    return out
