"""atyarisi tjkbulten JSON API: günlük hipodrom listesi + program ayrıntısı (tam yapıyı kaydet)."""
import json, os, requests, datetime, gzip
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
gun = os.environ.get("AY_GUN") or (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", "Accept": "application/json", "Origin": "https://www.atyarisi.com", "Referer": "https://www.atyarisi.com/"}
out = {}
r = requests.get("https://tjkbulten.atyarisi.com/api/v1/ProgramHippodromes", params={"date": gun}, headers=H, timeout=30)
out["liste_durum"] = r.status_code
try:
    liste = r.json()
except Exception:
    liste = {}
out["liste"] = liste
det = {}
for h in (liste.get("d") or []):
    pid = h.get("id")
    rr = requests.get("https://tjkbulten.atyarisi.com/api/v2/ProgramDetails", params={"programId": pid}, headers=H, timeout=30)
    try:
        det[str(pid)] = rr.json()
    except Exception:
        det[str(pid)] = {"hata": rr.status_code, "ham": rr.text[:300]}
out["detay"] = det
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
with gzip.open(os.path.join(KOK, "data", "futbol", "atyarisi_api.json.gz"), "wt") as f:
    json.dump(out, f, ensure_ascii=False)
print(gun, out["liste_durum"], len(det))
