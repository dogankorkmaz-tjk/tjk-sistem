"""Devirli havuz kaydi ve beklenen getiri tablosu.
Kayit:   python -m tjk.havuz_canli ekle TARIH HIPODROM KOSU TUR TUTAR [DEVIR]   (TUR: sirali5, 7li, 6li ...)
Tablo:   python -m tjk.havuz_canli ev DEVIR_TL [SATIS_TL]
Rastgele (beceriden bagimsiz) alicinin beklenen geri donusu ~ NET_ORAN + devir/satis (kesintiden devir muaf).
Satis bilinmiyorsa gecmis ilk-adim devirlerinin medyanindan (net havuz ~ 0,7 x satis) tahmin edilir."""
import os, sys, json, glob
import numpy as np, pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASOR = os.path.join(KOK, "data", "havuz_canli")
NET = 0.70


def kaydet(tarih, hip, kosu, tur, tutar, devir=None, not_=""):
    os.makedirs(KLASOR, exist_ok=True)
    yol = os.path.join(KLASOR, f"{tarih}.json")
    L = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else []
    L.append({"hipodrom": hip, "kosu": int(kosu), "tur": tur, "tutar": float(tutar), "devir": float(devir) if devir else None, "not": not_})
    json.dump(L, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def satis_dagilimi():
    """Gecmis ilk-adim siralı 5'li devirlerinden satis tahmini (net havuz / 0,7)."""
    o = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz"))])
    b = o[o.tur.str.contains("SIRALI 5")].sort_values(["hipodrom", "tarih", "kosu"]).copy()
    b["devir"] = b.tur.str.contains("DEVİR"); b["onceki"] = b.groupby("hipodrom").devir.shift(1).fillna(False)
    x = b[b.devir & ~b.onceki].tutar / NET
    return x.quantile([.1, .25, .5, .75, .9]).to_dict()


def ev_tablosu(devir, satis=None):
    S = {"?": satis} if satis else {f"q{int(k*100)}": v for k, v in satis_dagilimi().items()}
    return {k: round(NET + devir / v, 2) for k, v in S.items()}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "ekle":
        kaydet(*a[1:6], devir=a[6] if len(a) > 6 else None)
    elif a and a[0] == "ev":
        print(ev_tablosu(float(a[1]), float(a[2]) if len(a) > 2 else None))
    else:
        print(__doc__)
