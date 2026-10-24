"""Galop/idman uç noktası arama: JS paketinde geçen adlar (GallopsSprints, race-gallops-sprints) için tjkbulten.atyarisi.com altında sınırlı sayıda deneme."""
import json, os, time, datetime as dt, requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://tjkbulten.atyarisi.com/api/"
H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek)", "Accept": "application/json", "Origin": "https://www.atyarisi.com", "Referer": "https://www.atyarisi.com/"}
t = (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%Y-%m-%d")
def al(yol, **p):
    time.sleep(3)
    try:
        r = requests.get(B + yol, params=p, headers=H, timeout=25)
        return r.status_code, r.text[:600]
    except Exception as e:
        return 0, repr(e)
js = requests.get(B + "v1/ProgramHippodromes", params={"date": t}, headers=H, timeout=25).json()
pid = [h["id"] for h in js["d"] if not h["hippodrome"].get("isForeign")][0]
out = {"pid": pid}
for ver in ("v1", "v2", "v3"):
    for ad in ("GallopsSprints", "RaceGallopsSprints", "Gallops", "GallopSprints", "GetGallopsSprints"):
        for prm in ({"programId": pid}, {"programId": pid, "raceNo": 1}):
            sc, tx = al(f"{ver}/{ad}", **prm)
            if sc not in (404, 0):
                out[f"{ver}/{ad}/{len(prm)}"] = [sc, tx]
                print(ver, ad, sc, tx[:150], flush=True)
            if sc == 200: break
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe9.json"), "w"), ensure_ascii=False, indent=1)
print("bitti", len(out))
