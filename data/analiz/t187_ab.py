"""T187 adım A (kalibrasyon haritası) ve B (segment testi). Ön kayıt: hipotez_defteri T187. Çalıştırma: python3 data/analiz/t187_ab.py | tee data/analiz/t187_ab_sonuc.txt"""
import os, sys, re, gzip, json, glob, collections, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import g1
KOK = g1.KOK; rng = np.random.default_rng(187)
SPLIT = "2025-04-01"

# --- koşu meta (atyarisi program)
META = {}
for f in sorted(glob.glob(os.path.join(KOK, "data", "atyarisi", "*.json.gz"))):
    t = os.path.basename(f)[:10]
    try: x = json.load(gzip.open(f))
    except Exception: continue
    for h, L in (x.get("program") or {}).items():
        for r in L or []:
            td = (r.get("typeDescription") or "").lower(); gn = r.get("groupName") or ""
            if td.startswith("maiden"): tur = "maiden"
            elif td.startswith(("handikap", "kısa vade", "kv-")): tur = "handikap"
            elif td.startswith(("şartl", "şartli")): tur = "sartli"
            else: tur = "diger"
            yas = "2y" if gn.startswith("2 ") else "3y" if gn.startswith("3 Yaşlı") else "karisik" if gn else None
            irk = "arap" if "Arap" in gn else "ingiliz" if "İngiliz" in gn else None
            try: ms = int(r.get("distance"))
            except Exception: ms = None
            mes = None if ms is None else "<=1300" if ms <= 1300 else "1301-1800" if ms <= 1800 else ">1800"
            META[(t, h, int(r.get("number") or 0))] = dict(tur=tur, yas=yas, irk=irk, pist=r.get("raceCourseType") or None, mes=mes)

# --- koşular
K = collections.defaultdict(list)
for r in g1._satirlar(): K[(r["tarih"], r["hipodrom"], int(r["kosu"]))].append(r)
gunler = sorted({k[0] for k in K}); gi = {g: i for i, g in enumerate(gunler)}
H = []   # her at: gun_idx, pm, win, odds, meta
for key in sorted(K):
    ok = [r for r in K[key] if r["kosmadi"] != "True" and g1._fl(r["ganyan"], 0) > 1 and g1._fl(r["sira"], 0) > 0]
    if len(ok) < 6: continue
    if sum(1 for r in ok if g1._fl(r["sira"]) == 1.0) != 1: continue
    inv = np.array([1 / g1._fl(r["ganyan"]) for r in ok]); pm = inv / inv.sum(); n = len(ok)
    m = META.get(key, {}); alan = "<=8" if n <= 8 else "9-10" if n <= 10 else ">=11"
    for p, r in zip(pm, ok):
        H.append((gi[key[0]], key[0], float(p), 1.0 if g1._fl(r["sira"]) == 1.0 else 0.0, g1._fl(r["ganyan"]), alan, m.get("tur"), m.get("yas"), m.get("irk"), m.get("pist"), m.get("mes"), key[1]))
print("at-koşu", len(H), "koşu", len({(h[1], h[11]) for h in H}), "gün", len(gunler))
band = lambda p: "favori" if p >= .25 else "orta" if p >= .08 else "uzun"
bins = [(0, .03), (.03, .06), (.06, .10), (.10, .17), (.17, .30), (.30, 1.01)]
ND = len(gunler)

def hucre_matris(filtre):
    M = np.zeros((ND, 4))   # n, Σpm, Σwin, Σödeme
    for h in H:
        if filtre(h): M[h[0]] += (1, h[2], h[3], h[3] * h[4])
    return M

def boot(M, B, lo_q):
    d = np.where(M.sum(1) > 0)[0]
    if len(d) < 5: return None
    Md = M[d]; W = rng.multinomial(len(d), np.ones(len(d)) / len(d), size=B).astype(float); S = W @ Md
    with np.errstate(divide="ignore", invalid="ignore"):
        orn = S[:, 2] / S[:, 1]; roi = S[:, 3] / S[:, 0] - 1
    q = [lo_q, 1 - lo_q]
    return np.nanpercentile(orn, [100 * x for x in q]), np.nanpercentile(roi, [100 * x for x in q])

def ozet(M, B=2000, lo_q=.025):
    n, spm, sw, sp = M.sum(0)
    if n == 0: return None
    b = boot(M, B, lo_q)
    return dict(n=int(n), orn=sw / spm, roi=sp / n - 1, orn_ga=b[0] if b else (np.nan, np.nan), roi_ga=b[1] if b else (np.nan, np.nan), kaz=int(sw))

keş = np.array([g < SPLIT for g in gunler]); dog = ~keş
def kes(M, mask): X = M.copy(); X[~mask] = 0; return X

print("\n=== ADIM A: genel kalibrasyon (keşif | doğrulama | tümü) — oran = gerçek kazanan / Σpm; ROI 1 TL düz ganyan, büyük ödemeler dahil ===")
for lo, hi in bins:
    M = hucre_matris(lambda h: lo <= h[2] < hi)
    for ad, mk in (("keşif", keş), ("doğr.", dog), ("tümü", keş | dog)):
        s = ozet(kes(M, mk))
        print(f"pm[{lo:.2f},{min(hi,1):.2f}) {ad:6s} n={s['n']:6d} kazanan {s['kaz']:5d} oran {s['orn']:.3f} [{s['orn_ga'][0]:.3f};{s['orn_ga'][1]:.3f}]  ROI {s['roi']:+.1%} [{s['roi_ga'][0]:+.1%};{s['roi_ga'][1]:+.1%}]")

print("\n=== ADIM B: segment × pm bandı ===")
BOY = {"alan": 5, "tur": 6, "yas": 7, "irk": 8, "pist": 9, "mes": 10, "hip": 11}
hucre = []
for ad, ix in BOY.items():
    for sev in sorted({h[ix] for h in H if h[ix]}):
        for bd in ("favori", "orta", "uzun"):
            hucre.append((ad, sev, bd, ix))
adaylar = []
for ad, sev, bd, ix in hucre:
    M = hucre_matris(lambda h: h[ix] == sev and band(h[2]) == bd)
    Mk = kes(M, keş)
    if Mk[:, 0].sum() < 400: continue
    adaylar.append((ad, sev, bd, M))
m = len(adaylar); loq = .025 / m
print(f"Keşifte n>=400 olan hücre sayısı m={m}; Bonferroni nominal %{100*loq:.3f} kuyruk")
sonuc = []
for ad, sev, bd, M in adaylar:
    k = ozet(kes(M, keş), B=6000, lo_q=loq); d = ozet(kes(M, dog), B=2000)
    yon = 1 if k["orn_ga"][0] > 1 else -1 if k["orn_ga"][1] < 1 else 0
    dgz = None
    if d and d["n"] >= 200:
        dgz = (d["orn_ga"][0] > 1) if yon == 1 else (d["orn_ga"][1] < 1) if yon == -1 else False
    sonuc.append((ad, sev, bd, k, d, yon, dgz))
    
sonuc.sort(key=lambda s: -abs(math.log(s[3]["orn"])))
print("\nEn büyük 25 sapma (keşif oranı) — keşif oran [Bonf. GA] ROI | doğrulama oran [GA] ROI n:")
for ad, sev, bd, k, d, yon, dgz in sonuc[:25]:
    ds = "yok" if not d else f"oran {d['orn']:.3f} [{d['orn_ga'][0]:.3f};{d['orn_ga'][1]:.3f}] ROI {d['roi']:+.1%} [{d['roi_ga'][0]:+.1%};{d['roi_ga'][1]:+.1%}] n={d['n']}"
    print(f"{ad}:{sev}/{bd} | keşif n={k['n']} oran {k['orn']:.3f} [{k['orn_ga'][0]:.3f};{k['orn_ga'][1]:.3f}] ROI {k['roi']:+.1%} | doğr. {ds}")

ya = [s for s in sonuc if s[5] != 0]
print(f"\nKeşifte Bonferroni-anlamlı sapma gösteren hücre: {len(ya)} / {m}")
yf = [s for s in ya if s[6]]
print(f"  doğrulamada aynı yönde nominal anlamlı (YANLIŞ FİYATLANMIŞ): {len(yf)}")
for ad, sev, bd, k, d, yon, dgz in yf:
    kul = d["roi"] > 0 and k["roi"] > 0; tk = kul and d["roi_ga"][0] > 0
    print(f"  {ad}:{sev}/{bd} yön {'+' if yon>0 else '-'}  keşif ROI {k['roi']:+.1%}  doğr. oran {d['orn']:.3f} ROI {d['roi']:+.1%} [{d['roi_ga'][0]:+.1%};{d['roi_ga'][1]:+.1%}]  KULLANILABİLİR={kul} TAKEOUT'U GEÇTİ={tk}")
# beklenen tesadüf: nominal %2,5/kuyruk x m hücre
print(f"Bilgi: doğrulamada nominal GA tesadüfen ~{0.05*len(ya):.1f} 'doğrulama' bekleriz (yalnız anlamlı keşif hücreleri arasında).")
