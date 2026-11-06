"""TJK TV canlı akışından kare örnekleri (padok/galop görüntüsü var mı?). Yalnız kendi analizim için; Actions'ta çalışır.
Her çalışmada: akışın erişilebilirliği + SURE sn boyunca ARALIK sn'de bir kare -> data/padok_kare/<gün>/."""
import os, subprocess, datetime, sys
URL = "https://tjktv-live.tjk.org/taytv/taytv.m3u8"
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
SURE = int(sys.argv[1]) if len(sys.argv) > 1 else 900
ARALIK = int(sys.argv[2]) if len(sys.argv) > 2 else 30
GEN = int(sys.argv[3]) if len(sys.argv) > 3 else 480      # T143-B: 640 px, 1 sn
gun = datetime.datetime.utcnow().strftime("%Y-%m-%d")
sa = datetime.datetime.utcnow().strftime("%H%M")
r = subprocess.run(["curl", "-s", "-m", "30", "-A", UA, "-e", "https://www.tjk.org/", "-o", "/tmp/m.m3u8", "-w", "%{http_code}", URL], capture_output=True, text=True)
print("m3u8 http", r.stdout, os.path.getsize("/tmp/m.m3u8") if os.path.exists("/tmp/m.m3u8") else 0)
if r.stdout != "200":
    sys.exit(0)
print(open("/tmp/m.m3u8").read()[:600])
d = f"data/padok_kare/{gun}"; os.makedirs(d, exist_ok=True)
import time; open(f"{d}/{sa}_baslangic.txt", "w").write(str(time.time()))   # ilk karenin yaklaşık epoch zamanı (kare i = başlangıç + (i-1)·ARALIK sn)
p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-user_agent", UA, "-headers", "Referer: https://www.tjk.org/\r\n", "-i", URL, "-t", str(SURE),
                    "-vf", f"fps=1/{ARALIK},scale={GEN}:-2", "-q:v", "7", f"{d}/{sa}_%05d.jpg"], capture_output=True, text=True)
print("ffmpeg rc", p.returncode, p.stderr[-400:])
print("kare", len([f for f in os.listdir(d) if f.startswith(sa)]))
