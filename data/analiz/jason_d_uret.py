"""jason_d.pkl yeniden üretimi (T134-T149 ortak kaynağı). Üretimdeki Jason eğitim hattının (tjk/golge.py egit) tablosu AYNEN:
d = MS.ekle(hazirla(temiz, program, model_v1)) + f_lp2. Yalnız /tmp/claude-0/jason_d.pkl yazar; üretim dosyalarına dokunmaz.
Çalıştır: cd <repo> && python3 data/analiz/jason_d_uret.py   (arka planda: nohup setsid ... > /tmp/jason_d_uret.log)"""
import sys, os, numpy as np, pandas as pd, time
sys.path.insert(0, "."); from tjk import golge as GL, mesafe as MS
from tjk.ozellik import hazirla
from tjk.calistir import yukle_model
def log(*a): print(*a, flush=True)
t0 = time.time(); M = yukle_model()
d = MS.ekle(hazirla(GL._oku("temiz"), GL._oku("program"), M))
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
os.makedirs("/tmp/claude-0", exist_ok=True)
d.to_pickle("/tmp/claude-0/jason_d.pkl")
log("satır", len(d), "sütun", d.shape[1], "tarih", d.tarih.min(), "→", d.tarih.max(), "%d sn" % (time.time() - t0))
feat = M["feat"] + GL.EK + GL.LPEK; log("özellik sayısı (f_lp2 dahil)", len(feat))
x = d[d.kazandi.notna() & d.lp.notna()]
eksik = [f for f in feat if f not in d.columns]; log("tabloda olmayan özellik:", eksik)
for f in feat:
    if f in d.columns:
        s = x[f]; n_nan = int(s.isna().sum()); sd = float(s.std(ddof=0))
        if n_nan or sd == 0: log("  UYARI", f, "NaN", n_nan, "sd", sd)
log("kazandi dolu koşu satırı", len(x), "koşu", x.groupby(["tarih", "hipodrom", "kosu"]).ngroups)
log("bitti")
