"""T179 (ön kayıt hipotez_defteri): altılı kupon kurma kuralları geriye dönük karşılaştırma."""
import json, glob, gzip, re, math, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from tjk.kupon import kur, ozet, birim
rng = np.random.default_rng(179)
def modelP(pp, z, w0, c2):
    l = np.log(np.maximum(pp, 1e-6)); s = w0 * l + c2 * l * l + z; e = np.exp(s - s.max()); return e / e.sum()
ALT = {}
for f in sorted(glob.glob("data/atyarisi/2026-*.json.gz")):
    try: x = json.load(gzip.open(f))
    except Exception: continue
    g_ = x.get("tarih") or f.split("/")[-1][:10]
    for hh, L in (x.get("program") or {}).items():
        for r in L or []:
            for m in re.findall(r"(\d)\. 6'LI GANYAN bu koşudan başlar", str(r.get("bets"))):
                ALT.setdefault((g_, hh), {})[m] = int(r["number"])
OD = pd.concat([pd.read_csv(f) for f in glob.glob("data/odeme/2026-*.csv.gz")]); OD = OD[OD.tur == "6'LI GANYAN"]
S = []
for f in sorted(glob.glob("docs/data/gun/2026-*.json")):
    d = json.load(open(f, encoding="utf-8")); gun = d.get("tarih")
    if not gun or gun > "2026-11-06" or d.get("w0_g1") is None: continue
    for h in d["hipodromlar"]:
        K = {k["kosu"]: k for k in h["kosular"]}
        for alt, ilk in ALT.get((gun, h["id"]), {}).items():
            ay, kaz, ok = [], [], True
            for kn in range(int(ilk), int(ilk) + 6):
                k = K.get(kn)
                if not k or not k.get("sonuc"): ok = False; break
                so = k["sonuc"]; at = [a for a in k["atlar"] if not a.get("kosmaz") and str(a["no"]) in so]
                fa = "agf_a1" if str(alt) == "1" else "agf"
                agf = np.array([a.get(fa) or np.nan for a in at], float)
                zb = [a.get("z6b") if a.get("z6b") is not None else a.get("z6") for a in at]
                sira = np.array([so[str(a["no"])].get("sira") or 99 for a in at])
                if len(at) < 4 or np.isnan(agf).any() or (agf <= 0).any() or any(z is None for z in zb) or not (sira == 1).any(): ok = False; break
                pA = agf / agf.sum(); c2 = (d.get("lp2_g1") or 0.0) if all(a.get("z6b") is not None for a in at) else 0.0
                bA = modelP(pA, np.array(zb, float), d["w0_g1"], c2)
                ay.append({int(a["no"]): (float(bA[i]), float(pA[i])) for i, a in enumerate(at)}); kaz.append([int(a["no"]) for i, a in enumerate(at) if sira[i] == 1])
            if not ok: continue
            son = int(ilk) + 5; o = OD[(OD.tarih == gun) & (OD.hipodrom == h["id"]) & (OD.kosu == son)].tutar
            S.append(dict(gun=gun, hip=h["id"], alt=alt, ay=ay, kaz=kaz, odeme=float(o.max()) if len(o) else float("nan")))
print("tam altılı:", len(S), "gün:", len({s['gun'] for s in S}))
def kapsama(ay, hed):
    TAU = [1, 1, .95, .90, .85, .80]; out = []
    for j, a in enumerate(ay):
        t = TAU[j]; z = sum(v[0] ** t for v in a.values()) or 1; g = {n: (v[0] ** t) / z for n, v in a.items()}
        sira = sorted(g, key=lambda n: -g[n]); cum = 0; sec = []
        for n in sira[:10]:
            if cum >= hed: break
            sec.append(n); cum += g[n]
        out.append(sec or sira[:1])
    return out
KUR = {"F48": lambda a: kur(a, 48, "favori"), "F192": lambda a: kur(a, 192, "favori"), "D48": lambda a: kur(a, 48, "deger"), "D192": lambda a: kur(a, 192, "deger"),
       "K50": lambda a: kapsama(a, .50), "K65": lambda a: kapsama(a, .65)}
rows = []
for s in S:
    for ad, fn in KUR.items():
        sec = fn(s["ay"]); o = ozet(s["ay"], sec); hit = sum(1 for i in range(6) if set(s["kaz"][i]) & set(sec[i]))
        b = o["kombinasyon"] * birim(s["hip"]); kz = (s["odeme"] if hit == 6 and s["odeme"] == s["odeme"] else 0.0)
        rows.append(dict(gun=s["gun"], hip=s["hip"], alt=s["alt"], k=ad, hit=hit, komb=o["kombinasyon"], bedel=b, kazanc=kz, tm=o["tutma_model"]))
D = pd.DataFrame(rows)
def boot(fn, df, n=3000):
    gs = df.gun.unique(); idx = {g: df[df.gun == g] for g in gs}; r = []
    for _ in range(n):
        q = pd.concat([idx[g] for g in rng.choice(gs, len(gs))]); r.append(fn(q))
    return np.percentile(r, [2.5, 97.5])
print(f"{'kural':5} {'n':>3} {'ort.ayak':>9} {'[aralık]':>16} {'≥5 oranı':>9} {'6/6':>4} {'ort.komb':>9} {'bedel':>7} {'ROI':>8}")
for k in KUR:
    x = D[D.k == k]; lo, hi = boot(lambda q: q.hit.mean(), x)
    print(f"{k:5} {len(x):3d} {x.hit.mean():9.3f} [{lo:5.2f};{hi:5.2f}] {(x.hit>=5).mean():9.3f} {int((x.hit==6).sum()):4d} {x.komb.mean():9.1f} {x.bedel.sum():7.0f} {x.kazanc.sum()/x.bedel.sum()-1:+8.2f}")
print("=== Eşleşmiş fark (kural − F192): ayak ort. | ≥5 oranı | maliyet oranı")
F = D[D.k == "F192"].set_index(["gun", "hip", "alt"])
for k in KUR:
    if k == "F192": continue
    X = D[D.k == k].set_index(["gun", "hip", "alt"]).join(F, rsuffix="_F").reset_index()
    f1 = lambda q: (q.hit - q.hit_F).mean(); f2 = lambda q: ((q.hit >= 5).astype(float) - (q.hit_F >= 5).astype(float)).mean(); f3 = lambda q: q.komb.mean() / q.komb_F.mean()
    a = boot(f1, X); b = boot(f2, X)
    print(f"  {k:5}: ayak {f1(X):+.3f} [{a[0]:+.3f};{a[1]:+.3f}] | ≥5 {f2(X):+.3f} [{b[0]:+.3f};{b[1]:+.3f}] | maliyet ×{f3(X):.2f}")
print("=== G (gün filtresi): F192, eşik = ilk yarının tutma_model medyanı; değerlendirme ikinci yarı")
Fd = D[D.k == "F192"].sort_values("gun").reset_index(drop=True); m = len(Fd) // 2; esik = Fd.tm[:m].median(); T = Fd[m:]; Y = T[T.tm >= esik]; N = T[T.tm < esik]
for ad, x in (("oynanan", Y), ("elenen", N), ("hepsi", T)):
    if len(x): print(f"  {ad:8}: n {len(x)}  ort.ayak {x.hit.mean():.3f}  ≥5 {(x.hit>=5).mean():.3f}  6/6 {int((x.hit==6).sum())}  bedel {x.bedel.sum():.0f}  kazanç {x.kazanc.sum():.0f}")
print("  eşik (tutma_model):", round(float(esik), 5))
if len(Y) and len(N):
    d_ = Y.hit.mean() - N.hit.mean(); lo, hi = boot(lambda q: q.hit.mean(), Y)
    print(f"  oynanan − elenen ortalama ayak farkı: {d_:+.3f}")
print("=== Kalibrasyon: model tutma beklentisi vs gerçek 6/6 (F192, tüm altılılar):", round(float(D[D.k=='F192'].tm.sum()), 2), "beklenen |", int((D[D.k=='F192'].hit == 6).sum()), "gerçek")
