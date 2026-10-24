"""Kapı özellikleri (ön kayıt hipotez_defteri 2026-10-24 18:55). out=(kapı−1)/(n−1); f_kk/f_ko/f_ku = out×[mesafe bandı]. JK=1 ise f_jk = out × jokeyin ÖNCEKİ AYLARDA öğrenilmiş eğimi."""
import numpy as np, pandas as pd
def uygula(d):
    A = pd.read_pickle("/tmp/claude-0/arsiv_kapi.pkl").drop_duplicates(["tarih", "hip", "kosu", "no"])
    d = d.merge(A.rename(columns={"hip": "hipodrom"})[["tarih", "hipodrom", "kosu", "no", "start", "n_k", "D"]], on=["tarih", "hipodrom", "kosu", "no"], how="left")
    out = ((d.start - 1) / (d.n_k - 1).clip(lower=1)).fillna(0.5).values - 0.5 * (d.start.isna().values)  # eksik: 0
    out = np.where(d.start.isna(), 0.0, out)
    D = d.D.values
    d["f_kk"] = np.where(D < 1400, out, 0.0); d["f_ko"] = np.where((D >= 1400) & (D < 1800), out, 0.0); d["f_ku"] = np.where(D >= 1800, out, 0.0)
    d["out_k"] = out
    return d
