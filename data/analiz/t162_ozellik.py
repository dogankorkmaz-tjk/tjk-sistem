"""T162 (ön kayıt: hipotez_defteri 2026-11-06): video şeridinden sessiz sorun / son bölüm kazancı / tempo baskısı özellikleri (tjk/serit_oz.py).
ekle(d) → d + SV sütunları (at başına önceki 3 koşu ortalaması; şerit yoksa 0 + sv_var)."""
import os, glob, json, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tjk import serit_oz as SO
import t152_ozellik as T

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEAT = ["sv_sorun_n", "sv_sorun_kayip", "sv_son_kazanc", "sv_erken", "sv_orta", "sv_tempo_on", "sv_var"]
_C = {}


def tablo():
    if "S" in _C: return _C["S"]
    R = []
    for f in glob.glob(os.path.join(KOK, "data", "video_seyir", "20*.json")):
        b = os.path.basename(f)[:-5].split("_")
        if len(b) != 3: continue
        try: j = json.load(open(f))
        except Exception: continue
        if j.get("okuyucu") != "rakam1": continue
        O = SO.olcu(j); tp = SO.tempo(j)
        for n, v in O.items():
            R.append(dict(tarih=b[0], hipodrom=b[1], kosu=int(b[2]), no=int(n), _sn=v["sorun_n"], _sk=v["sorun_kayip"], _skz=v["son_kazanc"], _er=v["erken_sira"],
                          _or=v["orta_sira"], _to=(1 - v["erken_sira"]) * ((tp or 1.0) - 1.0)))
    _C["S"] = pd.DataFrame(R).drop_duplicates(["tarih", "hipodrom", "kosu", "no"]); return _C["S"]


def ekle(d):
    d = d.copy(); d["_i"] = np.arange(len(d))
    d = d.merge(tablo(), on=["tarih", "hipodrom", "kosu", "no"], how="left")
    src = ["_sn", "_sk", "_skz", "_er", "_or", "_to"]; out = FEAT[:-1]
    d = T._onceki3(d, src, out)
    d["sv_var"] = d.sv_erken.notna().astype(float)
    for c in out: d[c] = d[c].fillna(0.0)
    return d.sort_values("_i").drop(columns=["_i"]).reset_index(drop=True)
