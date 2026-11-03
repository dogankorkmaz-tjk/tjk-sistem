"""data/atyarisi/*.json.gz (yerel ham API arşivi, sonuc/raceMoneys) -> data/odeme/YYYY-MM.csv.gz geri doldurma (ağ yok). Mevcut (tarih,hipodrom,kosu,tur) satırlarına dokunmaz.
python3 data/analiz/odeme_geri_doldur.py [ilk_gün] [son_gün]"""
import os, sys, glob, gzip, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import atyapi as A
from tjk.sonuccsv import _yaz, KOK
ilk = sys.argv[1] if len(sys.argv) > 1 else "0000"; son = sys.argv[2] if len(sys.argv) > 2 else "9999"
dosyalar = [f for f in sorted(glob.glob("data/atyarisi/20*.json.gz")) if ilk <= os.path.basename(f)[:10] <= son]
aylar = {}
for f in dosyalar: aylar.setdefault(os.path.basename(f)[:7], []).append(f)
toplam = 0
for ay, fl in aylar.items():
    rows = []
    for f in fl:
        tarih = os.path.basename(f)[:10]
        try: sonuc = json.load(gzip.open(f)).get("sonuc") or {}
        except Exception as e: print("okunamadı", f, e); continue
        for hip, ko in sonuc.items():
            for k in ko:
                if not any((a.get("order") or 0) > 0 for a in (k.get("horses") or [])): continue
                for m in k.get("raceMoneys") or []:
                    tur = str(m.get("betTypeName") or "").strip().upper()
                    try: tutar = float(str(m.get("prizeText") or "0").replace(".", "").replace(",", "."))
                    except ValueError: continue
                    if tur in A._TUR and m.get("result") and tutar > 0:
                        rows.append({"tarih": tarih, "hipodrom": hip, "kosu": int(k["number"]), "tur": tur, "seq": 0, "kombo": str(m["result"]).strip(), "tutar": tutar})
                    c = A.coklu_satir(tarih, hip, k, m)
                    if c: rows.append(c)
        rows += A.devir_satirlari(tarih, sonuc)
    if not rows: print(ay, "satır yok"); continue
    yol = os.path.join(KOK, "odeme", ay + ".csv.gz")
    if os.path.exists(yol):
        var = pd.read_csv(yol); anahtar = set(zip(var.tarih, var.hipodrom, var.kosu, var.tur)); rows = [r for r in rows if (r["tarih"], r["hipodrom"], r["kosu"], r["tur"]) not in anahtar]
    sayac = {}
    for r in rows:
        if r.pop("_s", False): continue
        a = (r["tarih"], r["hipodrom"], r["kosu"], r["tur"]); r["seq"] = sayac.get(a, 0); sayac[a] = r["seq"] + 1
    n = _yaz("odeme", pd.DataFrame(rows), ["tarih", "hipodrom", "kosu", "tur", "seq", "kombo"]) if rows else 0
    s5 = sum(1 for r in rows if r["tur"].startswith("SIRALI 5")); toplam += n; print(ay, "eklenen", n, "satır; sıralı5", s5, flush=True)
print("toplam eklenen", toplam)
