"""Alman at yarışı veri kaynağı adaylarının robots.txt kuralları (23 Ekim 2026). Yalnızca robots.txt okunur. -> data/futbol/robots_adaylar.json"""
import json, os, requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAY = ["german-racing.com", "www.german-racing.com", "turf-times.de", "www.turf-times.de", "www.galopp-sport.de", "www.rennbahn-info.de",
        "www.racingpost.com", "www.sportinglife.com", "www.timeform.com", "www.attheraces.com", "www.horseracingnation.com", "www.sporttrader.de",
        "www.wettstar.de", "www.german-tote.de", "german-tote.de", "www.pferdewetten.de", "www.equibase.com", "www.rennsport.net", "www.pferderennen.de", "www.dvr.de", "www.pmu.fr", "racing.hkjc.com"]
H = {"User-Agent": "tjk-sistem/1.0 (kisisel arastirma)"}
out = {}
for h in ADAY:
    try:
        r = requests.get("https://%s/robots.txt" % h, headers=H, timeout=25)
        out[h] = {"durum": r.status_code, "metin": r.text[:1800] if r.status_code == 200 else ""}
    except Exception as e:
        out[h] = {"durum": "hata", "metin": repr(e)[:120]}
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(KOK, "data", "futbol", "robots_adaylar.json"), "w"), ensure_ascii=False, indent=1)
for h, v in out.items():
    print(h, v["durum"], "|", v["metin"][:100].replace("\n", " "))
