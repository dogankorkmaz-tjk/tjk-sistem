"""Bugünün atları için son koşularındaki spiker notları (tjk/spiker_ayikla). Her ata a["spiker"] = [{"t": "05.11 Ankara 4.", "o": "2 boy geç çıktı; erken 6./9"}...]
(en yeni önce, son 3 koşudan transkripti olanlar). Kaynak: data/temiz (at geçmişi: tarih, hipodrom, koşu, no) + data/spiker transkriptleri.
Çağrı: calistir sabah (try/except). Bilgi amaçlı; modele girmez (model testi T160 ön kayıtlı)."""
import os, glob, gzip, json
import pandas as pd
from . import spiker_ayikla as SA
from . import ortak as O

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AD = {"gec_cikis": "geç çıktı", "avantaj_kaybi": "avantaj kaybetti", "sikisma": "sıkıştı/kapandı", "dis_acilma": "dışa açıldı",
      "dusme_tokezleme": "tökezledi/düştü", "huysuz": "huysuzlandı", "lehine": "koşu lehine aktı"}


def _transkript(t, hip, k):
    f = os.path.join(KOK, "data", "spiker", t[:7], f"{t}_{hip}_{k}.json.gz")
    return json.load(gzip.open(f)) if os.path.exists(f) else None


def notlar(at_adlari, bugun, n=3):
    aylar = sorted(glob.glob(os.path.join(KOK, "data", "temiz", "20*.csv.gz")))[-8:]
    T = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "at", "kosmadi"]) for f in aylar])
    T = T[(T.tarih < bugun) & (T.kosmadi != True) & T["at"].isin(at_adlari)].sort_values("tarih", ascending=False)
    out = {}
    for at, g in T.groupby("at"):
        L = []
        for r in g.head(n).itertuples():
            j = _transkript(r.tarih, r.hipodrom, int(r.kosu))
            if not j: continue
            no = int(r.no); O_ = SA.olaylar(j["seg"]).get(no, []); K = SA.konum(j["seg"], j["sure"]).get(no, {})
            par = []
            for tur, s, boy, _ in O_:
                par.append((f"{boy:g} boy " if boy else "") + AD.get(tur, tur))
            if "erken" in K:
                say = sum(1 for v in SA.konum(j["seg"], j["sure"]).values() if "erken" in v)
                par.append(f"erken {K['erken']}./{say}")
            L.append({"t": f"{r.tarih[8:10]}.{r.tarih[5:7]} {O.AD.get(r.hipodrom, r.hipodrom)} {int(r.kosu)}.", "o": "; ".join(par) or "olay yok"})
        if L: out[at] = L
    return out


def ekle(obj):
    adlar = {a["at"] for h in obj["hipodromlar"] for k in h["kosular"] for a in k["atlar"] if a.get("at")}
    N = notlar(adlar, obj["tarih"]); say = 0
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            for a in k["atlar"]:
                if a.get("at") in N: a["spiker"] = N[a["at"]]; say += 1
    return say
