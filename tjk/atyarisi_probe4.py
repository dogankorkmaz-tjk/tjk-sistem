import json, os, requests, gzip
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", "Accept": "application/json", "Origin": "https://www.atyarisi.com", "Referer": "https://www.atyarisi.com/"}
out = {}
for gun in ("2026-10-22", "2026-10-21"):
    L = requests.get("https://tjkbulten.atyarisi.com/api/v1/ProgramHippodromes", params={"date": gun}, headers=H, timeout=30).json().get("d") or []
    for h in L:
        if h["hippodrome"].get("isForeign"):
            continue
        out[f"{gun}-{h['hippodrome']['code']}"] = requests.get("https://tjkbulten.atyarisi.com/api/v4/RaceResult", params={"programId": h["id"]}, headers=H, timeout=30).json()
with gzip.open(os.path.join(KOK, "data", "futbol", "atyarisi_sonuc.json.gz"), "wt") as f:
    json.dump(out, f, ensure_ascii=False)
print(list(out))
