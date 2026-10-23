"""Jason tüyosunun egzotik bahislerde değerlendirilmesi (kâğıt üstü, ön kayıt 23 Ekim 2026; kurallar sonuç görülmeden donduruldu).
Her dondurulmuş tüyo atı T için, koşunun sabah AGF'sine (agf0) göre T hariç en yüksek iki atı F1, F2:
  İKİLİ: {T,F1}, {T,F2}  | SIRALI İKİLİ: T-F1, T-F2 (T birinci)  -> 2 kombinasyon, birim 1 TL.
Kontrol (aynı koşular, yalnız piyasa): AGF'nin en yüksek üç atı F1,F2,F3 arasında İKİLİ kutu (3 komb) ve SIRALI İKİLİ tüm sıralar (6 komb).
Ödemeler data/odeme (TJK CSV veya atyarisi API). Karar için en az 300 tüyo; gün kümeli bootstrap; ara bakışlar karar değildir."""
import os, json, glob
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data"), os.path.join(KOK, "docs", "data")


def _odeme(gun):
    try:
        od = pd.read_csv(os.path.join(VERI, "odeme", gun[:7] + ".csv.gz"))
    except Exception:
        return {}
    od = od[(od.tarih == gun) & od.tur.isin(["İKİLİ", "SIRALI İKİLİ"])]
    out = {}
    for r in od.itertuples():
        out.setdefault((r.hipodrom, int(r.kosu), r.tur), []).append((str(r.kombo), float(r.tutar)))
    return out


def _tut(od, hip, kosu, tur, kombolar):
    """kombolar: ödemeyle eşleşecek 'a/b' dizgeleri kümesi (İKİLİ'de küçük/büyük sıralı). Döner: ödeme toplamı (1 TL birim)."""
    t = 0.0
    for kombo, tutar in od.get((hip, kosu, tur), []):
        k = kombo.strip()
        if tur == "İKİLİ":
            p = sorted(k.split("/"), key=lambda x: int(x)) if "/" in k else [k]
            k = "/".join(p)
        if k in kombolar:
            t += tutar
    return t


def hesapla():
    S = {t: {"n": 0, "maliyet": 0.0, "donus": 0.0, "isabet": 0, "gun": {}} for t in ("İKİLİ", "SIRALI İKİLİ")}
    K = {t: {"n": 0, "maliyet": 0.0, "donus": 0.0, "isabet": 0} for t in ("İKİLİ", "SIRALI İKİLİ")}
    for y in sorted(glob.glob(os.path.join(VERI, "tuyo", "*.json"))):
        gun = os.path.basename(y)[:-5]
        gy = os.path.join(SITE, "gun", gun + ".json")
        if not os.path.exists(gy):
            continue
        G = json.load(open(gy, encoding="utf-8")); od = _odeme(gun)
        kos = {(h["id"], k["kosu"]): k for h in G["hipodromlar"] for k in h["kosular"]}
        gorulen = set()
        for c in json.load(open(y, encoding="utf-8")).values():
            if "sira" not in c:
                continue
            k = kos.get((c["hipodrom"], c["kosu"]))
            if not k:
                continue
            at = [a for a in k["atlar"] if not a.get("kosmaz") and (a.get("agf0") or a.get("agf"))]
            at.sort(key=lambda a: -(a.get("agf0") or a.get("agf") or 0))
            f = [a["no"] for a in at if a["no"] != c["no"]][:2]
            if len(f) < 2:
                continue
            T = c["no"]
            ik = {"/".join(map(str, sorted([T, x]))) for x in f}
            sr = {f"{T}/{x}" for x in f}
            for tur, kombolar in (("İKİLİ", ik), ("SIRALI İKİLİ", sr)):
                if (c["hipodrom"], c["kosu"], tur) not in od:
                    continue                                   # ödeme verisi yoksa değerlendirilmez
                tt = _tut(od, c["hipodrom"], c["kosu"], tur, kombolar)
                s = S[tur]; s["n"] += 1; s["maliyet"] += 2; s["donus"] += tt; s["isabet"] += tt > 0
                d = s["gun"].setdefault(gun, [0, 0.0, 0.0]); d[0] += 1; d[1] += 2; d[2] += tt
                kk = (c["hipodrom"], c["kosu"], tur)
                if kk not in gorulen:                           # kontrol: koşu başına bir kez (üç favori)
                    gorulen.add(kk)
                    top3 = [a["no"] for a in at[:3]]
                    if len(top3) == 3:
                        if tur == "İKİLİ":
                            kb = {"/".join(map(str, sorted([x, y2]))) for i, x in enumerate(top3) for y2 in top3[i + 1:]}; mal = 3
                        else:
                            kb = {f"{x}/{y2}" for x in top3 for y2 in top3 if x != y2}; mal = 6
                        t2 = _tut(od, c["hipodrom"], c["kosu"], tur, kb)
                        q = K[tur]; q["n"] += 1; q["maliyet"] += mal; q["donus"] += t2; q["isabet"] += t2 > 0
    out = {}
    for tur in S:
        s = S[tur]; q = K[tur]
        out[tur] = {"n": s["n"], "isabet": s["isabet"], "maliyet": s["maliyet"], "geri_donus": round(s["donus"] / s["maliyet"], 3) if s["maliyet"] else None,
                    "kontrol": {"koşu": q["n"], "isabet": q["isabet"], "maliyet": q["maliyet"], "geri_donus": round(q["donus"] / q["maliyet"], 3) if q["maliyet"] else None},
                    "gun": {g: v for g, v in s["gun"].items()}}
    return out


def guncelle():
    o = hesapla()
    os.makedirs(SITE, exist_ok=True)
    json.dump({"sonuc": o}, open(os.path.join(SITE, "tuyo_egz.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return o


if __name__ == "__main__":
    for t, v in guncelle().items():
        print(t, {k: v[k] for k in ("n", "isabet", "maliyet", "geri_donus", "kontrol")})
