"""TJK muhtemeller uçları tarayıcıdan (CORS) okunabilir mi? Yalnızca başlıkları kaydeder (24 Ekim 2026)."""
import json, datetime as dt, requests, os
from . import ortak as O
t = O.tr_simdi().date(); u = f"/muhtemeller/s/{t:%Y/%m/%d}/"
HEDEF = {"checksum": "https://vhs-medya.tjk.org" + u + "checksum.json", "cdn_kok": "https://vhs-medya-cdn.tjk.org" + u + "checksum.json"}
rap = {}
for ad, url in HEDEF.items():
    for org in ("https://example.com", "https://github.io"):
        for yontem in ("GET", "OPTIONS"):
            try:
                h = {"Origin": org, "User-Agent": "Mozilla/5.0"}
                if yontem == "OPTIONS":
                    h.update({"Access-Control-Request-Method": "GET"})
                r = requests.request(yontem, url, headers=h, timeout=20)
                rap[f"{ad}|{org}|{yontem}"] = {"kod": r.status_code, "cors": {k: v for k, v in r.headers.items() if k.lower().startswith("access-control") or k.lower() in ("vary", "cache-control", "server", "content-type")}, "boyut": len(r.content)}
            except Exception as e:
                rap[f"{ad}|{org}|{yontem}"] = {"hata": repr(e)}
os.makedirs("docs/data", exist_ok=True)
json.dump(rap, open("docs/data/cors_probe.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(rap, ensure_ascii=False, indent=1))
