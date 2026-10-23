"""atyarisi istatistik widget'ları (galoplar vb.): sayfa metni + arka plan JSON/XHR istekleri."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://www.atyarisi.com"
URLS = [B + "/at-yarisi/tjk-at-yarisi-istatistikler/galoplar", B + "/gallop-sprint-widget", B + "/at-yarisi/tjk-at-yarisi-istatistikler/en-iyi-derece", B + "/tjk-at-yarisi-istatistikler-mobile"]
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for u in URLS:
        pg = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", locale="tr-TR").new_page()
        ist = []
        def yanit(r, ist=ist):
            try:
                ct = r.headers.get("content-type", "")
                if ("json" in ct or r.request.resource_type in ("xhr", "fetch")) and "GetFooter" not in r.url and "nr-data" not in r.url and "google" not in r.url and "facebook" not in r.url:
                    ist.append({"url": r.url[:240], "durum": r.status, "bas": r.text()[:700]})
            except Exception:
                pass
        pg.on("response", yanit)
        try:
            r0 = pg.goto(u, wait_until="domcontentloaded", timeout=45000); pg.wait_for_timeout(9000)
            out[u] = {"durum": r0.status if r0 else None, "baslik": pg.title(), "metin": re.sub(r"\s+", " ", pg.inner_text("body"))[:1500], "istekler": ist, "iframe": pg.evaluate("[...document.querySelectorAll('iframe')].map(f=>f.src)")}
        except Exception as e:
            out[u] = {"hata": repr(e), "istekler": ist}
        pg.close()
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe6.json"), "w"), ensure_ascii=False, indent=1)
print({u.split("com")[-1]: (v.get("durum"), len(v.get("istekler", []))) for u, v in out.items()})
