"""ESPN herkese açık maç özeti servisinden oyuncu bazlı maç verisi (22 Ekim 2026). Resmî olmayan, belgelenmemiş uç nokta: nazik kullanım (1 istek ~0,5 sn, çalıştırma başına sınırlı).
Her biten maç için: tarih, takımlar, hakem (varsa), ilk 11 ve yedekler, oyuncu başına faul yapma/yeme, sarı/kırmızı kart, şut, dakika. data/futbol/espn/<lig>_<yıl-ay>.json.gz"""
import os, sys, json, gzip, time, datetime
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HD = os.path.join(KOK, "data", "futbol", "espn")
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "application/json"}
LIGLER = ["tur.1"]
BASLA = datetime.date(2023, 8, 1)
LIMIT = int(os.environ.get("ESPN_LIMIT", "200"))
BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/%s/"


def yukle(lig, ay):
    yol = os.path.join(HD, "%s_%s.json.gz" % (lig, ay))
    return yol, (json.load(gzip.open(yol, "rt", encoding="utf-8")) if os.path.exists(yol) else {})


def sade(sm, ev):
    ro = []
    for t in sm.get("rosters") or []:
        for p in t.get("roster") or []:
            st = {s.get("name"): s.get("value") for s in p.get("stats") or []}
            ro.append({"t": t["team"]["displayName"], "ha": t.get("homeAway"), "id": p["athlete"]["id"], "ad": p["athlete"]["displayName"], "poz": (p.get("position") or {}).get("abbreviation"),
                       "ilk11": p.get("starter"), "giren": p.get("subbedIn"), "cikan": p.get("subbedOut"),
                       "fy": st.get("foulsCommitted"), "fe": st.get("foulsSuffered"), "sari": st.get("yellowCards"), "kirmizi": st.get("redCards"), "sut": st.get("totalShots"), "dk": st.get("appearances")})
    gi = sm.get("gameInfo") or {}
    return {"d": ev.get("date"), "ev": [c["team"]["displayName"] for c in ev["competitions"][0]["competitors"] if c.get("homeAway") == "home"][0],
            "dep": [c["team"]["displayName"] for c in ev["competitions"][0]["competitors"] if c.get("homeAway") == "away"][0],
            "hakem": [o.get("displayName") for o in (gi.get("officials") or [])], "oyuncu": ro}


def main():
    os.makedirs(HD, exist_ok=True)
    bugun = datetime.date.today(); n = 0
    for lig in LIGLER:
        gun = BASLA
        while gun <= bugun and n < LIMIT:
            bit = min(gun + datetime.timedelta(days=6), bugun)
            try:
                sb = requests.get(BASE % lig + "scoreboard?dates=%s-%s" % (gun.strftime("%Y%m%d"), bit.strftime("%Y%m%d")), headers=H, timeout=40).json()
            except Exception as e:
                print("scoreboard hata", gun, repr(e)[:80]); gun = bit + datetime.timedelta(days=1); continue
            for ev in sb.get("events", []):
                if not ev.get("status", {}).get("type", {}).get("completed"):
                    continue
                ay = ev["date"][:7]; yol, d = yukle(lig, ay)
                if ev["id"] in d:
                    continue
                try:
                    sm = requests.get(BASE % lig + "summary?event=" + ev["id"], headers=H, timeout=40).json()
                    d[ev["id"]] = sade(sm, ev); n += 1
                    with gzip.open(yol, "wt", encoding="utf-8") as f:
                        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
                except Exception as e:
                    print("özet hata", ev["id"], repr(e)[:80])
                time.sleep(0.5)
            gun = bit + datetime.timedelta(days=1)
            time.sleep(0.3)
    print("yeni maç", n)


if __name__ == "__main__":
    main()
