"""İkinci piyasa + piyasa zamanlaması (24 Ekim 2026): atyarisi'nin Türk koşuları için
  FobProbables  -> sabit ihtimalli (TJK'nın belirlediği sabit oran; betTypeId 1001 ganyan, 1002 plase, ...)
  Probables     -> canlı muhtemel (havuz) oranları
tek atlı satırlarını (runner2 boş) zaman damgasıyla data/piyasa/<gün>.csv.gz'ye yalnız DEĞİŞTİKÇE ekler.
Amaç: (1) kapanıştan önce ne zaman hangi oran vardı, (2) sabit ihtimalli ile havuz kapanışı arasındaki fark bilgi taşıyor mu.
Nazik: program başına 2 istek, her çalışmada."""
import os, time, datetime as dt
import pandas as pd
import requests
from . import ortak as O
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://tjkbulten.atyarisi.com/api/v1/"
H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek)", "Accept": "application/json", "Origin": "https://www.atyarisi.com", "Referer": "https://www.atyarisi.com/"}
SUT = ["saat", "kaynak", "hipodrom", "kosu", "tip", "no", "oran"]


def _hip(ad):
    k = str(ad or "").strip().translate(O.TR).lower()
    for h, a in O.AD.items():
        if a.translate(O.TR).lower() == k or h == k:
            return h
    return None


def _al(yol, **p):
    r = requests.get(B + yol, params=p, headers=H, timeout=25)
    r.raise_for_status()
    return r.json()


def topla(tarih):
    yol = os.path.join(KOK, "data", "piyasa", tarih + ".csv.gz")
    eski = pd.read_csv(yol) if os.path.exists(yol) else pd.DataFrame(columns=SUT)
    son = {(r.kaynak, r.hipodrom, r.kosu, r.tip, r.no): r.oran for r in eski.itertuples()}
    saat = O.tr_simdi().strftime("%H:%M:%S"); yeni = []
    try:
        liste = _al("ProgramHippodromes", date=tarih).get("d") or []
    except Exception as e:
        print("piyasa liste hatası:", repr(e)); return 0
    for h in liste:
        hi = h.get("hippodrome") or {}
        hid = None if hi.get("isForeign") else (_hip(hi.get("place")) or _hip(hi.get("code")))
        if not hid or hid not in O.TRH:
            continue
        for kaynak, ad in (("F", "FobProbables"), ("M", "Probables")):
            time.sleep(1.5)
            try:
                yar = ((_al(ad, programId=h["id"]).get("d") or {}).get("races")) or []
            except Exception as e:
                print("piyasa", hid, ad, "hata:", repr(e)); continue
            for y in yar:
                for b in y.get("bets", []):
                    for p in b.get("probables", []):
                        if p.get("runner2") not in ("", None):
                            continue
                        try:
                            no = int(p["runner1"]); o = float(p["ganyan"])
                        except Exception:
                            continue
                        anah = (kaynak, hid, int(y["raceNo"]), int(b["betTypeId"]), no)
                        if o and son.get(anah) != o:
                            son[anah] = o; yeni.append(dict(saat=saat, kaynak=kaynak, hipodrom=hid, kosu=anah[2], tip=anah[3], no=no, oran=o))
    if yeni:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        pd.concat([eski, pd.DataFrame(yeni)], ignore_index=True).to_csv(yol, index=False, compression="gzip")
    return len(yeni)
