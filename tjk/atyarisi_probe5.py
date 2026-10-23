"""atyarisi 'İstatistikler' bölümünde idman verisi var mı? Menü bağlantılarını ve her sayfanın JSON isteklerini kaydeder."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {"linkler": [], "sayfa": {}}
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_context(user_agent=UA, locale="tr-TR").new_page()
    pg.goto("https://www.atyarisi.com/tjk-at-yarisi-programi", wait_until="networkidle", timeout=60000)
    L = pg.evaluate("[...new Set([...document.querySelectorAll('a')].map(a=>a.href))]")
    out["linkler"] = [l for l in L if "atyarisi.com" in l]
    hedef = [l for l in out["linkler"] if re.search(r"istatistik|idman|training|statistic", l, re.I)][:8]
    out["hedef"] = hedef
    for u in hedef:
        ist = []
        def yanit(r):
            try:
                if "json" in r.headers.get("content-type", "") and "GetFooter" not in r.url and "nr-data" not in r.url:
                    ist.append({"url": r.url[:200], "bas": r.text()[:400]})
            except Exception:
                pass
        pg.on("response", yanit)
        try:
            pg.goto(u, wait_until="networkidle", timeout=60000); pg.wait_for_timeout(2500)
            out["sayfa"][u] = {"metin": re.sub(r"\s+", " ", pg.inner_text("body"))[:1200], "istekler": ist}
        except Exception as e:
            out["sayfa"][u] = {"hata": repr(e)}
        pg.remove_listener("response", yanit)
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe5.json"), "w"), ensure_ascii=False, indent=1)
print(len(out["linkler"]), out["hedef"])
