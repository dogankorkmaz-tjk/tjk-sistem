"""Bülten sayfasında 'Galoplar' sekmesine tıklayıp arka plan isteklerini yakalar (ağ izi)."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {"istekler": [], "adimlar": []}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", locale="tr-TR", viewport={"width": 1400, "height": 1200}).new_page()
    def yanit(r):
        try:
            u = r.url
            if "atyarisi.com" in u and r.request.resource_type in ("xhr", "fetch") and not any(x in u for x in ("GetFooter", "nr-data", "GetSeoConfig", "GetGeneralNotice")):
                out["istekler"].append({"adim": len(out["adimlar"]), "url": u[:260], "durum": r.status, "bas": r.text()[:700]})
        except Exception:
            pass
    pg.on("response", yanit)
    pg.goto("https://www.atyarisi.com/tjk-at-yarisi-bulteni", wait_until="domcontentloaded", timeout=45000); pg.wait_for_timeout(6000)
    out["adimlar"].append("bülten yüklendi")
    for ad in ("Ankara", "İzmir"):
        try:
            pg.get_by_text(ad, exact=False).first.click(timeout=4000); pg.wait_for_timeout(3000); out["adimlar"].append("hipodrom " + ad); break
        except Exception as e:
            out["adimlar"].append("hipodrom yok " + ad)
    for sek in ("Galoplar", "İdman", "Galop"):
        try:
            pg.get_by_text(sek, exact=True).first.click(timeout=4000); pg.wait_for_timeout(5000); out["adimlar"].append("sekme " + sek)
            out["metin_" + sek] = re.sub(r"\s+", " ", pg.inner_text("body"))[:1500]
            break
        except Exception as e:
            out["adimlar"].append("sekme yok " + sek + " " + type(e).__name__)
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe10.json"), "w"), ensure_ascii=False, indent=1)
print(out["adimlar"], len(out["istekler"]))
