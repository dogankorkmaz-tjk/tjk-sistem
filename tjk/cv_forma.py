"""T143-D görüntü pilotu (7 Kasım 2026): bitiş karelerinde at kimliği — jokey forması + eyer örtüsü rengi eşleştirmesi.
Girdi: data/cv_pilot/liste.txt (ad bitiş_sn hd_url) + data/atyarisi arşivi (forma görselleri, resmî sıra). Çıktı: data/cv_forma/<ad>.json, data/cv_forma/ozet.txt, ornek/<ad>.jpg."""
import os, json, gzip, subprocess, tempfile, time, glob
import numpy as np, cv2
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr
from ultralytics import YOLO
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
M = YOLO("yolov8s.pt"); os.makedirs("data/cv_forma/ornek", exist_ok=True)
EYER = {1: (220, 30, 30), 2: (30, 60, 200), 3: (240, 140, 30), 4: (40, 160, 70), 5: (20, 20, 20), 6: (120, 40, 160), 7: (60, 170, 230), 8: (110, 40, 30), 9: (200, 170, 90), 10: (170, 150, 220)}
def hist(img, mask=None):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); h = cv2.calcHist([hsv], [0, 1], mask, [18, 8], [0, 180, 0, 256]); cv2.normalize(h, h, 1, 0, cv2.NORM_L1); return h
def forma_ref(url, d):
    p = f"{d}/f_{abs(hash(url))}.jpg"
    if not os.path.exists(p):
        subprocess.run(["curl", "-s", "-m", "30", "-A", UA, "-e", "https://www.tjk.org/", "-o", p, url]); time.sleep(0.5)
    im = cv2.imread(p)
    if im is None: return None
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); mask = ((g < 235) & (g > 0)).astype(np.uint8) * 255   # beyaz zemin dışı
    return hist(im, mask)
def renk_uz(bgr_ort, no):
    if no not in EYER: return 0.5
    r, g, b = EYER[no]; return float(np.linalg.norm(np.array([b, g, r]) - bgr_ort) / 442.0)
OZ = []
for satir in open("data/cv_pilot/liste.txt").read().split("\n"):
    if not satir.strip(): continue
    ad, fin, url = satir.split(); fin = float(fin); gun = ad[:10]; hip = ad.split("_")[1]; kn = int(ad.split("_")[-1])
    try:
        x = json.load(gzip.open(f"data/atyarisi/{gun}.json.gz")); R = [r for r in x["sonuc"][hip] if int(r["number"]) == kn][0]
    except Exception as e:
        print(ad, "arşiv yok", e); continue
    H = [h for h in R["horses"] if h.get("order")]; resmi = {int(h["number"]): int(h["order"]) for h in H}
    with tempfile.TemporaryDirectory() as d:
        ref = {int(h["number"]): forma_ref(h.get("uniformImageURL") or "", d) for h in H}
        mp4 = f"{d}/v.mp4"; r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", url], capture_output=True, text=True); time.sleep(2)
        if r.stdout.strip() != "200": print(ad, "video yok"); continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, fin - 3)), "-i", mp4, "-t", "4", "-vf", "fps=10", "-q:v", "2", f"{d}/k_%03d.jpg"], check=True)
        K = sorted(glob.glob(f"{d}/k_*.jpg")); kare_sonuc = []
        # koşu yönü: kamera atları izler → arka plan ters yöne akar; arka plan sola akıyorsa atlar sağa gidiyor (ön = büyük x)
        dxs = []
        for f1, f2 in zip(K[:-1:4], K[1::4]):
            g1 = cv2.resize(cv2.imread(f1, 0), (480, 270)); g2 = cv2.resize(cv2.imread(f2, 0), (480, 270))
            fl = cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 3, 15, 3, 5, 1.2, 0); dxs.append(float(np.median(fl[..., 0])))
        sag = (np.median(dxs) if dxs else -1) < 0
        for i, f in enumerate(K):
            im = cv2.imread(f); res = M.predict(im, classes=[0, 17], conf=0.15, imgsz=1280, verbose=False)[0]
            bx = [(int(c), [float(v) for v in b]) for c, b in zip(res.boxes.cls, res.boxes.xyxy)]
            atlar = [b for c, b in bx if c == 17]; jok = [b for c, b in bx if c == 0]
            adaylar = []
            for a in atlar:   # atın üstündeki jokey: merkez atın üst yarısında
                ax = (a[0] + a[2]) / 2; js = [j for j in jok if a[0] <= (j[0] + j[2]) / 2 <= a[2] and j[3] <= a[1] + 0.75 * (a[3] - a[1])]
                if not js: continue
                j = min(js, key=lambda j: abs((j[0] + j[2]) / 2 - ax))
                x0, y0, x1, y1 = map(int, j); y1f = int(y0 + 0.55 * (y1 - y0))
                fo = im[max(0, y0):max(y0 + 1, y1f), max(0, x0):max(x0 + 1, x1)]
                ey = im[int(y1 - 0.15 * (y1 - y0)):int(min(a[3], y1 + 0.25 * (a[3] - a[1]))), int(x0):int(x1)]
                if fo.size == 0: continue
                adaylar.append(dict(kutu=a, h=hist(fo), ey=ey.reshape(-1, 3).mean(0) if ey.size else np.array([128, 128, 128])))
            nos = [n for n in resmi if ref.get(n) is not None]
            if len(adaylar) < 2 or not nos: kare_sonuc.append(None); continue
            C = np.array([[cv2.compareHist(q["h"], ref[n], cv2.HISTCMP_BHATTACHARYYA) + 0.5 * renk_uz(q["ey"], n) for n in nos] for q in adaylar])
            ri, ci = linear_sum_assignment(C)
            es = sorted([((adaylar[r_]["kutu"][2] if sag else -adaylar[r_]["kutu"][0]), nos[c_]) for r_, c_ in zip(ri, ci)], key=lambda z: -z[0])   # önden geriye (yön akıştan)
            kare_sonuc.append([n for _, n in es])
            if i == len(K) * 3 // 4:
                o = im.copy()
                for r_, c_ in zip(ri, ci):
                    b = list(map(int, adaylar[r_]["kutu"])); cv2.rectangle(o, b[:2], b[2:], (0, 255, 255), 2); cv2.putText(o, str(nos[c_]), (b[0], b[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
                cv2.imwrite(f"data/cv_forma/ornek/{ad}.jpg", cv2.resize(o, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 70])
        son = [k for k in kare_sonuc[-12:-2] if k]          # bitişe en yakın kareler
        if not son: print(ad, "eşleşme yok"); OZ.append(dict(ad=ad, n=len(resmi), on_dogru=None, rho=None)); continue
        oy = {}
        for k in son[-5:]:
            if k: oy[k[0]] = oy.get(k[0], 0) + 1
        on = max(oy, key=oy.get); son_k = son[-1]
        rho = spearmanr(range(len(son_k)), [resmi[n] for n in son_k])[0] if len(son_k) >= 3 else np.nan
        OZ.append(dict(ad=ad, n=len(resmi), gorulen=len(son_k), on_at=on, birinci=[n for n, o in resmi.items() if o == 1][0], on_dogru=resmi.get(on) == 1, rho=None if np.isnan(rho) else round(float(rho), 2), yon="sağa" if sag else "sola"))
        json.dump(dict(ad=ad, kareler=kare_sonuc, resmi=resmi), open(f"data/cv_forma/{ad}.json", "w"))
        print(OZ[-1], flush=True)
ok = [o for o in OZ if o.get("on_dogru") is not None]; rh = [o["rho"] for o in OZ if o.get("rho") is not None]
s = f"T143-D: {len(OZ)} koşu, eşleşen {len(ok)} | öndeki atı doğru bilme %{100 * np.mean([o['on_dogru'] for o in ok]):.0f} (rastgele ≈ %{100 * np.mean([1 / o['n'] for o in ok]):.0f}) | sıra Spearman ortalama {np.mean(rh):+.2f} ({len(rh)} koşu)" if ok else "T143-D: eşleşme yok"
print(s); open("data/cv_forma/ozet.txt", "w").write(s + "\n" + "\n".join(json.dumps(o, ensure_ascii=False) for o in OZ) + "\n")
