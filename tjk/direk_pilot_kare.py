"""T124 pilot adım 1: 4 videodan kare örnekleri (direk/işaret nasıl görünüyor?). Actions'ta çalışır."""
import os, subprocess, json, glob
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
H = {"adana":1,"izmir":2,"istanbul":3,"bursa":4,"ankara":5}
adaylar = []
for f in sorted(glob.glob("data/video_seyir/2026-10-2*_*.json")):
    j = json.load(open(f))
    if len(j.get("bolum", {})) >= 4:
        b = os.path.basename(f)[:-5]; t, hip, k = b.split("_")
        if hip in H: adaylar.append((t, hip, int(k)))
import random; random.Random(1).shuffle(adaylar)
os.makedirs("data/direk_pilot", exist_ok=True)
n = 0
for t, hip, k in adaylar:
    if n >= 4: break
    y, a, g = t[:4], str(int(t[5:7])), t[2:4]+t[5:7]+t[8:10]
    u = f"https://video-cdn.tjk.org/videoftp/{y}/{a}/{g}{H[hip]}{k}_m.mp4"
    yol = "/tmp/v.mp4"
    c = subprocess.run(["curl","-s","-m","120","-A",UA,"-e","https://www.tjk.org/","-o",yol,"-w","%{http_code}",u],capture_output=True,text=True).stdout
    if c != "200": print("yok", c, u); continue
    ad = f"{t}_{hip}_{k}"
    subprocess.run(["ffmpeg","-v","error","-y","-i",yol,"-vf","fps=1/6,scale=640:-1","-frames:v","14","-q:v","5",f"data/direk_pilot/{ad}_%02d.jpg"])
    print("ok", u, json.load(open(f"data/video_seyir/{ad}.json"))["bolum"]); n += 1
