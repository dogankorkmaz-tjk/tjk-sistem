"""Benter-K (gölge, T155) ileriye dönük takip: Benter (z6) ile ayrıştığı yerler ve sonuçlar.
Kaynak: docs/data/gun/*.json (zk6 ve z6'nın donmuş, koşu öncesi son hâli + sonuç) ve docs/data/besli.json (-G kuponları).
Kullanım: python3 data/analiz/benterk_ayrisma.py [BAŞLANGIÇ, varsayılan 2026-11-07]
Ölçüler (AGF ile, iki model aynı piyasa girdisiyle):
  - kazanan ve ilk-5 (sıraya özgü δ dahil) log kaybı farkı K − Benter, gün-küme bootstrap %95
  - ayrışan koşular: favori farklı / ilk-5 kümesi farklı → hangisinin seçimi tuttu
  - sıralı 5'li -G kuponları: Benter-K-G vs G1-S-G aynı bütçede harcama/kazanç (büyük ödemeler DAHİL, güven aralıklı)
Not: resmî ileri pencere kararı (Ocak sonu) harness ile verilir (T154/T155 ön kaydı); bu betik canlı kayıttan betimseldir."""
import glob, json, math, os, sys
import numpy as np

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BAS = sys.argv[1] if len(sys.argv) > 1 else "2026-11-07"
rng = np.random.default_rng(7)


def sm(s):
    m = max(s); e = [math.exp(x - m) for x in s]; z = sum(e); return [x / z for x in e]


def pl_kayip(p, sira, gam, off=None, n=5):
    """Sıraya özgü üs + ofsetli PL: adım j'de ağırlık p_i^γ_j · exp(off_j,i). sira: bitiriş sırasına göre indeksler."""
    kalan = list(range(len(p))); L = []
    for j in range(min(n, len(sira))):
        w = [max(p[i], 1e-12) ** gam[j] * (math.exp(off[j][i]) if off else 1.0) for i in kalan]; t = sum(w)
        L.append(-math.log(w[kalan.index(sira[j])] / t)); kalan.remove(sira[j])
    return np.cumsum(L)


S = []; AY = []
for f in sorted(glob.glob(os.path.join(KOK, "docs", "data", "gun", "20*.json"))):
    t = os.path.basename(f)[:10]
    if t < BAS:
        continue
    o = json.load(open(f, encoding="utf-8"))
    if o.get("w0_k") is None or o.get("w0_g1") is None:
        continue
    for h in o["hipodromlar"]:
        for k in h["kosular"]:
            so = k.get("sonuc")
            at = [a for a in k["atlar"] if a.get("agf") and not a.get("kosmaz")]
            if not so or len(at) < 5 or any(a.get("zk6") is None or a.get("z6") is None or a.get("zkd") is None for a in at):
                continue
            sr = {int(n): v.get("sira") for n, v in so.items() if v.get("sira")}
            if not all(a["no"] in sr for a in at):
                continue
            tot = sum(a["agf"] for a in at); pp = [a["agf"] / tot for a in at]
            pg = sm([o["w0_g1"] * math.log(max(p, 1e-6)) + a["z6"] for p, a in zip(pp, at)])
            pk = sm([o["w0_k"] * math.log(max(p, 1e-6)) + a["zk6"] for p, a in zip(pp, at)])
            sira = sorted(range(len(at)), key=lambda i: sr[at[i]["no"]])
            if [sr[at[i]["no"]] for i in sira[:5]] != [1, 2, 3, 4, 5]:
                continue
            off = [[0.0] * len(at)] + [[g * a["zkd"] for a in at] for g in o["a_k"][1:]]
            Lg = pl_kayip(pg, sira, o["a_g1"]); Lk = pl_kayip(pk, sira, o["a_k"], off)
            fg, fk = int(np.argmax(pg)), int(np.argmax(pk)); t5g = set(np.argsort(pg)[::-1][:5]); t5k = set(np.argsort(pk)[::-1][:5]); ilk5 = set(sira[:5])
            S.append(dict(gun=t, d=Lk - Lg, fav_farkli=fg != fk, fg_kazandi=sira[0] == fg, fk_kazandi=sira[0] == fk,
                          t5_farkli=t5g != t5k, t5g_isabet=len(t5g & ilk5), t5k_isabet=len(t5k & ilk5)))

if not S:
    print("Henüz Benter-K puanlı ve sonuçlanmış koşu yok (başlangıç", BAS + ")."); sys.exit()
D = np.array([s["d"] for s in S]); gun = np.array([s["gun"] for s in S]); ug, inv = np.unique(gun, return_inverse=True); N = np.bincount(inv)
print(f"Benter-K − Benter ({len(S)} koşu, {len(ug)} gün, {BAS} sonrası; negatif = Benter-K daha iyi)")
for j, ad in enumerate(["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]):
    Sm = np.bincount(inv, weights=D[:, j]); bs = []
    for _ in range(2000):
        kk = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)); bs.append((kk @ Sm) / (kk @ N))
    lo, hi = np.percentile(bs, [2.5, 97.5]); print(f"   {ad:8s} {D[:, j].mean():+.4f} [{lo:+.4f}; {hi:+.4f}]")
F = [s for s in S if s["fav_farkli"]]
print(f"Favori farklı: {len(F)} koşu | Benter'in favorisi kazandı {sum(s['fg_kazandi'] for s in F)}, Benter-K'nınki {sum(s['fk_kazandi'] for s in F)}")
T5 = [s for s in S if s["t5_farkli"]]
print(f"İlk-5 kümesi farklı: {len(T5)} koşu | ilk 5'e giren at sayısı toplamı: Benter {sum(s['t5g_isabet'] for s in T5)}, Benter-K {sum(s['t5k_isabet'] for s in T5)}")
try:
    b = json.load(open(os.path.join(KOK, "docs", "data", "besli.json"), encoding="utf-8"))
    print("Sıralı 5'li -G kuponları (kâğıt üstü, büyük ödemeler dahil):")
    for x in sorted([x for x in b.get("toplam", []) if x.get("grup") == "hepsi" and x["model"] in ("G1-S-G", "Benter-K-G")], key=lambda x: (x["butce"], x["model"])):
        print(f"   {x['model']:11s} ≤{x['butce']:<4} koşu {x['kosu']:4d} harcama {x['harcama']:9.2f} kazanç {x['kazanc']:10.2f} isabet {x['isabet']}")
except Exception as e:
    print("besli.json okunamadı:", e)
