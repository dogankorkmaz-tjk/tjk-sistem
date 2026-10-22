"""Barcelona ofsayt tuzağı hipotezi için La Liga (esp.1) maç başı takım ofsayt sayıları (ESPN). 22 Ekim 2026.
Çıktı: data/futbol/ofsayt/esp.1.json.gz  {maç_id: {d, ev, dep, off_ev, off_dep, gol_ev, gol_dep}}"""
import os, json, gzip, time, datetime
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HD = os.path.join(KOK, "data", "futbol", "ofsayt")
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "application/json"}
LIG = os.environ.get("OFS_LIG", "esp.1")
BASLA = datetime.date.fromisoformat(os.environ.get("OFS_BASLA", "2023-08-10"))
BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/%s/" % LIG
LIMIT = int(os.environ.get("OFS_LIMIT", "1500"))


def ofs(sm):
    out = {}
    for t in (sm.get("boxscore") or {}).get("teams", []):
        v = None
        for s in t.get("statistics") or []:
            if "offside" in (s.get("name") or "").lower():
                try: v = float(s.get("displayValue"))
                except Exception: pass
        out[t.get("homeAway")] = v
    return out


def main():
    os.makedirs(HD, exist_ok=True)
    yol = os.path.join(HD, LIG + ".json.gz")
    d = json.load(gzip.open(yol, "rt")) if os.path.exists(yol) else {}
    durum_yol = os.path.join(HD, LIG + "_durum.txt")
    gun = datetime.date.fromisoformat(open(durum_yol).read().strip()) if os.path.exists(durum_yol) else BASLA
    bugun = datetime.date.today(); n = 0
    while gun <= bugun and n < LIMIT:
        try:
            sb = requests.get(BASE + "scoreboard?dates=%s" % gun.strftime("%Y%m%d"), headers=H, timeout=40).json()
        except Exception as e:
            print("scoreboard hata", gun, repr(e)[:80]); break
        for ev in sb.get("events", []):
            if not ev.get("status", {}).get("type", {}).get("completed") or ev["id"] in d:
                continue
            try:
                sm = requests.get(BASE + "summary?event=" + ev["id"], headers=H, timeout=40).json()
                c = ev["competitions"][0]["competitors"]
                ha = {x["homeAway"]: x for x in c}
                o = ofs(sm)
                d[ev["id"]] = {"d": ev["date"], "ev": ha["home"]["team"]["displayName"], "dep": ha["away"]["team"]["displayName"],
                               "off_ev": o.get("home"), "off_dep": o.get("away"), "gol_ev": ha["home"].get("score"), "gol_dep": ha["away"].get("score")}
                n += 1
            except Exception as e:
                print("özet hata", ev["id"], repr(e)[:80])
            time.sleep(0.4)
        gun += datetime.timedelta(days=1)
        if gun < bugun - datetime.timedelta(days=3):
            open(durum_yol, "w").write(gun.isoformat())
        time.sleep(0.2)
        if n and n % 100 == 0:
            with gzip.open(yol, "wt") as f: json.dump(d, f, separators=(",", ":"))
    with gzip.open(yol, "wt") as f: json.dump(d, f, separators=(",", ":"))
    print("maç", len(d), "yeni", n, "son gün", gun)


if __name__ == "__main__":
    main()
