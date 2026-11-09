"""TJK Komiserler Kurulu günlük raporları (PDF) → metin arşivi. Nazik: tek bağlantı, istekler arası 4 sn, 404 = rapor yok (atlanır).
Kullanım (repo kökünden):
  python3 -m tjk.komiser indeks            # data/gozlem/komiser/indeks.csv içindeki bağlantılar (yalnız arşivde olmayanlar)
  python3 -m tjk.komiser gun [GUN_GERI=4]  # son N günün raporları (program dosyasındaki hipodromlar), her seferinde yeniden çekilir (ek raporlar sonradan eklenir)
  python3 -m tjk.komiser geri BAS BIT [MAX=400]  # tarih aralığı (program dosyasındaki gün+hipodromlar), arşivde olmayanlar
Çıktı: data/komiser/YYYY-MM.jsonl.gz  satır = {tarih, hipodrom, url, sayfa, metin, ozet(sha1)} ; anahtar (tarih, hipodrom), metin değişirse güncellenir."""
import os, io, re, sys, json, gzip, time, glob, hashlib, datetime as dt
import requests

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(KOK, "data", "komiser")
KOD = {"Adana": 1, "İzmir": 2, "İstanbul": 3, "Bursa": 4, "Ankara": 5, "Şanlıurfa": 6, "Elazığ": 7, "Diyarbakır": 8, "Kocaeli": 9, "Antalya": 10}
ASCII = {"adana": "Adana", "izmir": "İzmir", "istanbul": "İstanbul", "bursa": "Bursa", "ankara": "Ankara", "sanliurfa": "Şanlıurfa",
         "elazig": "Elazığ", "diyarbakir": "Diyarbakır", "kocaeli": "Kocaeli", "antalya": "Antalya"}
BEKLE = 4.0
H = {"User-Agent": "Mozilla/5.0 (tjk-sistem arastirma; nazik tarama)"}


def url(tarih, hip):
    t = tarih.replace("-", "")
    return f"https://medya-cdn.tjk.org/raporftp/YarisBilgileri/{tarih[:4]}/{t}{KOD[hip]}.pdf"


def _yol(ay): return os.path.join(DIR, f"{ay}.jsonl.gz")


def yukle(ay):
    p = _yol(ay); d = {}
    if os.path.exists(p):
        for s in gzip.open(p, "rt", encoding="utf-8"):
            r = json.loads(s); d[(r["tarih"], r["hipodrom"])] = r
    return d


def kaydet(ay, d):
    os.makedirs(DIR, exist_ok=True)
    with gzip.open(_yol(ay), "wt", encoding="utf-8") as f:
        for k in sorted(d): f.write(json.dumps(d[k], ensure_ascii=False) + "\n")


def metin(pdf_bytes):
    import logging, pdfplumber
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as p:
        return len(p.pages), "\n".join((pg.extract_text() or "") for pg in p.pages)


def cek(tarih, hip, oturum):
    u = url(tarih, hip)
    try:
        r = oturum.get(u, headers=H, timeout=40)
    except Exception as e:
        return None, f"HATA {e}"
    if r.status_code == 404: return None, "404"
    if r.status_code != 200: return None, f"HTTP {r.status_code}"
    try:
        n, t = metin(r.content)
    except Exception as e:
        return None, f"PDF-HATA {e}"
    return {"tarih": tarih, "hipodrom": hip, "url": u, "sayfa": n, "metin": t, "ozet": hashlib.sha1(t.encode()).hexdigest()[:12]}, "ok"


def isle(hedefler, yenile):
    """hedefler: [(tarih, hip)] ; yenile=False ise arşivde olanlar atlanır."""
    oturum = requests.Session(); ay_d = {}; yeni = guncel = yok = hata = 0; degisti = set()
    for i, (t, h) in enumerate(hedefler):
        ay = t[:7]
        if ay not in ay_d: ay_d[ay] = yukle(ay)
        if not yenile and (t, h) in ay_d[ay]: continue
        r, durum = cek(t, h, oturum)
        if r is None:
            if durum == "404": yok += 1
            else: hata += 1; print("!", t, h, durum, flush=True)
        else:
            eski = ay_d[ay].get((t, h))
            if eski is None: yeni += 1
            elif eski["ozet"] != r["ozet"]: guncel += 1
            if eski is None or eski["ozet"] != r["ozet"]: ay_d[ay][(t, h)] = r; degisti.add(ay)
        if (i + 1) % 50 == 0:
            for a in degisti: kaydet(a, ay_d[a])
            degisti = set(); print(f"{i+1}/{len(hedefler)} yeni {yeni} güncel {guncel} yok {yok} hata {hata}", flush=True)
        time.sleep(BEKLE)
    for a in degisti: kaydet(a, ay_d[a])
    print(f"BİTTİ: hedef {len(hedefler)} yeni {yeni} güncellenen {guncel} yok(404) {yok} hata {hata}")


def program_gunleri():
    import pandas as pd
    out = {}
    for f in sorted(glob.glob(os.path.join(KOK, "data", "program", "*.csv.gz"))):
        d = pd.read_csv(f, usecols=["tarih", "hipodrom"]).drop_duplicates()
        for t, h in d.itertuples(index=False):
            if h in ASCII: out.setdefault(str(t), set()).add(ASCII[h])
    return out


if __name__ == "__main__":
    mod = sys.argv[1]
    if mod == "indeks":
        import pandas as pd
        ix = pd.read_csv(os.path.join(KOK, "data", "gozlem", "komiser", "indeks.csv"))
        isle([(r.tarih, r.hipodrom) for r in ix.itertuples() if r.hipodrom in KOD], False)
    elif mod == "gun":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        bugun = dt.datetime.utcnow() + dt.timedelta(hours=3); pg = program_gunleri(); hed = []
        for k in range(n):
            t = (bugun.date() - dt.timedelta(days=k)).isoformat()
            hed += [(t, h) for h in sorted(pg.get(t, []))]
        print("hedef:", hed, flush=True); isle(hed, True)
    elif mod == "geri":
        bas, bit = sys.argv[2], sys.argv[3]; mx = int(sys.argv[4]) if len(sys.argv) > 4 else 400
        pg = program_gunleri(); hed = [(t, h) for t in sorted(pg, reverse=True) if bas <= t <= bit for h in sorted(pg[t])][:mx]
        print("hedef sayısı:", len(hed), flush=True); isle(hed, False)
