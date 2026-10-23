"""Nal Sesleri API (nalsesleri.com/api?horse_name=...): atın geçmiş koşuları (kapı, AGF1/AGF2, oran, derece...). Nazik, düzenli, düşük hacimli toplama.
Kurallar: istekler arası >=3 sn; çalışma başına en fazla BUTCE istek; 429/5xx/ardışık hata -> hemen dur; aynı ata en fazla 7 günde bir sorulur.
Çıktı: data/nalsesleri/gecmis.csv.gz (anahtar: race_date, hippodrome_id, race_number, horse_number) ve durum.json {at: son_sorgu_tarihi}.
Not: isimle sorgulandığı için aynı adlı farklı atlar karışabilir; satırlar ham saklanır, kullanımda eşleştirme (tarih+hipodrom+koşu+no) ile doğrulanır."""
import os, re, json, glob, time, datetime
import requests
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASOR = os.path.join(KOK, "data", "nalsesleri")
URL = "https://nalsesleri.com/api"
UA = "GanyanMasasi-arastirma/1.0 (kisisel, dusuk hacim; durum iletisi icin: dogankorkmaz-tjk)"
BEKLE, BUTCE, YENILE_GUN = 3.0, 400, 7


def at_adlari():
    """Sistemdeki gün dosyalarından at adları; en yeni günler önde."""
    sayac, sira = {}, []
    for y in sorted(glob.glob(os.path.join(KOK, "docs", "data", "gun", "*.json")), reverse=True):
        try:
            g = json.load(open(y, encoding="utf-8"))
        except Exception:
            continue
        for h in g.get("hipodromlar", []):
            for k in h.get("kosular", []):
                for a in k.get("atlar", []):
                    ad = (a.get("at") or "").strip()
                    if ad and ad not in sayac:
                        sayac[ad] = 1; sira.append(ad)
    return sira


def calistir(butce=BUTCE):
    os.makedirs(KLASOR, exist_ok=True)
    dy = os.path.join(KLASOR, "durum.json")
    durum = json.load(open(dy, encoding="utf-8")) if os.path.exists(dy) else {}
    bugun = datetime.date.today()
    bekleyen = [a for a in at_adlari() if a not in durum or (bugun - datetime.date.fromisoformat(durum[a])).days >= YENILE_GUN]
    print("sorgulanacak at:", len(bekleyen), "| bu çalışmada en fazla", butce)
    yol = os.path.join(KLASOR, "gecmis.csv.gz")
    satir, n, hata = [], 0, 0
    oturum = requests.Session(); oturum.headers["User-Agent"] = UA
    for ad in bekleyen[:butce]:
        try:
            r = oturum.get(URL, params={"horse_name": ad}, timeout=30)
        except Exception as e:
            hata += 1; print("istek hatası:", ad, repr(e))
            if hata >= 3:
                print("ardışık hata: duruluyor"); break
            time.sleep(BEKLE); continue
        if r.status_code in (429, 500, 502, 503, 504):
            print("sunucu", r.status_code, "-> nazikçe duruluyor"); break
        hata = 0; n += 1
        try:
            j = r.json()
            if j.get("status") == "success":
                for x in j.get("data") or []:
                    x["sorgu_adi"] = ad; satir.append(x)
            durum[ad] = bugun.isoformat()               # "veri yok" yanıtı da kaydedilir; 7 gün sonra tekrar sorulur
        except Exception as e:
            print("yanıt okunamadı:", ad, repr(e))
        time.sleep(BEKLE)
    if satir:
        yeni = pd.DataFrame(satir)
        if os.path.exists(yol):
            yeni = pd.concat([pd.read_csv(yol, dtype=str), yeni.astype(str)], ignore_index=True)
        else:
            yeni = yeni.astype(str)
        yeni = yeni.drop_duplicates(["race_date", "hippodrome_id", "race_number", "horse_number", "horse_name"], keep="last").sort_values(["race_date", "hippodrome_id", "race_number", "horse_number"])
        yeni.to_csv(yol, index=False)
        print("toplam satır:", len(yeni))
    json.dump(durum, open(dy, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("sorgulanan:", n, "| eklenen satır:", len(satir), "| durum kaydı:", len(durum))


if __name__ == "__main__":
    calistir()
