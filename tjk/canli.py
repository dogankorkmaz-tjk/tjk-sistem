"""Son dakika oran kaydı: sitede 'Kaydet' ile data/canli_oran/<tarih>_<hipodrom>_<kosu>_<SSDD>.json olarak yazılan, makinede görülen
ganyan oranlarını sonuçla karşılaştırır -> docs/data/canli.json.
Her koşu için son kayıt alınır. Model olasılığı: softmax(w0*log(piyasa) + z), piyasa = 1/oran normalize (ekür düzeltmesi yok).
Getiri iki türlü: girilen oranla (makinede gördüğün) ve kapanış ganyanıyla (resmî ödeme)."""
import os, glob, json
import numpy as np

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASOR = os.path.join(KOK, "data", "canli_oran")
SITE = os.path.join(KOK, "docs", "data")
ESIKLER = (1.0, 1.1, 1.2)


def _yarisi(g, hip, kosu):
    for h in g.get("hipodromlar", []):
        if h["id"] == hip:
            for k in h["kosular"]:
                if k["kosu"] == kosu:
                    return k
    return None


def ozet():
    son = {}
    for f in sorted(glob.glob(os.path.join(KLASOR, "*.json"))):
        try:
            r = json.load(open(f, encoding="utf-8"))
            son[(r["tarih"], r["hipodrom"], int(r["kosu"]))] = r        # dosya adı saat sırasıyla: sonuncusu kalır
        except Exception:
            continue
    if not son:
        return None
    gunler = {}; satirlar = []
    for (t, hip, kosu), r in sorted(son.items()):
        if t not in gunler:
            yol = os.path.join(SITE, "bugun.json")
            g = None
            for y in (os.path.join(SITE, "gun", t + ".json"), yol):
                if os.path.exists(y):
                    gg = json.load(open(y, encoding="utf-8"))
                    if gg.get("tarih") == t:
                        g = gg; break
            gunler[t] = g
        g = gunler[t]
        k = _yarisi(g, hip, kosu) if g else None
        oran = {str(a): float(str(o).replace(",", ".")) for a, o in r["oranlar"].items() if float(str(o).replace(",", ".")) >= 1.01}
        if not k or len(oran) < 2:
            continue
        atlar = [a for a in k["atlar"] if str(a["no"]) in oran]
        if len(atlar) < 2:
            continue
        ham = np.array([1.0 / oran[str(a["no"])] for a in atlar]); pp = ham / ham.sum()
        s = g.get("w0", 1.0) * np.log(np.maximum(pp, 1e-6)) + np.array([a.get("z", 0.0) or 0.0 for a in atlar])
        e = np.exp(s - s.max()); pm = e / e.sum()
        pj = None
        if g.get("w0_aday") is not None and all(a.get("z2") is not None for a in atlar):
            sj = g["w0_aday"] * np.log(np.maximum(pp, 1e-6)) + g.get("lp2_aday", 0.0) * np.log(np.maximum(pp, 1e-6)) ** 2 + np.array([a["z2"] for a in atlar])
            ej = np.exp(sj - sj.max()); pj = ej / ej.sum()
        sn = k.get("sonuc")
        for ix, (a, p1, p2) in enumerate(zip(atlar, pp, pm)):
            o = oran[str(a["no"])]; x = (sn or {}).get(str(a["no"]))
            satirlar.append({"tarih": t, "hipodrom": hip, "kosu": kosu, "no": a["no"], "at": a["at"], "saat": r.get("saat"), "oran": o,
                             "pp": float(p1), "pm": float(p2), "ev": float(p2 * o), "evj": float(pj[ix] * o) if pj is not None else None, "bitti": bool(sn),
                             "kazandi": (x or {}).get("sira") == 1 if sn else None, "kapanis": (x or {}).get("g") if sn else None})
    bitmis = [x for x in satirlar if x["bitti"] and x["kapanis"]]
    tablo = []; tablo_j = []
    for anahtar, hedef in (("ev", tablo), ("evj", tablo_j)):
      for esik in ESIKLER:
        sec = [x for x in bitmis if x.get(anahtar) is not None and x[anahtar] >= esik]
        n = len(sec)
        hedef.append({"esik": esik, "bahis": n, "isabet": sum(1 for x in sec if x["kazandi"]),
                      "getiri_girilen": round(sum(x["oran"] for x in sec if x["kazandi"]) / n, 3) if n else None,
                      "getiri_kapanis": round(sum(x["kapanis"] for x in sec if x["kazandi"]) / n, 3) if n else None})
    tum = len(bitmis)
    out = {"kosu": len({(x["tarih"], x["hipodrom"], x["kosu"]) for x in satirlar}), "biten_kosu": len({(x["tarih"], x["hipodrom"], x["kosu"]) for x in bitmis}),
           "tum_atlar_getiri_kapanis": round(sum(x["kapanis"] for x in bitmis if x["kazandi"]) / tum, 3) if tum else None,
           "tablo": tablo, "tablo_jason": tablo_j, "son": [x for x in satirlar if x["ev"] >= 1.0][-30:]}
    os.makedirs(SITE, exist_ok=True)
    json.dump(out, open(os.path.join(SITE, "canli.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return out
