"""liderform.com.tr: yalnızca robots.txt / llms.txt / sitemap / ana sayfa başlığı (basit istek, Playwright yok)."""
import json, os, requests, re
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"}
out = {}
for host in ("https://liderform.com.tr", "https://www.liderform.com.tr"):
    for yol in ("/robots.txt", "/llms.txt", "/sitemap.xml", "/program/galop", "/"):
        try:
            r = requests.get(host + yol, headers=H, timeout=20, allow_redirects=True)
            t = r.text
            out[host + yol] = {"durum": r.status_code, "tip": r.headers.get("content-type", "")[:40], "boyut": len(t), "son_url": r.url,
                               "metin": t[:3500] if yol in ("/robots.txt", "/llms.txt", "/sitemap.xml") else re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S))[:600],
                               "script_src": re.findall(r'<script[^>]+src="([^"]+)"', t)[:15] if yol in ("/", "/program/galop") else None}
        except Exception as e:
            out[host + yol] = {"hata": repr(e)}
json.dump(out, open(os.path.join(KOK, "data", "futbol", "liderform_robots.json"), "w"), ensure_ascii=False, indent=1)
print({k: v.get("durum", v.get("hata")) for k, v in out.items()})
