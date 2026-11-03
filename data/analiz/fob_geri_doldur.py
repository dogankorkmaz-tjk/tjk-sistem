"""data/atyarisi ham arşivinden sabit ihtimalli kazananlar (ilk/son oran) -> data/sabit_kazanan/YYYY-MM.csv.gz. python3 data/analiz/fob_geri_doldur.py"""
import os, sys, glob, gzip, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import atyapi as A
top = 0
for f in sorted(glob.glob("data/atyarisi/20*.json.gz")):
    t = os.path.basename(f)[:10]
    try: s = json.load(gzip.open(f)).get("sonuc") or {}
    except Exception as e: print("okunamadı", f, e); continue
    n = A.fob_yaz(t, s); top += n
print("toplam", top)
