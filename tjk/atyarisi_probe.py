"""atyarisi.com program sayfası dinamik mi, veri hangi JSON isteğiyle geliyor? (23 Ekim 2026; robots tüm sayfalara izin veriyor, llms.txt otomatik kullanıma açık). Tek sayfa, tek yükleme."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {"istekler": []}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", locale="tr-TR")
    pg = ctx.new_page()
    def yanit(r):
        try:
            ct = r.headers.get("content-type", "")
            if r.request.resource_type in ("xhr", "fetch") or "json" in ct:
                kayit = {"url": r.url[:200], "durum": r.status, "tip": ct[:40]}
                if "json" in ct:
                    kayit["bas"] = r.text()[:500]
                out["istekler"].append(kayit)
        except Exception as e:
            pass
    pg.on("response", yanit)
    pg.goto("https://www.atyarisi.com/tjk-at-yarisi-programi", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(4000)
    out["baslik"] = pg.title()
    out["metin"] = re.sub(r"\s+", " ", pg.inner_text("body"))[:2500]
    out["tablo"] = pg.evaluate("document.querySelectorAll('table').length")
    out["linkler"] = pg.evaluate("[...document.querySelectorAll('a')].map(a=>a.href).filter(h=>/program|hipodrom|kosu|bursa|istanbul/i.test(h)).slice(0,40)")
    b.close()
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_probe.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({"baslik": out["baslik"], "tablo": out["tablo"], "istek_say": len(out["istekler"])}, ensure_ascii=False))
