"""agftablosu yedeği: data/atyarisi arşivinden (TJK resmî atyarisi API'si) sonuclar/temiz/program satırları, agftablosu biçiminde.

Neden (6 Kasım 2026): agftablosu 22 Ekim'den beri Cloudflare engelinde; gece işi sonuç/program alamadığı için temiz/sonuclar/program
21 Ekim'de durdu ve Jason her gece aynı veriyle eğitildi. Bu modül eksik kalan (tarih, hipodrom) çiftlerini arşivden doldurur.

Biçim kuralları (agftablosu satırlarıyla örtüşen 8 günde alan alan karşılaştırıldı, 2023-07..2026-09, bkz. hipotez defteri 6 Kasım):
- sonuclar: sira/jokey/kilo/derece_sn/kosmadi/hnd birebir (derece "1.18.71" -> 78.71 sn; hnd boş -> 0). kosmadi = status False VEYA
  derece "0" ve sırasız; koşmaz atın ganyanı boş bırakılır (piyasa olasılığına girmez, eski temiz ile aynı). At adı: agftablosu nadiren
  "AD(2) (USA)" yazıyordu (1775 satırda 3), API yalnız "AD" verir.
- program: p_at, yas_ham, baba (yalnız baba adı; boşluklar sadeleştirilir, "A. P." -> "A.P."), st, hk birebir;
  son6 yalnız rakam (agftablosu yıl ayracı "-" içerir; özellik kodu zaten rakam dışını siler); kgs 127'de kırpılır (agftablosu tavanı).
- sahip = owner.shortName, antrenor = coach.shortName (agftablosu ile aynı yazım). Arşiv yarıştan aylar sonra alınmışsa API GÜNCEL
  sahip/antrenörü verir (örtüşen günlerde farkların 43/48'i atın sonraki antrenörüydü); bu yüzden yalnız yarış gününe yakın alınmış
  arşiv kullanılmalı (gece doldurma bunu sağlar).
- apranti = jockey.apprentice (agftablosu çırak işaretini ~%5-15 satırda kaçırıyordu; API tutarlı).
- fark (bitiş farkı) tablosu doldurulmaz.
Kullanım: python -m tjk.atyarisi_gecmis doldur BAS BIT [--yaz]   (--yaz yoksa yalnız rapor)"""
import os, re, sys, json, gzip, datetime
import numpy as np
from . import ortak as O

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KL = os.path.join(KOK, "data", "atyarisi")


def _derece(s):
    m = re.match(r"^\s*(\d+)[.:](\d{2})[.:](\d{1,2})\s*$", str(s or ""))
    return int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / 100 if m else np.nan


def _baba(s):
    s = re.sub(r"\.\s+(?=[A-ZÇĞİÖŞÜ]\.)", ".", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def _int(x):
    s = str(x if x is not None else "").strip()
    return int(s) if s.isdigit() else 0


def _say(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def oku(t, getir=True):
    """Arşiv günü (sonuç tam değilse ve getir=True ise atyarisi'nden yeniden alır). Yoksa None."""
    from . import atyarisi_arsiv as AR
    yol = os.path.join(KL, t + ".json.gz")
    o = json.load(gzip.open(yol, "rt")) if os.path.exists(yol) else None
    if getir and (o is None or not AR.tam_mi(o)):
        try:
            print("  atyarisi arşivi alınıyor:", t, AR.arsivle(t))
        except Exception as e:
            print("  atyarisi arşiv hatası:", t, repr(e))
        o = json.load(gzip.open(yol, "rt")) if os.path.exists(yol) else None
    return o


def satirlar(t, getir=True):
    """-> (sonuc_satirlari, program_satirlari); yalnız TÜM koşularının sonucu belli olan Türkiye hipodromları."""
    o = oku(t, getir)
    if not o:
        return [], []
    S, P, tamam = [], [], set()
    for hid, kos in (o.get("sonuc") or {}).items():
        if hid not in O.TRH or not kos:
            continue
        if not all(any((a.get("order") or 0) > 0 for a in (k.get("horses") or [])) or k.get("canceledRace") for k in kos):
            continue                                   # hipodromun sonuçları eksik: hiç yazma (sonraki gece tekrar denenir)
        tamam.add(hid)
        for k in kos:
            if k.get("canceledRace"):
                continue
            for a in k.get("horses") or []:
                j = a.get("jockey") or {}
                # koşmaz: status False VEYA (derece "0" ve sırasız); derecesiz bitiren "Drcsz" koşmuş sayılır (örtüşen günlerde 37/37 agftablosu ile aynı)
                kosmaz = (not a.get("status", True)) or (str(a.get("degree") or "").strip() == "0" and not (a.get("order") or 0))
                S.append({"tarih": t, "hipodrom": hid, "kosu": int(k["number"]), "sira": int(a.get("order") or 0), "no": int(a["number"]),
                          "at": (a.get("name") or "").strip(), "jokey": (j.get("name") or "").strip(), "apranti": bool(j.get("apprentice")),
                          "kilo": _say(a.get("weight")), "derece_sn": _derece(a.get("degree")), "kosmadi": kosmaz,
                          "ganyan": np.nan if kosmaz or not a.get("ganyan") else float(a["ganyan"]), "hnd": _int(a.get("handicap"))})
    for hid, kos in (o.get("program") or {}).items():
        if hid not in tamam:
            continue
        for k in kos:
            for a in k.get("horses") or []:
                p = a.get("parents") or {}
                kg = _say(a.get("kgs"))
                P.append({"tarih": t, "hipodrom": hid, "kosu": int(k["number"]), "no": int(a["number"]), "p_at": (a.get("name") or "").strip(),
                          "yas_ham": re.sub(r"\s+", " ", a.get("age") or "").strip(), "baba": _baba((p.get("father") or {}).get("name")),
                          "sahip": ((a.get("owner") or {}).get("shortName") or "").strip(), "antrenor": ((a.get("coach") or {}).get("shortName") or "").strip(),
                          "st": _say(a.get("start")), "hk": _int(a.get("handicap")),
                          "son6": "".join(re.sub(r"\D", "", str(x.get("result", ""))) for x in (a.get("last6") or [])),
                          "kgs": min(kg, 127.0) if kg == kg else np.nan})
    return S, P


def eksik_doldur(gunler, yaz=False, getir=True):
    """gunler: ISO tarih listesi. sonuclar'da OLMAYAN (tarih, hipodrom) çiftlerini arşivden ekler (sonuclar, temiz, program)."""
    import pandas as pd
    from .calistir import oku as C_oku, ekle
    sn = C_oku("sonuclar")
    var = set(zip(sn.tarih, sn.hipodrom))
    YS, YP = [], []
    for t in gunler:
        S, P = satirlar(t, getir)
        hs = sorted({r["hipodrom"] for r in S if (t, r["hipodrom"]) not in var})
        YS += [r for r in S if r["hipodrom"] in hs]; YP += [r for r in P if r["hipodrom"] in hs]
        print(" ", t, "eklenecek hipodrom:", hs, "| sonuç", sum(r["hipodrom"] in hs for r in S), "program", sum(r["hipodrom"] in hs for r in P))
    if YS and yaz:
        ns, npg = pd.DataFrame(YS), pd.DataFrame(YP)
        ekle("sonuclar", ns, sn.columns)
        ekle("temiz", O.temiz_yap(ns), C_oku("temiz").columns)
        if len(npg):
            ekle("program", npg, C_oku("program").columns)
        print("atyarisi yedeğinden EKLENDİ: sonuç", len(ns), "program", len(npg))
    return YS, YP


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "doldur":
        a, b = datetime.date.fromisoformat(sys.argv[2]), datetime.date.fromisoformat(sys.argv[3])
        gl = [(a + datetime.timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]
        eksik_doldur(gl, yaz="--yaz" in sys.argv, getir="--getirme" not in sys.argv)
    else:
        print(__doc__)
