"""atyarisi'nin diğer sayfalarında (sabit ihtimalli, muhtemel/AGF, bülten, tahminler, kuponlar, ortak altılı) arka plan API'leri."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://www.atyarisi.com"
SAYFALAR = ["/tjk-sabit-ihtimalli", "/tjk-at-yarisi-muhtemel-agf", "/tjk-uzun-vadeli-at-yarisi-bulteni", "/tjk-at-yarisi-tahminleri", "/tjk-at-yarisi-editor-hazir-kuponlar", "/tjk-at-yarisi-ortak-altili", "/tjk-at-yarisi-bulteni"]
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for yol in SAYFALAR:
        pg = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", locale="tr-TR").new_page()
        ist = []
        def yanit(r, ist=ist):
            try:
                u = r.url
                if "atyarisi.com" in u and ("json" in r.headers.get("content-type", "") or r.request.resource_type in ("xhr", "fetch")) and not any(x in u for x in ("GetFooter", "nr-data", "GetSeoConfig", "GetGeneralNotice")):
                    ist.append({"url": u[:230], "durum": r.status, "bas": r.text()[:500]})
            except Exception:
                pass
        pg.on("response", yanit)
        try:
            pg.goto(B + yol, wait_until="domcontentloaded", timeout=45000); pg.wait_for_timeout(8000)
            out[yol] = {"baslik": pg.title(), "metin": re.sub(r"\s+", " ", pg.inner_text("body"))[:700], "istekler": ist}
        except Exception as e:
            out[yol] = {"hata": repr(e), "istekler": ist}
        pg.close()
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe7.json"), "w"), ensure_ascii=False, indent=1)
print({k: len(v.get("istekler", [])) for k, v in out.items()})
