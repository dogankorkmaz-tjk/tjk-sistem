"""T168 (ön kayıt hipotez_defteri 2026-11-07): kapanış öncesi görülen fiyatla ikili/sıralı ikili ve ganyan değer bahsi."""
import json, glob, pickle, numpy as np, pandas as pd
rng = np.random.default_rng(168); A0 = 0.715
HMAP = {"DBAKIR": "diyarbakir", "SANLIURFA": "sanliurfa", "ELAZIG": "elazig", "ISTANBUL": "istanbul", "IZMIR": "izmir"}
c = pickle.load(open("/tmp/claude-0/cache_MJ_2026-10.pkl", "rb")); C = {tuple(k): i for i, k in enumerate(c["keys"])}
OD = pd.read_csv("data/odeme/2026-10.csv.gz"); ODM = {}
for r in OD[OD.tur.isin(["İKİLİ", "SIRALI İKİLİ"])].itertuples():
    ODM[(r.tarih, r.hipodrom, int(r.kosu), "ik" if r.tur == "İKİLİ" else "si")] = (str(r.kombo), float(r.tutar))
T = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "ganyan", "kosmadi"]) for f in sorted(glob.glob("data/temiz/2026-10*.csv.gz"))])
GN = {(r.tarih, r.hipodrom, int(r.kosu), int(r.no)): float(r.ganyan) for r in T.itertuples() if r.ganyan == r.ganyan and r.kosmadi != True}
def boot(df, col_r, col_m="m"):
    g = df.groupby("gun").agg(r=(col_r, "sum"), m=(col_m, "sum")); ug = g.index.values
    if not len(ug): return np.nan, (np.nan, np.nan)
    bs = [ (lambda s: g.r[s].sum() / g.m[s].sum() - 1)(rng.choice(ug, len(ug))) for _ in range(3000)]
    return g.r.sum() / g.m.sum() - 1, tuple(np.percentile(bs, [2.5, 97.5]))
def pre_p(i, gpre):
    nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n].copy(); l0 = c["L0"][i][:n]
    g = np.array([gpre.get(str(x), np.nan) for x in nos])
    if np.isnan(g).any() or (g <= 1).any(): return None, None, nos
    lp = np.log(1 / g); lp -= np.log(np.exp(lp).sum()); s = s + A0 * (lp - l0)
    p = np.exp(s - s.max()); p /= p.sum(); return p, g, nos
AK, GK, KAY = [], [], []
for f in sorted(glob.glob("data/muh/2026-10-*.json")):
    gun = f[-15:-5]
    for k, v in json.load(open(f)).items():
        h = HMAP.get(v.get("hipodrom"), str(v.get("hipodrom")).lower()); key = (gun, h, int(v["kosu"])); i = C.get(key)
        if i is None: continue
        an = [a for a in v.get("anlik", []) if a.get("durum") == "AÇIK" and a.get("dk") is not None]
        # B) ganyan
        b = [a for a in an if 1 <= a["dk"] <= 5]
        if b:
            p, g, nos = pre_p(i, b[-1]["g"])
            gf = np.array([GN.get((gun, h, key[2], x), np.nan) for x in nos])
            if p is not None and not np.isnan(gf).any():
                n = len(nos); s = c["S3"][i][:n]; pc = np.exp(s - s.max()); pc /= pc.sum()
                ev = p * g; j = int(np.argmax(ev)); evc = pc * gf; jc = int(np.argmax(evc))
                GK.append(dict(gun=gun, dk=b[-1]["dk"], once=g[0], son=gf[0],
                               sec=int(ev[j] >= 1.2), r_gercek=(gf[j] if j == 0 else 0.0) * (ev[j] >= 1.2), r_sanilan=(g[j] if j == 0 else 0.0) * (ev[j] >= 1.2),
                               secc=int(evc[jc] >= 1.2), r_kap=(gf[jc] if jc == 0 else 0.0) * (evc[jc] >= 1.2)))
        # A) ikili
        hv = v.get("havuz")
        if not hv or hv.get("durum") != "AÇIK" or not (0 <= (hv.get("dk") or -1) <= 10): continue
        sn = min(an, key=lambda a: abs(a["dk"] - hv["dk"])) if an else None
        if sn is None: continue
        p, g, nos = pre_p(i, sn["g"])
        if p is None: continue
        gg = c["g3"]; w2 = np.power(p, gg[1]); kaz = (nos[0], nos[1])
        def sp(a, b_):
            if a not in nos or b_ not in nos or a == b_: return None
            ia, ib = nos.index(a), nos.index(b_); return p[ia] * w2[ib] / (w2.sum() - w2[ia])
        for tur in ("si", "ik"):
            od = ODM.get((gun, h, key[2], tur))
            if od is None: continue
            for x in hv.get(tur) or []:
                try: a, b_, o = int(x[0]), int(x[1]), float(str(x[2]).replace(",", "."))
                except Exception: continue
                if tur == "si": pr = sp(a, b_); hit = (a, b_) == kaz
                else:
                    pa, pb = sp(a, b_), sp(b_, a); pr = None if pa is None else pa + pb; hit = {a, b_} == set(kaz)
                if pr is None or o <= 1: continue
                if hit: AK.append(dict(gun=gun, tur=tur, once=o, son=od[1]))
                if pr * o >= 1.2: KAY.append(dict(gun=gun, tur=tur, m=1.0, r_sanilan=o * hit, r_gercek=od[1] * hit, hit=int(hit), key=key))
A = pd.DataFrame(AK); K = pd.DataFrame(KAY); G = pd.DataFrame(GK)
print("=== A) İKİLİ / SIRALI İKİLİ (havuz AÇIK, koşuya 0–10 dk)")
for tur, ad in (("si", "sıralı ikili"), ("ik", "ikili")):
    a = A[A.tur == tur] if len(A) else A
    if len(a): print(f"{ad}: kazanan kombinasyon listede {len(a)} koşu | resmî ödeme / önce oranı medyan {np.median(a.son / a.once):.3f} (çeyrekler {np.percentile(a.son / a.once, 25):.3f}–{np.percentile(a.son / a.once, 75):.3f})")
    k = K[K.tur == tur] if len(K) else K
    if len(k):
        r1, ci1 = boot(k, "r_sanilan"); r2, ci2 = boot(k, "r_gercek")
        print(f"   değer bahisleri: {len(k)} bahis, {k.key.nunique()} koşu, {k.gun.nunique()} gün, {k.hit.sum()} isabet | önce oranıyla SANILAN ROI {r1:+.3f} [{ci1[0]:+.3f}; {ci1[1]:+.3f}] | resmî ödemeyle GERÇEK ROI {r2:+.3f} [{ci2[0]:+.3f}; {ci2[1]:+.3f}] | fark {r2 - r1:+.3f}")
print("=== B) GANYAN (koşuya 1–5 dk kalan son anlık)")
print(f"koşu {len(G)}, gün {G.gun.nunique()}, ort. dk {G.dk.mean():.1f} | kazananın resmî ganyan / önce oranı medyan {np.median(G.son / G.once):.3f} (çeyrekler {np.percentile(G.son / G.once, 25):.3f}–{np.percentile(G.son / G.once, 75):.3f})")
g1 = G[G.sec == 1].assign(m=1.0); g2 = G[G.secc == 1].assign(m=1.0)
r1, c1 = boot(g1, "r_sanilan"); r2, c2 = boot(g1, "r_gercek"); r3, c3 = boot(g2, "r_kap")
print(f"önce fiyatıyla seçim: {len(g1)} bahis, {int((g1.r_gercek > 0).sum())} isabet | SANILAN ROI {r1:+.3f} [{c1[0]:+.3f}; {c1[1]:+.3f}] | GERÇEK ROI {r2:+.3f} [{c2[0]:+.3f}; {c2[1]:+.3f}]")
print(f"kapanış fiyatıyla seçim (T159 kuralı, aynı koşular): {len(g2)} bahis, {int((g2.r_kap > 0).sum())} isabet | ROI {r3:+.3f} [{c3[0]:+.3f}; {c3[1]:+.3f}]")
