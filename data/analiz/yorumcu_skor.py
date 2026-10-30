"""T58 yorumcu puanlama. python3 data/analiz/yorumcu_skor.py [tarih ...]
Kaynaklar: data/yorumcu/<gün>*.json (Doğan'ın elle girdikleri, koşu başına liste) ve data/yorumcu/otomatik/<gün>.json (sporx kuponları, altılı ayakları; yapay zeka günün atı).
Sonuç: docs/data/gun/<gün>.json (sonuc: sıra 1 = kazanan). Karşılaştırma: aynı boyutlu AGF ilk-k ve model (z4) ilk-k kümeleri."""
import sys, os, json, glob, math
import numpy as np
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def gun(t):
    p = os.path.join(KOK, "docs", "data", "gun", t + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
def kazanan(k):
    s = k.get("sonuc") or {}
    w = [int(n) for n, v in s.items() if v.get("sira") == 1]
    return w[0] if w else None
def ilk_k(k, key, kk):
    at = [a for a in k["atlar"] if not a.get("kosmaz") and a.get(key) is not None]
    return {a["no"] for a in sorted(at, key=lambda a: -a[key])[:kk]}
def kosu_bul(G, hip, n):
    h = next((x for x in G["hipodromlar"] if x["id"] == hip), None)
    return h, (next((k for k in h["kosular"] if k["kosu"] == n), None) if h else None)
def altili_kosular(h, no):
    ks = sorted(k["kosu"] for k in h["kosular"])
    return ks[:6] if no == 1 else ks[-6:] if no == 2 else None
def main(tarihler):
    R = {}                                                   # kaynak -> liste (isabet, k, agf_isabet, model_isabet, oran)
    for t in tarihler:
        G = gun(t)
        if not G: continue
        for f in sorted(glob.glob(os.path.join(KOK, "data", "yorumcu", t + "*.json"))):
            Y = json.load(open(f, encoding="utf-8")); ad = Y.get("kaynak", os.path.basename(f))[:30]
            for n, nolar in Y["kosular"].items():
                h, k = kosu_bul(G, Y["hipodrom"], int(n)); w = kazanan(k) if k else None
                if w is None: continue
                kk = len(nolar); at = [a for a in k["atlar"] if not a.get("kosmaz")]
                R.setdefault(ad, []).append((w in nolar, kk, w in ilk_k(k, "agf", kk), w in ilk_k(k, "z4", kk), kk / len(at)))
        fo = os.path.join(KOK, "data", "yorumcu", "otomatik", t + ".json")
        if os.path.exists(fo):
            D = json.load(open(fo, encoding="utf-8"))
            for key, c in D["kuponlar"].items():
                h = next((x for x in G["hipodromlar"] if x["id"] == c["hip"]), None)
                ks = altili_kosular(h, c["altili_no"]) if h else None
                if not ks: continue
                hits = []; maliyet = 1
                for ay, n in zip(c["ayaklar"], ks):
                    _, k = kosu_bul(G, c["hip"], n); w = kazanan(k) if k else None
                    if w is None: hits = None; break
                    kk = len(ay); at = [a for a in k["atlar"] if not a.get("kosmaz")]; maliyet *= kk
                    hits.append((w in ay, kk, w in ilk_k(k, "agf", kk), w in ilk_k(k, "z4", kk), kk / len(at)))
                if hits is None: continue
                R.setdefault("sporx:" + c["slug"] + " (ayak)", []).extend(hits)
                R.setdefault("sporx:" + c["slug"] + " (altılı tam)", []).append((all(x[0] for x in hits), maliyet, all(x[2] for x in hits), all(x[3] for x in hits), 0))
            for key, y in D["yz"].items():
                _, k = kosu_bul(G, y["hip"], y["kosu"]); w = kazanan(k) if k else None
                if w is None: continue
                no = next((a["no"] for a in k["atlar"] if a["at"].replace("İ", "I").upper() == y["at"].replace("İ", "I").upper()), None)
                R.setdefault("yz:" + y["ad"], []).append((w == no, 1, w in ilk_k(k, "agf", 1), w in ilk_k(k, "z4", 1), 1 / len(k["atlar"])))
    print("kaynak | n | yorumcu isabet | AGF ilk-k | model ilk-k | ort. k | rastgele beklenti")
    for ad, L in R.items():
        a = np.array(L, float); print(f"{ad:42s} {len(a):3d} | {a[:,0].mean()*100:5.1f}% | {a[:,2].mean()*100:5.1f}% | {a[:,3].mean()*100:5.1f}% | k={a[:,1].mean():.1f} | {a[:,4].mean()*100:5.1f}%")
if __name__ == "__main__":
    main(sys.argv[1:] or ["2026-10-30"])
