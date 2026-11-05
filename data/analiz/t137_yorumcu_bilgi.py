"""T137: yorumcu bilgi taşıyor mu? (hipotez_defteri.md ön kaydı 2026-11-06). Tekrar çalıştırılabilir."""
import glob, json, os, collections, numpy as np, pandas as pd
rng = np.random.default_rng(137)
def log(*a): print(*a, flush=True)
IX = {}   # (tarih,hipodrom,kosu,no) -> (p, piyasa sırası, kazandı); kaynak docs/data/gun/*.json sonuc.pp (kapanış ganyanından piyasa olasılığı)
for f in sorted(glob.glob("docs/data/gun/2026-*.json")):
    t = os.path.basename(f)[:10]; G = json.load(open(f, encoding="utf-8"))
    for h in G["hipodromlar"]:
        for k in h["kosular"]:
            sn = k.get("sonuc") or {}
            if not sn: continue
            rows = [(int(n), v.get("pp"), v.get("sira")) for n, v in sn.items() if v.get("pp") is not None]
            if len(rows) < 3: continue
            S = sum(r[1] for r in rows); order = sorted(rows, key=lambda r: -r[1])
            for rk, (n, pp, sira) in enumerate(order, 1): IX[(t, h["id"], int(k["kosu"]), n)] = (pp / S, rk, 1.0 if sira == 1 else 0.0)
log("sonuçlu koşu-at kaydı", len(IX))
def hnorm(h): return str(h).lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c").replace("i̇", "i")
birinci = collections.defaultdict(set); liste = collections.defaultdict(set); kanal = collections.defaultdict(set)
for f in sorted(glob.glob("data/yorumcu/20*.json")):
    d = json.load(open(f)); 
    if d.get("tur") == "tuyo" or "kosular" not in d: continue
    t = d["tarih"]; h = hnorm(d["hipodrom"]); kn = d.get("kaynak", os.path.basename(f))
    hepsi = set(str(x) for x in (d.get("hepsi") or []))
    for k, nos in d["kosular"].items():
        if k in hepsi: continue
        for n in nos: liste[(t, h, int(k), int(n))].add(kn)
    if d.get("sirali") and d.get("ilk_tercih"):
        for k, n in d["ilk_tercih"].items():
            if k in hepsi: continue
            birinci[(t, h, int(k), int(n))].add(kn); kanal[kn].add((t, h, int(k), int(n)))
def oe(keys, ad):
    rows = [(k[0], IX[k][0], IX[k][2]) for k in keys if k in IX and IX[k][1] >= 3]
    if not rows: log("  %-44s n=0" % ad); return
    D = pd.DataFrame(rows, columns=["gun", "p", "y"]); g = D.groupby("gun"); S = g.y.sum().values; E = g.p.sum().values; N = g.size().values
    o = S.sum() / E.sum(); bs = []
    for _ in range(2000):
        k = rng.integers(0, len(S), len(S)); bs.append(S[k].sum() / max(E[k].sum(), 1e-9))
    lo, hi = np.percentile(bs, [2.5, 97.5]); log("  %-44s n=%4d kazanan=%3d beklenen=%6.1f  O/E %.2f [%.2f, %.2f]" % (ad, N.sum(), S.sum(), E.sum(), o, lo, hi))
sonuclu = lambda keys: [k for k in keys if k in IX]
log("sonuçlanmış not satırı: birinci tercih", len(sonuclu(birinci)), "| listeye giren at", len(sonuclu(liste)))
log("== A (birincil): sıralı kanalların birinci tercihi, piyasa sırası >=3"); oe(list(birinci), "A tüm sıralı kanallar"); 
na = sum(1 for k in birinci if k in IX and IX[k][1] >= 3); log("   n(A) =", na, "-> karar için 300 gerekli" if na < 300 else "-> KARAR BAKILABİLİR")
log("== B: listeye giren, piyasa sırası >=3 (oy sayısına göre)")
oe([k for k in liste if len(liste[k]) == 1], "B oy=1 kanal"); oe([k for k in liste if len(liste[k]) >= 2], "B oy>=2 kanal"); oe(list(liste), "B tümü")
log("== TABAN (karşılaştırma): aynı günlerde TÜM piyasa sırası >=3 atlar"); oe([k for k in IX if (k[0],k[1]) in set((x[0],x[1]) for x in liste)], "taban tüm sıra>=3 atlar (not günleri/hipodromları)")
log("== C: kanal bazlı birinci tercih, piyasa sırası >=3 (betimsel)")
for kn, ks in sorted(kanal.items(), key=lambda x: -len(x[1])): oe(list(ks), kn[:44])
log("bitti")
