"""ganyancanavari.com.tr/mobile galop sayfaları: sayfa kaynağı + arka plan istekleri (robots: User-agent * Allow /). 3 sayfa yüklemesi, başka istek yok."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://www.ganyancanavari.com.tr/mobile/"
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for yol in ("gunluk-galoplar.html", "galoplar.html", "galoplar-ozet.html"):
        pg = b.new_context(user_agent="Mozilla/5.0 (Linux; Android 13) Chrome/124 Mobile Safari/537.36", locale="tr-TR").new_page()
        ist = []
        def yanit(r, ist=ist):
            try:
                u = r.url
                if r.request.resource_type in ("xhr", "fetch", "script", "document") and "google" not in u and "doubleclick" not in u:
                    ist.append({"tip": r.request.resource_type, "url": u[:300], "durum": r.status, "bas": r.text()[:600] if r.request.resource_type in ("xhr", "fetch") else ""})
            except Exception:
                pass
        pg.on("response", yanit)
        try:
            pg.goto(B + yol, wait_until="domcontentloaded", timeout=45000); pg.wait_for_timeout(9000)
            out[yol] = {"baslik": pg.title(), "metin": re.sub(r"\s+", " ", pg.inner_text("body"))[:2500], "istekler": ist, "html_bas": pg.content()[:3000]}
        except Exception as e:
            out[yol] = {"hata": repr(e), "istekler": ist}
        pg.close()
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "ganyancanavari_probe.json"), "w"), ensure_ascii=False, indent=1)
print({k: len(v.get("istekler", [])) for k, v in out.items()})
