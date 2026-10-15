"""Cloudflare JS denetimi olan sayfalar için gerçek tarayıcıyla indirme (Playwright Chromium). Yalnız gerektiğinde, yavaş."""
import time

_PW = None
_B = None


def getir(url, bekle=25):
    global _PW, _B
    from playwright.sync_api import sync_playwright
    if _B is None:
        _PW = sync_playwright().start()
        _B = _PW.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = _B.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", locale="tr-TR")
    pg = ctx.new_page()
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        t0 = time.time()
        while time.time() - t0 < bekle and "Just a moment" in (pg.title() or ""):
            pg.wait_for_timeout(1000)
        return None if "Just a moment" in (pg.title() or "") else pg.content()
    except Exception as e:
        print("tarayıcı hata:", url, repr(e)); return None
    finally:
        ctx.close()
