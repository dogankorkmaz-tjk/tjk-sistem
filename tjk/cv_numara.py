"""T143-E görüntü pilotu (7 Kasım 2026): bitiş karelerinde eyer örtüsü numarasını okuyarak at kimliği.
Girdi: data/cv_pilot/liste.txt + data/atyarisi (resmî sıra). Çıktı: data/cv_numara/<ad>.json, ozet.txt, ornek/<ad>.jpg."""
import os, json, gzip, subprocess, tempfile, time, glob, re
import numpy as np, cv2, pytesseract
from scipy.stats import spearmanr
from ultralytics import YOLO
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
M = YOLO("yolov8s.pt"); os.makedirs("data/cv_numara/ornek", exist_ok=True)
CFG = ["--psm 7 -c tessedit_char_whitelist=0123456789", "--psm 8 -c tessedit_char_whitelist=0123456789"]
def oku(crop, gecerli):
    if crop.size == 0 or crop.shape[0] < 6 or crop.shape[1] < 10: return None
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY); g = cv2.resize(g, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    oy = {}
    for im in (cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]):
        for c in CFG:
            t = re.sub(r"\D", "", pytesseract.image_to_string(im, config=c))
            if t and int(t) in gecerli: oy[int(t)] = oy.get(int(t), 0) + 1
    return max(oy, key=oy.get) if oy else None
def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]); i = max(0, x1 - x0) * max(0, y1 - y0)
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i + 1e-9)
OZ = []
for satir in open("data/cv_pilot/liste.txt").read().split("\n"):
    if not satir.strip(): continue
    ad, fin, url = satir.split(); fin = float(fin); gun = ad[:10]; hip = ad.split("_")[1]; kn = int(ad.split("_")[-1])
    try:
        R = [r for r in json.load(gzip.open(f"data/atyarisi/{gun}.json.gz"))["sonuc"][hip] if int(r["number"]) == kn][0]
    except Exception as e:
        print(ad, "arşiv yok", e); continue
    resmi = {int(h["number"]): int(h["order"]) for h in R["horses"] if h.get("order")}; gec = set(resmi)
    with tempfile.TemporaryDirectory() as d:
        mp4 = f"{d}/v.mp4"; r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", url], capture_output=True, text=True); time.sleep(2)
        if r.stdout.strip() != "200": print(ad, "video yok"); continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, fin - 6)), "-i", mp4, "-t", "7", "-vf", "fps=5", "-q:v", "2", f"{d}/k_%03d.jpg"], check=True)
        K = sorted(glob.glob(f"{d}/k_*.jpg")); izler = []; toplam = okunan = 0; KAR = []
        for i, f in enumerate(K):
            im = cv2.imread(f); res = M.predict(im, classes=[17], conf=0.15, imgsz=1280, verbose=False)[0]
            kare = []
            for b in res.boxes.xyxy:
                x0, y0, x1, y1 = [float(v) for v in b]; w, h = x1 - x0, y1 - y0; toplam += 1
                crop = im[int(y0 + 0.15 * h):int(y0 + 0.65 * h), int(x0 + 0.2 * w):int(x1 - 0.2 * w)]
                no = oku(crop, gec); okunan += no is not None
                # iz: önceki karedeki en çok örtüşen kutuya bağla
                bag = None
                for z in izler:
                    if z["son_kare"] == i - 1 and iou(z["kutu"], (x0, y0, x1, y1)) > 0.3 and (bag is None or iou(z["kutu"], (x0, y0, x1, y1)) > iou(bag["kutu"], (x0, y0, x1, y1))): bag = z
                if bag is None: bag = {"oy": {}}; izler.append(bag)
                bag.update(kutu=(x0, y0, x1, y1), son_kare=i)
                if no is not None: bag["oy"][no] = bag["oy"].get(no, 0) + 1
                kare.append((bag, (x0 + x1) / 2, (x0, y0, x1, y1), no))
            KAR.append(kare)
            if i == len(K) - 6:
                o = im.copy()
                for z, xc, bb, no in kare:
                    cv2.rectangle(o, tuple(map(int, bb[:2])), tuple(map(int, bb[2:])), (0, 255, 255), 2)
                    if no is not None: cv2.putText(o, str(no), (int(bb[0]), int(bb[1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
                cv2.imwrite(f"data/cv_numara/ornek/{ad}.jpg", cv2.resize(o, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 70])
        kimlik = lambda z: max(z["oy"], key=z["oy"].get) if z["oy"] else None
        rhos = []
        for kare in KAR[-8:-3]:
            L = [(xc, kimlik(z)) for z, xc, bb, no in kare if kimlik(z) is not None]
            seen = {}; [seen.setdefault(n, x) for x, n in L]
            if len(seen) >= 3: rhos.append(abs(spearmanr(list(seen.values()), [resmi[n] for n in seen])[0]))
        bulunan = {kimlik(z) for z in izler if kimlik(z) is not None}
        o = dict(ad=ad, n=len(resmi), kutu=toplam, okuma_orani=round(okunan / max(toplam, 1), 3), bulunan_at=len(bulunan), rho_mutlak=round(float(np.mean(rhos)), 2) if rhos else None)
        OZ.append(o); json.dump(dict(o, kimlikler=sorted(bulunan)), open(f"data/cv_numara/{ad}.json", "w")); print(o, flush=True)
oo = [o["okuma_orani"] for o in OZ]; rr = [o["rho_mutlak"] for o in OZ if o["rho_mutlak"] is not None]
s = f"T143-E: {len(OZ)} koşu | okuma oranı ort %{100 * np.mean(oo):.0f} | kimliği bulunan at / koşan ort %{100 * np.mean([o['bulunan_at'] / o['n'] for o in OZ]):.0f} | |Spearman| ort {np.mean(rr):.2f} ({len(rr)} koşu)"
print(s); open("data/cv_numara/ozet.txt", "w").write(s + "\n" + "\n".join(json.dumps(o, ensure_ascii=False) for o in OZ) + "\n")
