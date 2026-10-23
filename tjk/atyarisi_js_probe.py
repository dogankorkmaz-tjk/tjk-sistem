"""atyarisi.com'un herkese açık JS paketlerinde istatistik/galop API yollarını ara (yalnızca okuma; her dosya bir kez)."""
import json, os, re, requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"}
out = {"scriptler": [], "yollar": {}}
html = requests.get("https://www.atyarisi.com/tjk-at-yarisi-istatistikler", headers=H, timeout=30).text
src = re.findall(r'<script[^>]+src="([^"]+)"', html) + re.findall(r'href="([^"]+\.js)"', html)
src = [s if s.startswith("http") else "https://www.atyarisi.com" + s for s in dict.fromkeys(src)]
out["scriptler"] = src
pat = re.compile(r'["\'`]([^"\'`\s]*(?:api/v\d+|/Statistic|/Training|/Galop|/Gallop|/Idman|RaceAnalysis|HorseStat)[^"\'`\s]*)["\'`]', re.I)
for u in src:
    if "atyarisi" not in u and "tjk" not in u:
        continue
    try:
        t = requests.get(u, headers=H, timeout=40).text
    except Exception as e:
        continue
    bul = sorted(set(pat.findall(t)))
    if bul:
        out["yollar"][u] = bul[:200]
json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_js_probe.json"), "w"), ensure_ascii=False, indent=1)
print(len(src), {k.split("/")[-1]: len(v) for k, v in out["yollar"].items()})
