"""Türkiye at yarışı program verisi veren (jokey, kilo, at listesi) sitelerin robots.txt kuralları (23 Ekim 2026). Yalnızca robots.txt ve robots izin veriyorsa tek bir program sayfası okunur."""
import json, os, re, requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAY = {"www.sporx.com": "https://www.sporx.com/at-yarisi", "www.atyarisi.com": "https://www.atyarisi.com/", "www.nesine.com": "https://www.nesine.com/",
        "www.bilyoner.com": "https://www.bilyoner.com/", "www.misli.com": "https://www.misli.com/", "www.fanatik.com.tr": "https://www.fanatik.com.tr/at-yarisi",
        "www.hurriyet.com.tr": "https://www.hurriyet.com.tr/", "www.sabah.com.tr": "https://www.sabah.com.tr/at-yarisi", "www.ntvspor.net": "https://www.ntvspor.net/",
        "www.haberturk.com": "https://www.haberturk.com/", "www.yarisprogrami.com": "https://www.yarisprogrami.com/", "www.at-yarisi.com": "https://www.at-yarisi.com/",
        "www.tjk.org": "https://www.tjk.org/", "www.takvim.com.tr": "https://www.takvim.com.tr/at-yarisi", "www.milliyet.com.tr": "https://www.milliyet.com.tr/at-yarisi"}
H = {"User-Agent": "tjk-sistem/1.0 (kisisel arastirma)"}
out = {}
for h, sayfa in ADAY.items():
    try:
        r = requests.get("https://%s/robots.txt" % h, headers=H, timeout=25)
        m = r.text if r.status_code == 200 and "<html" not in r.text[:300].lower() else ""
        kayit = {"durum": r.status_code, "robots": m[:700]}
    except Exception as e:
        kayit = {"durum": "hata", "robots": repr(e)[:100]}
    out[h] = kayit
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(KOK, "data", "futbol", "robots_tr.json"), "w"), ensure_ascii=False, indent=1)
for h, v in out.items():
    print(h, v["durum"], "|", v["robots"][:110].replace("\n", " "))
