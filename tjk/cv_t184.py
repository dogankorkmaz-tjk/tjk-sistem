"""T184 algılama (ön kayıt hipotez_defteri): Accurace'lı koşuların HD videosunda tüm koşu boyunca at kutuları + kamera yatay kayması.
Kullanım: python3 tjk/cv_t184.py <parça_no> <parça_sayısı>. Girdi data/cv_t184/liste.txt (ad url). Çıktı data/cv_t184/<ad>.json:
 {"ad","sure","W","H","kare":[{"t":sn,"kutu":[[x1,y1,x2,y2,güven],...]}] (2 kare/sn), "kayma":[[t,dx],...] (0,1 sn aralıklı ardışık kareler arası yatay kayma, px@640 genişlik)}.
Üretime yazmaz. Analiz ayrı (data/analiz/t184_analiz.py)."""
import os, sys, json, subprocess, tempfile, time, glob
import numpy as np, cv2
from ultralytics import YOLO
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
p, n = int(sys.argv[1]), int(sys.argv[2])
L = [s.split() for s in open("data/cv_t184/liste.txt").read().split("\n") if s.strip()][p::n]
M = YOLO("yolov8s.pt")
for ad, url in L:
    if os.path.exists(f"data/cv_t184/{ad}.json"): continue
    t0 = time.time()
    with tempfile.TemporaryDirectory() as d:
        mp4 = f"{d}/v.mp4"; ok = False
        for u in (url, url.replace(".mp4", "_m.mp4")):
            r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", u], capture_output=True, text=True); time.sleep(1.5)
            if r.stdout.strip() == "200": ok = True; break
        if not ok: print(ad, "indirilemedi", flush=True); continue
        WH = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip().split(",")
        sure = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip() or 0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=10", "-q:v", "4", f"{d}/k_%05d.jpg"], check=True)
        K = sorted(glob.glob(f"{d}/k_*.jpg")); kayma = []; kare = []; onceki = None
        for i, f in enumerate(K):
            im = cv2.imread(f); g = cv2.cvtColor(cv2.resize(im, (640, int(640 * im.shape[0] / im.shape[1]))), cv2.COLOR_BGR2GRAY).astype(np.float32)
            if onceki is not None:
                (dx, dy), resp = cv2.phaseCorrelate(onceki, g); kayma.append([round(i / 10, 1), round(float(dx), 2), round(float(resp), 2)])
            onceki = g
            if i % 5 == 0:
                res = M.predict(im, classes=[17], conf=0.20, imgsz=1280, verbose=False)[0]
                kare.append({"t": round(i / 10, 1), "kutu": [[round(float(x), 1) for x in b] + [round(float(c), 2)] for b, c in zip(res.boxes.xyxy, res.boxes.conf)]})
        json.dump({"ad": ad, "sure": sure, "W": int(WH[0]), "H": int(WH[1]), "kare": kare, "kayma": kayma}, open(f"data/cv_t184/{ad}.json", "w"), separators=(",", ":"))
        print(ad, WH, f"{sure:.0f}s", len(kare), "kare", round(time.time() - t0), "sn", flush=True)
