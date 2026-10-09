"""TJK 'İdman İstatistikleri' PDF'lerini (Yazdır çıktısı) okuyup data/idman.csv.gz içinde biriktirir.
Kullanım (repo kökünden): python3 -m tjk.idman dosya1.pdf dosya2.pdf ...
Çıktı sütunları: it (idman tarihi), at, irk, cins, yas, m1400..m200 (saniye), durum, hip, pdur, pist, tur, jokey.
Aynı (it, at, hip, tur, jokey, süreler) kaydı tekrar eklenmez."""
import os, re, sys
import pandas as pd

VERI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
YOL = os.path.join(VERI, "idman.csv.gz")
MES = ["1400m", "1200m", "1000m", "800m", "600m", "400m", "200m"]


def _sn(x):
    """'0.38.20' -> 38.2 sn ; '1.01.00' -> 61.0"""
    x = (x or "").strip()
    m = re.fullmatch(r"(\d+)\.(\d\d)\.(\d\d)", x)
    return int(m[1]) * 60 + int(m[2]) + int(m[3]) / 100 if m else None


def oku(pdf):
    import logging, pdfplumber
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    out = []
    with pdfplumber.open(pdf) as p:
        for pg in p.pages:
            for tb in pg.extract_tables():
                for r in tb:
                    if not r or len(r) < 18 or r[0] == "At Adı":
                        continue
                    r = [(c or "").replace("\n", " ").strip() for c in r]
                    m = re.fullmatch(r"(\d\d)\.(\d\d)\.(\d{4})", r[12])
                    if not m:
                        continue
                    out.append({"it": f"{m[3]}-{m[2]}-{m[1]}", "at": r[0], "irk": r[1], "cins": r[2],
                                "yas": int(r[3]) if r[3].isdigit() else None,
                                **{"m" + k[:-1]: _sn(r[4 + i]) for i, k in enumerate(MES)},
                                "durum": r[11], "hip": r[13], "pdur": r[14], "pist": r[15], "tur": r[16], "jokey": r[17]})
    return pd.DataFrame(out)


def ekle(*pdfler):
    yeni = pd.concat([oku(f) for f in pdfler], ignore_index=True) if pdfler else pd.DataFrame()
    eski = pd.read_csv(YOL) if os.path.exists(YOL) else pd.DataFrame()
    tum = pd.concat([eski, yeni], ignore_index=True).drop_duplicates().sort_values(["it", "hip", "at"]).reset_index(drop=True)
    tum.to_csv(YOL, index=False, compression="gzip")
    return len(eski), len(yeni), len(tum), tum


if __name__ == "__main__":
    a, y, t, tum = ekle(*sys.argv[1:])
    print(f"önceki {a}, okunan {y}, toplam {t}")
    print(tum.groupby("it").size().to_string())
