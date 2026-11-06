"""T156 (ön kayıt: hipotez_defteri 2026-11-06 20:45): beklenen kazanca (EV) göre sıralı 5'li kupon.
A = üretim kurucusu kupon_g (tutma), B = EV-doldur, C = EV-değer (yalnız pozitif marjinal EV; değilse oynamaz).
Çıktı: /tmp/claude-0/t156_kayit.pkl (koşu × strateji × bütçe: maliyet, getiri, isabet) → t156_rapor.py."""
import sys, os, glob, pickle, math, itertools
import numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import besli as BS

rng = np.random.default_rng(156); BIRIM = BS.BIRIM; BUTCE = (48, 96, 150)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]

OD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202*.csv.gz"))])
OD = OD[OD.tur.str.contains("SIRALI 5")]
ODM = {}
for r in OD.itertuples():
    try: seq = tuple(int(x) for x in str(r.kombo).split("/"))
    except Exception: continue
    if len(seq) != 5: continue
    k = (r.tarih, r.hipodrom, int(r.kosu)); dv = "DEVİR" in r.tur
    o = ODM.setdefault(k, {"seq": seq, "tutar": 0.0, "devir": dv, "devir_tutar": 0.0})
    if dv: o["devir_tutar"] = max(o["devir_tutar"], float(r.tutar))
    else: o["tutar"] = max(o["tutar"], float(r.tutar)); o["devir"] = False


def perm_tablo(p, pm, gam, aday):
    """Adaylardan sıralı 5'li permütasyonlar; model PL (üs gam) ve piyasa Harville (G_P) olasılıkları, tüm alana göre normalize."""
    P = np.array(list(itertools.permutations(aday, 5)))
    def pl(w_all, G):
        out = np.ones(len(P)); used = np.zeros(len(P))
        for k in range(5):
            wk = np.power(np.maximum(w_all, 1e-12), G[k]); T = wk.sum()
            num = wk[P[:, k]]; den = T - sum(wk[P[:, j]] for j in range(k)) if k else np.full(len(P), T)
            out *= num / den
        return out
    return P, pl(np.array(p), gam), pl(np.array(pm), BS.G_P)


def ev_ve_tutma(P, pmod, oh, sets):
    m = np.ones(len(P), bool)
    for k in range(5):
        m &= np.isin(P[:, k], sets[k])
    return (pmod[m] * oh[m]).sum(), pmod[m].sum()


def ev_kur(P, pmod, oh, B, t, deger):
    bas = [[[t[0]], [t[1]], [t[2]], [t[3]], [t[4]]],
           [[t[0], t[1]], [t[0], t[1]], [t[2]], [t[3]], [t[4]]],
           [[t[0], t[1]], [t[0], t[1]], [t[2], t[3]], [t[2], t[3]], [t[4]]]]
    en = None
    for st in bas:
        nv = BS.gecerli_say(st)
        if not (0 < nv <= B): continue
        sets = [list(x) for x in st]; ev, _ = ev_ve_tutma(P, pmod, oh, sets)
        if deger and ev < BIRIM * nv: continue
        for _ in range(80):
            best = None; bg = -1e18
            for k in range(5):
                for h in t[:9]:
                    if h in sets[k]: continue
                    sets[k].append(h); v2 = BS.gecerli_say(sets)
                    if v2 > B or v2 <= nv: sets[k].pop(); continue
                    e2, _ = ev_ve_tutma(P, pmod, oh, sets); sets[k].pop()
                    g = (e2 - ev) / (v2 - nv)
                    if g > bg: bg, best = g, (k, h, e2, v2)
            if not best or (deger and bg < BIRIM): break
            sets[best[0]].append(best[1]); ev, nv = best[2], best[3]
        net = ev - BIRIM * nv
        if en is None or net > en[0]: en = (net, [list(x) for x in sets], nv)
    return en


def odeme_modeli(X):
    X = np.array(X); b, a = np.polyfit(X[:, 0], X[:, 1], 1); s2 = (X[:, 1] - a - b * X[:, 0]).var(); return a, b, s2


KAYIT = []; EGIT = []
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    model = odeme_modeli(EGIT) if len(EGIT) >= 80 else None
    yeni = []
    for i, key in enumerate(c["keys"]):
        key = (key[0], key[1], int(key[2])); od = ODM.get(key)
        if od is None: continue
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; lm = c["L0"][i][:n]
        if n < 6 or not all(x in nos for x in od["seq"]): continue
        perm = rng.permutation(n); nos = [nos[j] for j in perm]; s = s[perm]; lm = lm[perm]   # bitiriş sırası sızmasın
        p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        ix = [nos.index(x) for x in od["seq"]]
        # ödeme modeli eğitimi verisi (yalnız bilen olan koşular)
        Wp, Tp = BS._W(list(pm), BS.G_P); pkaz = BS._prob(Wp, Tp, [[j] for j in ix])
        if not od["devir"] and od["tutar"] > 0: yeni.append((math.log(1 / max(pkaz, 1e-12)), math.log(od["tutar"])))
        if model is None: continue
        a, b, s2 = model; gam = list(c["g3"])
        t = sorted(range(n), key=lambda j: -p[j]); aday = t[:min(n, 9)]
        P, pmod, pmk = perm_tablo(p, pm, gam, aday); oh = np.exp(a + b * np.log(1 / np.maximum(pmk, 1e-12)) + s2 / 2)
        kaz = tuple(ix); getiri = od["tutar"] if not od["devir"] else 0.0; getiri_dv = od["tutar"] if not od["devir"] else od["devir_tutar"]
        for B in BUTCE:
            kp = BS.kupon_g(list(p), B, gam)
            for ad, sets in (("A", kp[0] if kp else None), ("B", (ev_kur(P, pmod, oh, B, t, False) or (0, None, 0))[1]),
                             ("C", (ev_kur(P, pmod, oh, B, t, True) or (0, None, 0))[1])):
                if not sets:
                    KAYIT.append(dict(gun=key[0], key=key, ay=ay, B=B, s=ad, maliyet=0.0, getiri=0.0, getiri_dv=0.0, isabet=0, oyna=0)); continue
                v = BS.gecerli_say(sets); hit = all(kaz[k] in sets[k] for k in range(5))
                ev, tut = ev_ve_tutma(P, pmod, oh, sets)
                KAYIT.append(dict(gun=key[0], key=key, ay=ay, B=B, s=ad, maliyet=v * BIRIM, getiri=getiri * hit, getiri_dv=getiri_dv * hit, isabet=int(hit), oyna=1, ev=ev, tutma=tut))
    EGIT += yeni
    print(ay, "ödeme modeli", None if model is None else tuple(round(x, 3) for x in model), "| kayıt", len(KAYIT), flush=True)
pickle.dump(KAYIT, open("/tmp/claude-0/t156_kayit.pkl", "wb")); print("BİTTİ")
