"""Hipodrom bazlı günlük yağış/sıcaklık (Open-Meteo arşiv). Yalnızca analiz için (ıslak-pist vekili); modelde kullanılmaz. Çıktı: data/hava/gunluk.csv"""
import csv, json, datetime, time, urllib.request
YER = {"istanbul": (40.99, 28.88), "izmir": (38.39, 27.14), "adana": (37.00, 35.40), "bursa": (40.21, 29.02), "ankara": (39.96, 32.74),
       "sanliurfa": (37.15, 38.80), "antalya": (36.92, 30.72), "elazig": (38.67, 39.20), "kocaeli": (40.76, 29.95), "diyarbakir": (37.92, 40.21)}
bas = "2023-01-01"; son = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
rows = []
for h, (la, lo) in YER.items():
    u = f"https://archive-api.open-meteo.com/v1/archive?latitude={la}&longitude={lo}&start_date={bas}&end_date={son}&daily=precipitation_sum,rain_sum,temperature_2m_mean&timezone=Europe%2FIstanbul"
    for k in range(3):
        try:
            d = json.load(urllib.request.urlopen(u, timeout=60))["daily"]; break
        except Exception as e:
            print(h, "hata", e); time.sleep(10); d = None
    if not d: continue
    for t, p, r, s in zip(d["time"], d["precipitation_sum"], d["rain_sum"], d["temperature_2m_mean"]):
        rows.append((h, t, p, r, s))
    time.sleep(3)
with open("data/hava/gunluk.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["hipodrom", "tarih", "yagis_mm", "yagmur_mm", "sicaklik"]); w.writerows(rows)
print(len(rows), "satır")
