"""agftablosu.com bugünün program sayfaları erişilebilir mi? (23 Ekim 2026) -> data/futbol/agf_probe.json"""
import json, os, re, datetime
from tjk import ortak as O
t = O.tr_simdi().date()
out = {"gun": str(t)}
try:
    from curl_cffi import requests as CR
except Exception:
    CR = None
def al(url):
    try:
        r = CR.get(url, impersonate="chrome", timeout=30) if CR else __import__("requests").get(url, headers=O.HEADERS, timeout=30)
        return {"durum": r.status_code, "uzunluk": len(r.text), "bas": r.text[:200].replace("\n", " "), "metin": r.text}
    except Exception as e:
        return {"durum": "hata", "bas": repr(e)[:150], "metin": ""}
a = al(O.BASE)
out["ana"] = {k: v for k, v in a.items() if k != "metin"}
gun = f"{t.day}-{O.AYLAR[t.month-1]}-{t.year}"
out["ana_baglantilar"] = sorted(set(re.findall(r"/at-yarisi/[a-z\-]+/[0-9a-z\-]+", a["metin"])))[:40]
for h in ["bursa", "istanbul"]:
    r = al(O.prog_url(t, h))
    out["prog_" + h] = {k: v for k, v in r.items() if k != "metin"}
    out["prog_" + h]["tablo_say"] = r["metin"].count("<table")
    out["prog_" + h]["url"] = O.prog_url(t, h)
os.makedirs("data/futbol", exist_ok=True)
json.dump(out, open("data/futbol/agf_probe.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:2500])

# gerçek tarayıcı yolu
try:
    from tjk import tarayici as TR
    import time
    t0 = time.time()
    h = TR.getir(O.BASE, bekle=45)
    out["tarayici_ana"] = {"var": bool(h), "uzunluk": len(h or ""), "sn": round(time.time() - t0, 1), "govde": re.sub(r"<script.*?</script>|<style.*?</style>", "", h or "", flags=re.S)[:1500]}
    if h:
        out["tarayici_baglanti"] = sorted(set(re.findall(r"/at-yarisi/[a-z\-]+/[0-9a-z\-]+", h)))[:30]
        h2 = TR.getir(O.prog_url(t, "bursa"), bekle=45)
        out["tarayici_bursa"] = {"var": bool(h2), "tablo": (h2 or "").count("<table")}
except Exception as e:
    out["tarayici_hata"] = repr(e)[:300]
json.dump(out, open("data/futbol/agf_probe.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k.startswith("tarayici")}, ensure_ascii=False))
