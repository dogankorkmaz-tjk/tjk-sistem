"""Futbol veri kaynaklarına GitHub Actions'tan erişim yoklaması (22 Ekim 2026). Sonuç data/futbol/probe.json."""
import json, os, time
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEDEF = {
    "mk_robots": "https://www.mackolik.com/robots.txt",
    "mk_home": "https://www.mackolik.com/",
    "mk_canli": "https://www.mackolik.com/canli-sonuclar",
    "mk_mac": "https://www.mackolik.com/mac/galatasaray-fenerbahce/",
    "mk_arsiv": "https://arsiv.mackolik.com/Genis-Iddaa-Programi",

    "fd_T1": "https://www.football-data.co.uk/mmz4281/2526/T1.csv",
    "fd_E0": "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
    "fd_notes": "https://www.football-data.co.uk/notes.txt",
    "fbref_tr": "https://fbref.com/en/comps/26/Super-Lig-Stats",
    "understat": "https://understat.com/league/EPL",
    "sofascore_gun": "https://api.sofascore.com/api/v1/sport/football/scheduled-events/2026-10-22",
    "iddaa_site": "https://www.iddaa.com/",
    "iddaa_api": "https://sportsbookv2.iddaa.com/sportsbook/events?st=1&type=0&version=0",
    "nesine": "https://www.nesine.com/iddaa",
    "oddsportal": "https://www.oddsportal.com/matches/football/",
    "openfootball": "https://raw.githubusercontent.com/openfootball/football.json/master/README.md",
}
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "*/*"}
out = {}
for k, u in HEDEF.items():
    t = time.time()
    try:
        r = requests.get(u, headers=H, timeout=25)
        out[k] = {"kod": r.status_code, "bayt": len(r.content), "sn": round(time.time() - t, 1), "tip": r.headers.get("content-type", "")[:40], "bas": r.text[:300].replace("\n", " "), "metin": r.text[:4000] if k.startswith("mk_") else ""}
    except Exception as e:
        out[k] = {"hata": repr(e)[:200]}
    print(k, out[k].get("kod"), out[k].get("bayt"), out[k].get("hata", ""))
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(KOK, "data", "futbol", "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

try:
    r = requests.get(HEDEF["iddaa_api"], headers=H, timeout=40)
    open(os.path.join(KOK, "data", "futbol", "iddaa_ornek.json"), "w", encoding="utf-8").write(r.text)
except Exception as e:
    print("iddaa örnek hatası", repr(e))
