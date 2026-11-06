"""T143-B (ön kayıt: hipotez_defteri 2026-11-06 20:10): padok/kanter yayınında at başına kimlikli görüntü süresi.
Girdi: data/padok_ocr/<gün>_<run>.csv.gz (1 kare/sn OCR) + data/atyarisi/<gün>.json.gz (program).
Kimlik kuralı (yanlış eşleşmeyi önlemek için; sonuç görülmeden, 6 Kasım test verisinde 'İHTİMAL'/'RİYAD' gibi sözcük adlar yüzünden konuldu):
  OCR metninde '<eyer no> <at adı>' (no ile ad arasında ≤3 karakter) bulanık eşleşmesi (difflib oranı ≥0,85, büyük harf). Aynı ad aynı gün iki koşuda varsa koşu belirsiz → sayılmaz.
Ölçüler: at başına kimlikli saniye; koşu başına ≥10 sn'si olan atların oranı; KARAR: koşuların ≥%50'sinde atların ≥%70'i ≥10 sn → etiket aşaması.
Not: 6 Kasım dakikada 1 kare (pilot 1. gün) → saniye yerine kare sayısı; karar yalnız 1 kare/sn günlerinden (7 Kasım ve sonrası) verilir.
Kullanım: python3 data/analiz/t143b_kapsam.py [gün ...]  (boşsa tüm OCR dosyaları)"""
import sys, glob, gzip, json, os, re, difflib
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def program(gun):
    A = json.load(gzip.open(os.path.join(KOK, "data", "atyarisi", f"{gun}.json.gz")))
    P = []
    for h, rs in (A.get("program") or {}).items():
        if h == "karma":
            continue
        for r in rs or []:
            for x in r.get("horses", []) or []:
                if x.get("name") and x.get("number") is not None:
                    P.append((h, int(r["number"]), int(x["number"]), x["name"].upper()))
    say = pd.Series([p[3] for p in P]).value_counts()
    return [p for p in P if say[p[3]] == 1]


def eslesen(t, P):
    t = str(t).upper(); out = set()
    for h, k, no, ad in P:
        for m in re.finditer(rf"(?<!\d){no}(?!\d)", t):
            parca = t[m.end():m.end() + 3 + len(ad) + 2]
            for i in range(0, 4):
                s = parca[i:i + len(ad)]
                if len(s) >= len(ad) - 1 and difflib.SequenceMatcher(None, ad, s).ratio() >= 0.85:
                    out.add((h, k, no)); break
    return out


def gun_ozet(f):
    gun = os.path.basename(f)[:10]; P = program(gun); O = pd.read_csv(f)
    say = {}
    for t in O.metin:
        for key in eslesen(t, P):
            say[key] = say.get(key, 0) + 1
    D = pd.DataFrame([dict(hipodrom=h, kosu=k, no=no, saniye=say.get((h, k, no), 0)) for h, k, no, _ in P])
    return gun, len(O), D


if __name__ == "__main__":
    F = sorted(glob.glob(os.path.join(KOK, "data", "padok_ocr", "*.csv.gz")))
    if len(sys.argv) > 1:
        F = [f for f in F if os.path.basename(f)[:10] in sys.argv[1:]]
    tum = []
    for f in F:
        gun, n, D = gun_ozet(f)
        K = D.groupby(["hipodrom", "kosu"]).agg(at=("no", "size"), gorunen=("saniye", lambda s: (s > 0).sum()), on_sn=("saniye", lambda s: (s >= 10).mean()),
                                                 medyan_sn=("saniye", "median")).reset_index()
        K["gun"] = gun; tum.append(K)
        print(f"== {gun} ({n} kare) | at {len(D)}, en az 1 kimlikli karesi olan {int((D.saniye > 0).sum())}, ≥10 {int((D.saniye >= 10).sum())}")
        print(K.to_string(index=False))
    if tum:
        T = pd.concat(tum); ok = (T.on_sn >= 0.70).mean()
        print(f"\nKARAR ölçüsü: koşuların %{100 * ok:.0f}'inde atların ≥%70'i ≥10 sn (eşik %50) | koşu {len(T)}, gün {T.gun.nunique()}")
