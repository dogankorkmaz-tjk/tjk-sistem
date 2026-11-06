"""Görüntü pilotu (6 Kasım 2026, onay 23:29): HD yarış videosunda YOLO (yolov8n, COCO 'horse'=17, 'person'=0) at/jokey tespiti.
Girdi: data/cv_pilot/liste.txt (ad bitiş_sn hd_url). Bitiş penceresi: bitiş−5 sn .. +1 sn, 10 kare/sn; start penceresi: 0–8 sn, 5 kare/sn.
Çıktı: data/cv_pilot/<ad>.json (kare başına kutular) + data/cv_pilot/ornek/<ad>_{bitis,start}.jpg (işaretli örnek kareler)."""
import os, sys, json, subprocess, tempfile, time, glob
from ultralytics import YOLO
import cv2

UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
M = YOLO("yolov8n.pt"); os.makedirs("data/cv_pilot/ornek", exist_ok=True)


def kareler(mp4, bas, sure, fps, d):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, bas)), "-i", mp4, "-t", str(sure), "-vf", f"fps={fps}", "-q:v", "3", f"{d}/k_%04d.jpg"], check=True)
    return sorted(glob.glob(f"{d}/k_*.jpg"))


for satir in open("data/cv_pilot/liste.txt").read().split("\n"):
    if not satir.strip(): continue
    ad, fin, url = satir.split(); fin = float(fin); t0 = time.time()
    with tempfile.TemporaryDirectory() as d:
        mp4 = f"{d}/v.mp4"
        r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", url], capture_output=True, text=True); time.sleep(2)
        if r.stdout.strip() != "200": print(ad, "indirilemedi", r.stdout); continue
        boy = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip()
        out = {"ad": ad, "bitis_sn": fin, "cozunurluk": boy, "pencere": {}}
        for pn, bas, sure, fps in (("bitis", fin - 5, 6, 10), ("start", 0, 8, 5)):
            dd = f"{d}/{pn}"; os.makedirs(dd); K = kareler(mp4, bas, sure, fps, dd); L = []
            for i, f in enumerate(K):
                res = M.predict(f, classes=[0, 17], conf=0.25, verbose=False)[0]
                B = [[int(c), round(float(s), 3)] + [round(float(x), 1) for x in b] for c, s, b in zip(res.boxes.cls, res.boxes.conf, res.boxes.xyxy)]
                L.append({"t": round(bas + i / fps, 2), "kutu": B})
                if i == len(K) * 3 // 4 if pn == "bitis" else i == len(K) // 2:
                    cv2.imwrite(f"data/cv_pilot/ornek/{ad}_{pn}.jpg", cv2.resize(res.plot(), None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 70])
            out["pencere"][pn] = L
        json.dump(out, open(f"data/cv_pilot/{ad}.json", "w"))
        at = [sum(1 for b in x["kutu"] if b[0] == 17) for x in out["pencere"]["bitis"]]
        print(ad, boy, "bitiş penceresi kare başına at kutusu medyan", sorted(at)[len(at) // 2], "| sn", round(time.time() - t0))
