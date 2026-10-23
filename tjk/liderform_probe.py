"""liderform.com.tr/program/galop: önce robots.txt/llms.txt; izin varsa sayfa + JSON istekleri (tek yükleme)."""
import json, os, re, gzip, requests, urllib.robotparser
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"
B = "https://liderform.com.tr"
out = {}
for yol in ("/robots.txt", "/llms.txt", "/sitemap.xml"):
    try:
        r = requests.get(B + yol, headers={"User-Agent": UA}, timeout=20)
        out[yol] = {"durum": r.status_code, "metin": r.text[:4000]}
    except Exception as e:
        out[yol] = {"hata": repr(e)}
rp = urllib.robotparser.RobotFileParser()
try:
    rp.parse(out["/robots.txt"].get("metin", "").splitlines())
    out["izin_galop"] = rp.can_fetch("*", B + "/program/galop")
except Exception as e:
    out["izin_galop"] = None
print("robots durum:", out["/robots.txt"].get("durum"), "izin:", out["izin_galop"])
if out["izin_galop"] is not False and out["/robots.txt"].get("durum") in (200, 404):
    from playwright.sync_api import sync_playwright
    ist = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(user_agent=UA, locale="tr-TR").new_page()
        def yanit(r):
            try:
                ct = r.headers.get("content-type", "")
                if r.request.resource_type in ("xhr", "fetch") or "json" in ct:
                    ist.append({"url": r.url[:240], "durum": r.status, "tip": ct[:40], "bas": r.text()[:600]})
            except Exception:
                pass
        pg.on("response", yanit)
        pg.goto(B + "/program/galop", wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(8000)
        out["baslik"] = pg.title()
        out["metin"] = re.sub(r"[ \t]+", " ", pg.inner_text("body"))[:6000]
        out["tablo_say"] = pg.evaluate("document.querySelectorAll('table').length")
        out["linkler"] = pg.evaluate("[...new Set([...document.querySelectorAll('a')].map(a=>a.href))].slice(0,80)")
        with gzip.open(os.path.join(KOK, "data", "futbol", "liderform_galop.html.gz"), "wt") as f:
            f.write(pg.content())
        b.close()
    out["istekler"] = ist
json.dump(out, open(os.path.join(KOK, "data", "futbol", "liderform_probe.json"), "w"), ensure_ascii=False, indent=1)
