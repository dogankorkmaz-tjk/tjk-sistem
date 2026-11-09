"""Komiser raporu metinlerinden at-bazlı olay bayrakları. Kural-tabanlı (regex), sonuçlara bakılmadan yazıldı.
Çıktı: data/komiser/olaylar.csv.gz  (tarih, hipodrom, kosu, no, at, tur, cumle)
Türler: gec_start (starttan geç çıktı), sakat (koşu sırasında/sonrası topallık, sakatlanma),
        kamci_ceza (kamçı cezası). Engellenme (mağdur at) raporlarda nadiren adıyla geçtiği için KAPSAM DIŞI (suçlu binici adı yazılır). 'çıkan atlar' tablosu ve jokey/antrenör değişikliği DIŞINDA (onlar zaten bizde var)."""
import os, re, glob, gzip, json
import pandas as pd
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOSU = re.compile(r"KOŞU NO:\s*(\d+)")
NO_AT = re.compile(r"(\d+)\s*(?:numaral[ıi]|numaraya|numarada|numara|no'?lu)\s*(?:kayıtlı|kayitli)?\s+([A-ZÇĞİÖŞÜ0-9'’ .\-]+?)\s+isimli")
KURAL = [
    ("gec_start", re.compile(r"boy\s+geç|geç\s+çık|geç\s+çıkış", re.I)),
    ("sakat", re.compile(r"topallık|sakatlan|kanama|kırık|veteriner[^.]*rapor", re.I)),
    ("kamci_ceza", re.compile(r"kamçı", re.I)),
]

def bolumle(metin):
    """KOŞU NO: n başlıklarına göre {kosu: metin}; başlık öncesi (çıkan atlar/değişiklikler) atlanır."""
    parca = KOSU.split(metin); out = {}
    for i in range(1, len(parca) - 1, 2):
        out[int(parca[i])] = out.get(int(parca[i]), "") + " " + parca[i + 1]
    return out

def cumleler(t):
    t = re.sub(r"\s+", " ", t)
    return re.split(r"(?<=[.;])\s+(?=[A-ZÇĞİÖŞÜ0-9])", t)

def oku_tum():
    for f in sorted(glob.glob(os.path.join(KOK, "data", "komiser", "*.jsonl.gz"))):
        for s in gzip.open(f, "rt", encoding="utf-8"): yield json.loads(s)

def cikar(r):
    out = []
    for kosu, t in bolumle(r["metin"]).items():
        # at numarası/adı: cümlede 'N numaralı/numaraya kayıtlı ADI isimli at'; cümle başında numara yoksa önceki cümlenin atı devralınır
        son = None
        for c in cumleler(t):
            m = NO_AT.search(c)
            if m: son = (int(m.group(1)), m.group(2).strip())
            for tur, rx in KURAL:
                if rx.search(c):
                    if son is None: continue
                    out.append({"tarih": r["tarih"], "hipodrom": r["hipodrom"], "kosu": kosu, "no": son[0], "at": son[1], "tur": tur, "cumle": c[:400]})
    return out

if __name__ == "__main__":
    rows = []
    for r in oku_tum(): rows += cikar(r)
    d = pd.DataFrame(rows).drop_duplicates(["tarih", "hipodrom", "kosu", "no", "tur"])
    d.to_csv(os.path.join(KOK, "data", "komiser", "olaylar.csv.gz"), index=False, compression="gzip")
    print("olay:", len(d)); print(d.tur.value_counts().to_string())
