"""Piyasa tabanı ölçümü (betimleyici, ön kayıt gerektirmez): canlı kayıtlı koşularda kazanan olasılığının log-kaybı.
Karşılaştırılanlar: kapanış ganyanı (pp), kapanış ganyanı + güç kalibrasyonu (alfa, günlere göre çapraz doğrulama), AGF, Bolton (pm), Jason (pm2), Jason-K (pm3), Jason-S (pm4).
Ortak koşu kümesi üzerinde eşleştirilmiş fark ve gün kümeli bootstrap güven aralığı. Çalıştırma: python3 data/analiz/piyasa_tabani.py"""
import json, glob, math, random, os
import numpy as np

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = []                                              # her koşu: dict(gun, p:{ad:[olasılıklar]}, w:kazanan indeksi, g:[ganyan])
for y in sorted(glob.glob(os.path.join(KOK, "docs", "data", "gun", "*.json"))):
    gun = os.path.basename(y)[:-5]; G = json.load(open(y, encoding="utf-8"))
    for h in G["hipodromlar"]:
        for k in h["kosular"]:
            s = k.get("sonuc")
            if not s:
                continue
            nos = [n for n, v in s.items() if v.get("g") and v.get("pp")]
            kz = [n for n in nos if s[n].get("sira") == 1]
            if len(kz) != 1 or len(nos) < 3:
                continue
            ag = {str(a["no"]): a.get("agf") for a in k["atlar"]}
            d = {"gun": gun, "id": f"{h['id']}|{k['kosu']}", "w": nos.index(kz[0]), "g": np.array([s[n]["g"] for n in nos]),
                 "pp": np.array([s[n]["pp"] for n in nos])}
            for ad, key in (("pm", "pm"), ("pm2", "pm2"), ("pm3", "pm3"), ("pm4", "pm4")):
                if all(s[n].get(key) for n in nos):
                    d[ad] = np.array([s[n][key] for n in nos])
            if all(ag.get(n) for n in nos):
                a = np.array([ag[n] for n in nos], float); d["agf"] = a / a.sum()
            R.append(d)
print("koşu:", len(R), "gün:", len({r['gun'] for r in R}))


def nll(p, w):
    p = np.clip(p / p.sum(), 1e-9, 1)
    return -math.log(p[w])


def guc(g, a):                                       # kesintisiz kapanış olasılığı^alfa, yeniden normalize
    q = (1.0 / g) ** a
    return q / q.sum()


def fit_alfa(rows):
    best, ba = 1e18, 1.0
    for a in np.arange(0.70, 1.31, 0.02):
        t = sum(nll(guc(r["g"], a), r["w"]) for r in rows)
        if t < best:
            best, ba = t, a
    return ba


gunler = sorted({r["gun"] for r in R}); random.seed(7)
# günlere göre 5 katlı çapraz doğrulama ile güç kalibrasyonu
kat = {g: i % 5 for i, g in enumerate(gunler)}
for r in R:
    egit = [x for x in R if kat[x["gun"]] != kat[r["gun"]]]
    r["_a"] = None
alfa_k = {}
for f in range(5):
    alfa_k[f] = fit_alfa([x for x in R if kat[x["gun"]] != f])
for r in R:
    r["guc"] = guc(r["g"], alfa_k[kat[r["gun"]]])
print("alfa (kat başına):", {k: round(v, 2) for k, v in alfa_k.items()})


def rapor(ad, anahtarlar, taban="pp"):
    S = [r for r in R if all(k in r for k in anahtarlar + [taban])]
    if not S:
        return
    print(f"\n== {ad}: ortak koşu {len(S)}, gün {len({r['gun'] for r in S})}")
    L = {k: np.array([nll(r[k], r["w"]) for r in S]) for k in anahtarlar + [taban]}
    gun_idx = {}
    for i, r in enumerate(S):
        gun_idx.setdefault(r["gun"], []).append(i)
    for k in L:
        print(f"  {k:5s} log-kayıp {L[k].mean():.4f}")
    for k in anahtarlar:
        d = L[k] - L[taban]
        bs = []
        gl = list(gun_idx)
        for _ in range(2000):
            sel = [random.choice(gl) for _ in gl]
            idx = [i for g in sel for i in gun_idx[g]]
            bs.append(d[idx].mean())
        print(f"  {k:5s} − {taban}: {d.mean():+.4f}  %95 GA [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]  (negatif = {k} daha iyi)")


rapor("Piyasa varyantları", ["guc", "agf"], "pp")
rapor("Modeller / kapanış piyasası", ["pm", "pm2", "pm3", "pm4"], "pp")
rapor("Modeller / kalibre piyasa", ["pm", "pm2", "pm3", "pm4"], "guc")
