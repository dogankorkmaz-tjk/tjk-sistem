"""Sistem sağlığı (6 Kasım 2026): 'hata vermeden yanlış çalışan' durumları her çalışmada yakalamak için veri düzeyi kontroller.
Neden: 22 Ekim–6 Kasım arasında agftablosu engeli (sonuç/program/altılı yapısı durdu) ve sabah yazımının Benter puanlarını silmesi
haftalarca fark edilmedi; hatalar yalnız Actions günlüğüne yazılıyordu. Çıktı: docs/data/saglik.json (site: Bugün üstünde uyarı + Diğer → Sistem sağlığı).
Kullanım: from tjk import saglik; saglik.kontrol(obj)   (calistir sabah/gece/güncelleme sonunda; asla hata fırlatmaz)."""
import os, json, glob, gzip, datetime as dt

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data"); SITE = os.path.join(KOK, "docs", "data")


def _son_tarih_csv(klasor, sutun="tarih"):
    import pandas as pd
    fs = sorted(glob.glob(os.path.join(VERI, klasor, "*.csv.gz")))
    if not fs: return None
    try:
        x = pd.read_csv(fs[-1], usecols=[sutun], low_memory=False)
        return str(x[sutun].max())
    except Exception:
        return None


def _gun_farki(a, b):
    try: return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days
    except Exception: return None


def _ekle(L, ad, durum, detay):
    L.append({"ad": ad, "durum": durum, "detay": detay})


def kontrol(obj=None, bugun=None):
    L = []
    try:
        from . import ortak as O
        bugun = bugun or O.tr_simdi().date().isoformat()
    except Exception:
        bugun = bugun or dt.date.today().isoformat()
    dun = (dt.date.fromisoformat(bugun) - dt.timedelta(days=1)).isoformat()
    # 1) sonuç/temiz/program tazeliği (TJK neredeyse her gün koşu var; 2 günden eski = sorun)
    for k in ("sonuclar", "temiz", "program"):
        try:
            s = _son_tarih_csv(k); f = _gun_farki(s, bugun) if s else None
            if f is None: _ekle(L, f"veri: {k}", "hata", "okunamadı")
            else: _ekle(L, f"veri: {k}", "ok" if f <= 2 else ("uyari" if f <= 3 else "hata"), f"son gün {s} ({f} gün önce)")
        except Exception as e:
            _ekle(L, f"veri: {k}", "hata", repr(e)[:120])
    # 2) diğer akışlar
    for k, sut, esik in (("odeme", "tarih", 2), ("agf", "tarih", 2), ("galop", "it", 3)):
        try:
            s = _son_tarih_csv(k, sut); f = _gun_farki(s, bugun) if s else None
            _ekle(L, f"veri: {k}", "ok" if (f is not None and f <= esik) else "uyari", f"son gün {s}" + (f" ({f} gün önce)" if f is not None else ""))
        except Exception as e:
            _ekle(L, f"veri: {k}", "uyari", repr(e)[:120])
    # 3) atyarisi arşivi: dün tam mı
    try:
        from . import atyarisi_arsiv as AR
        y = os.path.join(VERI, "atyarisi", dun + ".json.gz")
        if os.path.exists(y):
            tam = AR.tam_mi(json.load(gzip.open(y, "rt")))
            _ekle(L, "atyarisi arşivi (dün)", "ok" if tam else "uyari", "tam" if tam else "sonuçları eksik")
        else:
            _ekle(L, "atyarisi arşivi (dün)", "uyari", "dosya yok")
    except Exception as e:
        _ekle(L, "atyarisi arşivi (dün)", "uyari", repr(e)[:120])
    # 4) model eğitim tarihleri
    for ad, yol, anahtar, esik in (("Jason eğitimi", "model_aday.json", "egitim_son_tarih", 3), ("Benter eğitimi", "analiz/g1v3_katsayi.json", "egitim", 3),
                                   ("piyasasız model eğitimi", "analiz/g1v3_nolp_katsayi.json", "egitim", 3)):
        try:
            d = json.load(open(os.path.join(VERI, yol))); s = str(d.get(anahtar)); f = _gun_farki(s, bugun)
            _ekle(L, ad, "ok" if (f is not None and f <= esik) else "uyari", f"{s}" + (f" ({f} gün önce)" if f is not None else ""))
            if ad == "piyasasız model eğitimi":
                _ekle(L, "piyasasız model galop", "ok" if d.get("galop") else "uyari", "var" if d.get("galop") else "YOK (T153'e göre olmalı)")
        except Exception as e:
            _ekle(L, ad, "uyari", repr(e)[:120])
    # 5) bugünkü gün dosyası: puan kapsamı, sıra üstelleri, altılı yapısı
    try:
        if obj is None:
            p = os.path.join(SITE, "gun", bugun + ".json")
            obj = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
        if obj and obj.get("tarih") == bugun and obj.get("hipodromlar"):
            A = [a for h in obj["hipodromlar"] for k in h["kosular"] if not k.get("sonuc") for a in k["atlar"] if not a.get("kosmaz")]
            if A:
                for key, ad in (("z2", "Jason puanı (z2)"), ("z6", "Benter puanı (z6)"), ("z7", "piyasasız puan (z7)")):
                    pc = 100.0 * sum(1 for a in A if a.get(key) is not None) / len(A)
                    _ekle(L, ad, "ok" if pc >= 95 else ("uyari" if pc >= 50 else "hata"), f"kapsam %{pc:.0f} (başlamamış koşulardaki atlar)")
                _ekle(L, "Benter sıra üstelleri (a_g1)", "ok" if obj.get("a_g1") else "hata", "var" if obj.get("a_g1") else "YOK — sitede sıralı bahisler çıkmaz")
            al = sum(1 for h in obj["hipodromlar"] if h.get("altili"))
            _ekle(L, "altılı yapısı", "ok" if al else "uyari", f"{al}/{len(obj['hipodromlar'])} hipodromda")
    except Exception as e:
        _ekle(L, "gün dosyası", "uyari", repr(e)[:120])
    sira = {"ok": 0, "uyari": 1, "hata": 2}
    genel = max((x["durum"] for x in L), key=lambda d: sira[d]) if L else "ok"
    out = {"tarih": bugun, "zaman": dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).strftime("%Y-%m-%d %H:%M TR"), "genel": genel, "kontroller": L}
    try:
        os.makedirs(SITE, exist_ok=True); json.dump(out, open(os.path.join(SITE, "saglik.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:
        print("sağlık yazma hatası:", repr(e))
    for x in L:
        if x["durum"] != "ok": print(f"SAĞLIK {x['durum'].upper()}: {x['ad']} — {x['detay']}")
    return out


if __name__ == "__main__":
    import sys; sys.path.insert(0, KOK)
    o = kontrol(); print(o["genel"]); [print(" ", x["durum"], x["ad"], "-", x["detay"]) for x in o["kontroller"]]
