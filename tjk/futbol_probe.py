"""Futbol veri kaynaklarına GitHub Actions'tan erişim yoklaması (22 Ekim 2026). Sonuç data/futbol/probe.json."""
import json, os, time
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEDEF = {
    "tff_robots": "https://www.tff.org/robots.txt",
    "tff_hakem": "https://www.tff.org/default.aspx?pageID=198",
    "tm_robots": "https://www.transfermarkt.com.tr/robots.txt",
    "tm_sl": "https://www.transfermarkt.com.tr/super-lig/startseite/wettbewerb/TR1",
    "wf_robots": "https://www.worldfootball.net/robots.txt",
    "wf_sl": "https://www.worldfootball.net/competition/tur-sueperlig/",
    "fotmob": "https://www.fotmob.com/api/leagues?id=71",
    "fdorg": "https://api.football-data.org/v4/competitions/PL/matches",
    "apifootball": "https://v3.football.api-sports.io/status",
    "sportsdb": "https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id=4339",
    "espn": "https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/scoreboard",
    "understat_players": "https://understat.com/league/EPL/2025",
}
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "*/*"}
out = {}
for k, u in HEDEF.items():
    t = time.time()
    try:
        r = requests.get(u, headers=H, timeout=25)
        out[k] = {"kod": r.status_code, "bayt": len(r.content), "sn": round(time.time() - t, 1), "tip": r.headers.get("content-type", "")[:40], "bas": r.text[:300].replace("\n", " "), "metin": r.text[:1500] if k.endswith("robots") else ""}
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
