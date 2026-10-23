"""Türk koşuları için Probables / FobProbables / FOBRace yapısı: bahis tipleri, ganyan muhtemel ve sabit ihtimalli (FOB) var mı? Nazik: birkaç istek."""
import json, os, time, datetime as dt, requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://tjkbulten.atyarisi.com/api/"
H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek)", "Accept": "application/json", "Origin": "https://www.atyarisi.com", "Referer": "https://www.atyarisi.com/"}
t = (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%Y-%m-%d")
out = {"tarih": t}
def al(yol, **p):
    time.sleep(3)
    r = requests.get(B + yol, params=p, headers=H, timeout=30)
    return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]
sc, js = al("v1/ProgramHippodromes", date=t); out["liste_sc"] = sc
tr = [h for h in (js.get("d") or []) if not (h.get("hippodrome") or {}).get("isForeign")]
out["hipodromlar"] = [(h["id"], h["hippodrome"]["place"], h["hippodrome"].get("hasActiveToteBet"), h["hippodrome"].get("hasActiveFOBBet")) for h in tr]
for h in tr[:2]:
    pid = h["id"]; o = out.setdefault(str(pid), {})
    for ad, yol in (("probables", "v1/Probables"), ("fob", "v1/FobProbables")):
        sc, js = al(yol, programId=pid); o[ad + "_sc"] = sc
        yar = ((js.get("d") or {}).get("races") if isinstance(js, dict) else None) or []
        o[ad + "_kosu"] = len(yar)
        o[ad + "_bahistipleri"] = sorted({b["betTypeId"] for y in yar for b in y.get("bets", [])})
        if yar:
            y = yar[0]; o[ad + "_ornek"] = {"raceNo": y["raceNo"], "bilgi": y.get("information"), "bets": [{"betTypeId": b["betTypeId"], "n": len(b.get("probables", [])), "ilk": b.get("probables", [])[:4], "anahtarlar": [k for k in b if k != "probables"]} for b in y.get("bets", [])]}
    sc, js = al("v1/FOBRace", programId=pid); o["fobrace_sc"] = sc; o["fobrace_ham"] = json.dumps(js, ensure_ascii=False)[:2500]
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe8.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:1500])
