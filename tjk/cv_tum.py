"""T183 görüntü pilotu: TÜM KOŞU boyunca kamera kapsamı (fazladan mesafe/yan konum ölçülebilir mi?). Betimsel; üretime yazmaz.
Girdi: data/cv_pilot/liste.txt (ad bitiş_sn hd_url). 1 kare/sn, yolov8s, at kutuları (COCO 17, güven ≥0,25, imgsz 960).
Çıktı: data/cv_tum/<ad>.json (saniye başına kutular [x1,y1,x2,y2,güven]), data/cv_tum/ozet.txt, data/cv_tum/ornek/ (her koşudan 4 işaretli kare)."""
import os, sys, json, subprocess, tempfile, time, glob
import numpy as np, cv2
from ultralytics import YOLO

UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
M = YOLO("yolov8s.pt"); os.makedirs("data/cv_tum/ornek", exist_ok=True)
OZ = []
for satir in open("data/cv_pilot/liste.txt").read().split("\n"):
    if not satir.strip(): continue
    ad, fin, url = satir.split(); fin = float(fin); t0 = time.time()
    with tempfile.TemporaryDirectory() as d:
        mp4 = f"{d}/v.mp4"
        r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", url], capture_output=True, text=True); time.sleep(2)
        if r.stdout.strip() != "200": print(ad, "indirilemedi", r.stdout, flush=True); continue
        sure = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip() or 0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=1,scale=1280:-2", "-q:v", "3", f"{d}/k_%04d.jpg"], check=True)
        K = sorted(glob.glob(f"{d}/k_*.jpg")); L = []; sec = []
        for i, f in enumerate(K):
            res = M.predict(f, classes=[17], conf=0.25, imgsz=960, verbose=False)[0]
            B = [[round(float(x), 1) for x in b] + [round(float(c), 2)] for b, c in zip(res.boxes.xyxy, res.boxes.conf)]
            L.append({"t": i, "kutu": B}); sec.append(len(B))
            if i in (len(K) // 5, 2 * len(K) // 5, 3 * len(K) // 5, 4 * len(K) // 5):
                cv2.imwrite(f"data/cv_tum/ornek/{ad}_{i:03d}.jpg", cv2.resize(res.plot(), None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 65])
        json.dump({"ad": ad, "sure": sure, "bitis_sn": fin, "kare": L}, open(f"data/cv_tum/{ad}.json", "w"), separators=(",", ":"))
        a = np.array(sec); n = len(a)
        dil = lambda lo, hi: round(float((a[int(n * lo):int(n * hi)] >= 5).mean()), 2) if n else None
        OZ.append(f"{ad} sure {sure:.0f}s kare {n} | ≥5 at: tüm {round(float((a>=5).mean()),2)} | start-ilk%20 {dil(0,.2)} orta {dil(.2,.8)} son%20 {dil(.8,1)} | ≥3 at {round(float((a>=3).mean()),2)} | medyan kutu {int(np.median(a))} | {round(time.time()-t0)} sn")
        print(OZ[-1], flush=True)
tum = [float(s.split("tüm ")[1].split(" ")[0]) for s in OZ]
open("data/cv_tum/ozet.txt", "w", encoding="utf-8").write("\n".join(OZ) + f"\nKOŞU {len(OZ)}; ≥5 at görülen kare payı medyan {np.median(tum):.2f}, ortalama {np.mean(tum):.2f}\n")
