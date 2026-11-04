"""Padok (yarış öncesi at gösterisi) görüntüsü var mı? tjk.org sayfaları ve video-cdn kalıpları (yalnız okur; GitHub Actions'ta çalışır)."""
import re, subprocess, sys, datetime as dt
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
def get(u, n=400000):
    r = subprocess.run(["curl", "-s", "-L", "-m", "40", "-A", UA, "-e", "https://www.tjk.org/", "-w", "\n@@%{http_code}", u], capture_output=True, text=True)
    t = r.stdout; i = t.rfind("\n@@"); return (t[:i][:n], t[i + 3:]) if i >= 0 else ("", "0")
def head(u):
    r = subprocess.run(["curl", "-s", "-I", "-m", "25", "-A", UA, "-e", "https://www.tjk.org/", u], capture_output=True, text=True)
    m = re.search(r"HTTP/\S+ (\d+)", r.stdout); L = re.search(r"(?i)content-length: (\d+)", r.stdout); return (m.group(1) if m else "0"), (L.group(1) if L else "")
out = []
def P(*a): s = " ".join(str(x) for x in a); print(s, flush=True); out.append(s)
bugun = dt.date.today(); gun = bugun.strftime("%y%m%d")
# 1) sayfalar
sayfalar = ["https://www.tjk.org/", "https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisProgrami", "https://www.tjk.org/TR/YarisSever/Info/Page/CanliYayin",
            "https://www.tjk.org/TR/YarisSever/Info/Page/YarisVideolari", "https://www.tjk.org/TR/YarisSever/Info/Sayfa/CanliYayin"]
bul = {}
for u in sayfalar:
    t, c = get(u); P("SAYFA", c, len(t), u)
    for m in re.finditer(r'(?i)href="([^"]*(?:video|canli|padok|paddock|tv|yayin)[^"]*)"', t):
        h = m.group(1); h = h if h.startswith("http") else "https://www.tjk.org" + (h if h.startswith("/") else "/" + h); bul[h] = 1
    for m in re.finditer(r"(?i).{0,80}(padok|paddock).{0,120}", t): P("  PADOK-GEÇTİ:", re.sub(r"\s+", " ", m.group(0)))
    for m in re.finditer(r'https?://[^"\'\s<>]+\.(?:m3u8|mp4)[^"\'\s<>]*', t): P("  MEDYA:", m.group(0))
P("BULUNAN BAĞLANTILAR", len(bul))
for u in list(bul)[:25]:
    t, c = get(u); P("  ALT", c, len(t), u)
    for m in re.finditer(r"(?i).{0,80}(padok|paddock).{0,120}", t): P("    PADOK-GEÇTİ:", re.sub(r"\s+", " ", m.group(0)))
    for m in re.finditer(r'https?://[^"\'\s<>]+\.(?:m3u8|mp4)[^"\'\s<>]*', t): P("    MEDYA:", m.group(0))
# 2) CDN kalıpları: bilinen yarış videosu ile aynı klasör
ay = bugun.strftime("%Y/%-m"); ay0 = bugun.strftime("%Y/%m")
for kod in ("11", "21", "31"):
    for suf in ("_m", "_p", "_pd", "_padok", "_h", "_s", "_t", "_l", "_g", "_e", ""):
        for kl in (ay0, ay):
            u = f"https://video-cdn.tjk.org/videoftp/{kl}/{gun}{kod}{suf}.mp4"
            c, n = head(u)
            if c != "404" and c != "0": P("CDN", c, n, u)
for yol in ("padok", "paddock", "padokvideo", "padokvideolari", "idmanpisti", "canli", "yayin", "tv"):
    for ek in ("/", "/" + bugun.strftime("%Y") + "/"):
        u = "https://video-cdn.tjk.org/videoftp/" + yol + ek; c, n = head(u); P("KLASÖR", c, u)
for u in ("https://video-cdn.tjk.org/", "https://video-cdn.tjk.org/videoftp/", "https://medya-cdn.tjk.org/"):
    t, c = get(u, 3000); P("KÖK", c, u, re.sub(r"\s+", " ", t)[:200])
open("data/padok_probe.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
