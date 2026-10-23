"""atyarisi İstatistikler sayfasının yüklediği JS paketlerinde galop/istatistik API yollarını ara (tarayıcı yalnızca okur)."""
import json, os, re
from playwright.sync_api import sync_playwright
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pat = re.compile(r'["\'`]((?:https?:)?[^"\'`\s]{0,80}(?:api/v\d+|/Statistic|/Training|/Galop|/Gallop|/Idman|RaceAnalysis|HorseStat|Sprint)[^"\'`\s]{0,120})["\'`]', re.I)
out = {"js": [], "yollar": {}, "json_istekleri": []}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", locale="tr-TR").new_page()
    govde = {}
    def yanit(r):
        try:
            u = r.url
            if u.split("?")[0].endswith(".js") and ("atyarisi" in u):
                govde[u] = r.text()
            elif "json" in r.headers.get("content-type", "") and "atyarisi" in u and "GetFooter" not in u:
                out["json_istekleri"].append({"url": u[:200], "bas": r.text()[:300]})
        except Exception:
            pass
    pg.on("response", yanit)
    pg.goto("https://www.atyarisi.com/tjk-at-yarisi-istatistikler", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(5000)
    out["js"] = [u[:160] for u in govde]
    for u, t in govde.items():
        bul = sorted(set(pat.findall(t)))
        if bul:
            out["yollar"][u[:160]] = bul[:300]
        # galop/sprint içeren bağlam
        for m in re.finditer(r"(?i)(galop|sprint|gallop)", t):
            s = max(0, m.start() - 120); out.setdefault("baglam", []).append(t[s:m.end() + 160].replace("\n", " "))
            if len(out["baglam"]) > 25: break
    b.close()
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_js_probe.json"), "w"), ensure_ascii=False, indent=1)
print(len(out["js"]), {k.split("/")[-1][:30]: len(v) for k, v in out["yollar"].items()})
