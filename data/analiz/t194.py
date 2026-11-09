"""T194: komiser raporu bayrakları (geç start / sakatlık / kamçı cezası) → atın SONRAKİ koşusunda piyasaya göre sapma. Ön kayıt: hipotez_defteri T194."""
import os, sys, json
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
import numpy as np, pandas as pd
from tjk import komiser_olay as KO, komiser as KM
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d = _ns["d"].copy()
rows = []
for r in KO.oku_tum(): rows += KO.cikar(r)
ol = pd.DataFrame(rows).drop_duplicates(["tarih", "hipodrom", "kosu", "no", "tur"])
ol["hipodrom"] = ol.hipodrom.map({v: k for k, v in KM.ASCII.items()})
print("olay:", ol.tur.value_counts().to_dict(), "rapor günü-hipodrom:", ol[["tarih", "hipodrom"]].drop_duplicates().shape[0], flush=True)
d = d.sort_values(["at", "tarih", "hipodrom", "kosu"]).reset_index(drop=True)
d["sonraki_tarih"] = d.groupby("at").tarih.shift(-1)
d["s_kaz"] = d.groupby("at").kazandi.shift(-1); d["s_p"] = d.groupby("at").p_piyasa.shift(-1)
d["s_gun"] = (pd.to_datetime(d.sonraki_tarih) - pd.to_datetime(d.tarih)).dt.days
anahtar = d.set_index(["tarih", "hipodrom", "kosu", "no"])
bas = ol.tarih.min(); bit = ol.tarih.max()
pencere = d[(d.tarih >= bas) & d.s_kaz.notna() & d.s_p.notna() & (d.s_gun <= 90)].copy()
pencere["res"] = pencere.s_kaz - pencere.s_p
taban = float(pencere.res.mean()); print("taban (rapor penceresi, tüm sonraki koşular) kazanma−piyasa:", round(taban, 5), "n", len(pencere), flush=True)
rng = np.random.default_rng(1940)
def ga(S, lo, hi, B=20000):
    g = S.groupby("tarih").res.agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values
    n = len(s); idx = rng.integers(0, n, (B, n)); m = s[idx].sum(1) / c[idx].sum(1)
    return float(s.sum() / c.sum()), float(np.percentile(m, lo)), float(np.percentile(m, hi)), int(c.sum())
res = {}
for tur in ("gec_start", "sakat", "kamci_ceza"):
    k = ol[ol.tur == tur][["tarih", "hipodrom", "kosu", "no"]].drop_duplicates()
    k = k.merge(pencere[["tarih", "hipodrom", "kosu", "no", "at", "res", "s_kaz", "s_p", "s_gun"]], on=["tarih", "hipodrom", "kosu", "no"], how="inner")
    if len(k) < 30:
        res[tur] = {"n": int(len(k)), "karar": "n<30: karar yok"}; print(tur, res[tur], flush=True); continue
    g = ga(k, 0.83, 99.17)     # Bonferroni 3 → %98,33
    fark = g[0] - taban
    res[tur] = {"n": g[3], "ort_res": g[0], "ga": [g[1], g[2]], "taban": taban, "fark_taban": fark, "kazanma": float(k.s_kaz.mean()), "piyasa_beklenti": float(k.s_p.mean()), "medyan_gun": float(k.s_gun.median()),
                "karar": "isaret" if (g[1] - taban > 0 or g[2] - taban < 0) else "yok"}
    print(tur, json.dumps(res[tur], ensure_ascii=False), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t194.json"), "w"), indent=1, ensure_ascii=False)
