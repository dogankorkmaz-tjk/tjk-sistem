"""Elle girilen kâğıt üstü kayıtların (data/abd_kayit) değerlendirmesi: Güney Afrika, Fransa ve elle girilen tüm koşular.
Sonuç kaynağı: data/abd_sonuc/<gün>_<pist>_<koşu>.json (siteden girilir) ya da kaydın içindeki 'sonuc' (sira + ganyan).
Ödeme: işaretli at kazandıysa kazananın ganyanı (resmî), değilse 0. Bahis anı ganyanı ('tjk') yalnız karşılaştırma içindir.
Çıktı: docs/data/abd_kayit_ozet.json. Kullanım: python3 -I data/analiz/abd_kayit_degerlendir.py"""
import glob, json, os, re

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def main():
    kay = {}
    for f in sorted(glob.glob(KOK + "/data/abd_kayit/*.json")):
        try:
            k = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        a = (k.get("tarih"), slug(k.get("pist")), str(k.get("kosu")))
        if a not in kay or (k.get("zaman") or "") >= (kay[a].get("zaman") or ""):
            kay[a] = k
    sonuc = {}
    for f in glob.glob(KOK + "/data/abd_sonuc/*.json"):
        try:
            s = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        sonuc[(s.get("tarih"), slug(s.get("pist")), str(s.get("kosu")))] = s
    satir, bekleyen, bahis, isabet, odeme = [], 0, 0, 0, 0.0
    ulke = {}
    for a, k in sorted(kay.items()):
        isr = k.get("isaretli") or []
        s = sonuc.get(a) or k.get("sonuc") or {}
        sira = s.get("sira") or []
        g = s.get("ganyan") or s.get("kazanan_ganyan")
        if not isr:
            continue
        if not sira or not g:
            bekleyen += 1
            satir.append({"tarih": a[0], "pist": k.get("pist"), "kosu": k.get("kosu"), "ulke": k.get("ulke"), "durum": "sonuç/ganyan bekleniyor", "isaretli": [x["no"] for x in isr]})
            continue
        for x in isr:
            kaz = x["no"] == sira[0]
            bahis += 1; isabet += kaz; odeme += g if kaz else 0
            u = ulke.setdefault(k.get("ulke") or "?", [0, 0, 0.0]); u[0] += 1; u[1] += kaz; u[2] += g if kaz else 0
            satir.append({"tarih": a[0], "pist": k.get("pist"), "kosu": k.get("kosu"), "ulke": k.get("ulke"), "no": x["no"], "kazandi": bool(kaz),
                          "bahis_ani_tjk": x.get("tjk"), "kapanis_ganyan_kazanan": g})
    cik = {"kayitli_kosu": len(kay), "bekleyen": bekleyen, "bahis": bahis, "isabet": isabet, "roi": round(odeme / bahis, 3) if bahis else None,
           "ulke": {u: {"bahis": v[0], "isabet": v[1], "roi": round(v[2] / v[0], 3)} for u, v in ulke.items()},
           "not": "Küçük örnek; karar için en az 300 bahis (hipotez defteri).", "satirlar": satir[-60:]}
    os.makedirs(KOK + "/docs/data", exist_ok=True)
    json.dump(cik, open(KOK + "/docs/data/abd_kayit_ozet.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({k: v for k, v in cik.items() if k != "satirlar"})


if __name__ == "__main__":
    main()
