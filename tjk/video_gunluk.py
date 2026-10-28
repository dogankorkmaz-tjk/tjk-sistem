"""TJK yarış videolarını (video-cdn.tjk.org, herkese açık mobil sürüm) indirip tjk.video_seyir ile işler, videoyu siler.
Kullanım: python3 -m tjk.video_gunluk YYYY-MM-DD [YYYY-MM-DD ...]   (GitHub Actions'ta çalışır; kalıp: YYAAGG<hipkodu><koşu>_m.mp4)
Çıktı: data/video_seyir/<tarih>_<hip>_<kosu>.json  ve  data/video_seyir/_rapor.csv (her deneme: durum, kare, doğrulama)."""
import os, sys, csv, json, time, subprocess, tempfile, datetime as dt
from multiprocessing import Pool
from . import gelen, video_seyir

KOK = gelen.KOK
CDN = "https://video-cdn.tjk.org/videoftp/{y}/{a}/{g}{h}{k}_m.mp4"
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
RAPOR = os.path.join(KOK, "data", "video_seyir", "_rapor.csv")
BASLIK = ["tarih", "hip", "kosu", "durum", "at_sayisi", "kare", "gecerli_kare", "bolum_n", "top3_dogru", "sn"]


def _indir(url, yol):
    r = subprocess.run(["curl", "-s", "-m", "180", "-A", UA, "-e", "https://www.tjk.org/", "-o", yol, "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip() == "200" and os.path.getsize(yol) > 100000


def _dogrula(c, tarih, hip, kosu):
    """Videonun son geçerli karesindeki ilk 3 ile resmi sonuç (data/temiz) ilk 3'ünü karşılaştırır (sonuç varsa)."""
    import pandas as pd
    f = os.path.join(KOK, "data", "temiz", tarih[:7] + ".csv.gz")
    if not os.path.exists(f):
        return ""
    d = pd.read_csv(f)
    d = d[(d.tarih == tarih) & (d.hipodrom.map(gelen._ascii) == hip) & (d.kosu == kosu) & d.sira.notna()].sort_values("sira")
    if len(d) < 3:
        return ""
    gercek = [int(x) for x in d.no.head(3)]
    z = [x for x in c["zaman"] if x["sira"]]
    if not z:
        return "0"
    return str(int(sorted(z[-1]["sira"][:3]) == sorted(gercek)))


def isle(args):
    tarih, hip_kod, kosu = args
    hip = gelen.KOD[hip_kod]
    ad = f"{tarih}_{hip}_{kosu}"
    cikti = os.path.join(KOK, "data", "video_seyir", ad + ".json")
    if os.path.exists(cikti):
        return [tarih, hip, kosu, "var", "", "", "", "", "", ""]
    t0 = time.time()
    atlar = gelen._atlar(tarih, hip, kosu)
    if not atlar:
        return [tarih, hip, kosu, "at_yok", "", "", "", "", "", ""]
    g = tarih[2:4] + tarih[5:7] + tarih[8:10]
    with tempfile.TemporaryDirectory() as k:
        yol = os.path.join(k, "v.mp4")
        if not _indir(CDN.format(y=tarih[:4], a=tarih[5:7], g=g, h=hip_kod, k=kosu), yol):
            return [tarih, hip, kosu, "video_yok", len(atlar), "", "", "", "", ""]
        try:
            c = video_seyir.isle(yol, atlar, ad)
        except Exception as e:
            return [tarih, hip, kosu, "hata:" + str(e)[:60].replace(",", ";"), len(atlar), "", "", "", "", ""]
    return [tarih, hip, kosu, "tamam", len(atlar), c["kare"], c["gecerli_kare"], len(c.get("bolum", {})), _dogrula(c, tarih, hip, kosu), round(time.time() - t0)]


def gun_isleri(tarih):
    """O gün CDN'de bulunan (hipodrom kodu, koşu) çiftleri: HEAD ile tarar."""
    g = tarih[2:4] + tarih[5:7] + tarih[8:10]
    isler = []
    for h in gelen.KOD:
        for k in range(1, 15):
            u = CDN.format(y=tarih[:4], a=tarih[5:7], g=g, h=h, k=k)
            c = subprocess.run(["curl", "-s", "-o", "/dev/null", "-I", "-m", "15", "-w", "%{http_code}", u], capture_output=True, text=True).stdout.strip()
            if c == "200":
                isler.append((tarih, h, k))
            elif k > 3:
                break
    return isler


if __name__ == "__main__":
    gunler = sys.argv[1:]
    os.makedirs(os.path.dirname(RAPOR), exist_ok=True)
    yeni = not os.path.exists(RAPOR)
    with open(RAPOR, "a", newline="") as f:
        w = csv.writer(f)
        if yeni:
            w.writerow(BASLIK)
        for t in gunler:
            isler = gun_isleri(t)
            with Pool(3) as p:
                for r in p.imap_unordered(isle, isler):
                    w.writerow(r); f.flush()
            print(t, len(isler), "video", flush=True)
