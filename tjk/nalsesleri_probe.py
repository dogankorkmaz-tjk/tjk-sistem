"""Nal Sesleri API'sinin derinliğini görmek için 6 at, 2 sn arayla (nazik küçük deneme)."""
import json, os, time, gzip, requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = json.load(open(os.path.join(KOK, "docs", "data", "gun", "2026-10-23.json"), encoding="utf-8"))
adlar = []
for h in g["hipodromlar"]:
    for k in h["kosular"]:
        for a in k["atlar"][:1]:
            adlar.append(a["at"])
adlar = adlar[:6]
out = {}
for ad in adlar:
    try:
        r = requests.get("https://nalsesleri.com/api", params={"horse_name": ad}, headers={"User-Agent": "GanyanMasasi-arastirma/1.0 (kisisel, dusuk hacim)"}, timeout=30)
        out[ad] = {"durum": r.status_code, "govde": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:500]}
    except Exception as e:
        out[ad] = {"hata": repr(e)}
    time.sleep(2)
with gzip.open(os.path.join(KOK, "data", "futbol", "nalsesleri_probe.json.gz"), "wt") as f:
    json.dump(out, f, ensure_ascii=False)
print({a: (len(v["govde"].get("data", [])) if isinstance(v.get("govde"), dict) else v) for a, v in out.items()})
