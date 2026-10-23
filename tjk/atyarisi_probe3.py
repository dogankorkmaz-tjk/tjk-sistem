"""atyarisi sonuç sayfası: hangi API çağrılıyor, egzotik ikramiyeler var mı (dünün sonuçları)."""
import json, os, re, datetime
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {"istekler": [], "linkler": []}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", locale="tr-TR").new_page()
    def yanit(r):
        try:
            if "atyarisi.com" in r.url and "json" in r.headers.get("content-type", "") and "GetFooter" not in r.url:
                out["istekler"].append({"url": r.url[:220], "durum": r.status, "bas": r.text()[:1500]})
        except Exception:
            pass
    pg.on("response", yanit)
    pg.goto("https://www.atyarisi.com/tjk-at-yarisi-programi", wait_until="networkidle", timeout=60000)
    out["linkler"] = pg.evaluate("[...new Set([...document.querySelectorAll('a')].map(a=>a.href))].filter(h=>/sonuc|result/i.test(h))")
    for u in out["linkler"][:2] + ["https://www.atyarisi.com/tjk-at-yarisi-sonuclari"]:
        try:
            pg.goto(u, wait_until="networkidle", timeout=60000); pg.wait_for_timeout(3000)
            out.setdefault("sayfalar", {})[u] = re.sub(r"\s+", " ", pg.inner_text("body"))[:1500]
        except Exception as e:
            out.setdefault("sayfalar", {})[u] = repr(e)
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe3.json"), "w"), ensure_ascii=False, indent=1)
print(len(out["istekler"]), out["linkler"][:5])
