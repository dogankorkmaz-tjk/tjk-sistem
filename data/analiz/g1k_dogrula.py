"""Benter-K üretim özellikleri (tjk/g1k.py) = araştırma özellikleri (t152_ozellik.py, T155'te kullanılan) mı? Aynı d (jason_d.pkl) üzerinde sütun sütun.
Önkoşul: t146_hazirla.py ile /tmp/claude-0/ay_oz.pkl taze üretilmiş olmalı (araştırma tarafı onu okur)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "data/analiz")
import t152_ozellik as T
from tjk import g1k as K
d = pd.read_pickle("/tmp/claude-0/jason_d.pkl").reset_index(drop=True)
P = K.ozellik_ekle(d)
kotu = 0
for g in ("OV", "V2", "SYG"):
    R = T.ekle(d, g)
    for c in K.OZ[g]:
        a, b = P[c].values.astype(float), R[c].values.astype(float); m = np.nanmax(np.abs(a - b)) if len(a) else 0
        ok = np.allclose(a, b, atol=1e-9, equal_nan=True); kotu += not ok
        print(f"{g:4s} {c:15s} en büyük fark {m:.2e} {'TAMAM' if ok else 'FARKLI'}")
print("SONUÇ:", "BİREBİR" if kotu == 0 else f"{kotu} sütun farklı", "|", len(d), "satır")
