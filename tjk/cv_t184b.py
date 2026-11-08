"""T184-B: yalnız kamera kayması, yeniden hesap (ön kayıt hipotez_defteri T184-B). Tam kare yerine pist bölgesi: üst %75, sol/sağ %10 kırpılı, Hann pencereli faz korelasyonu;
10 kare/sn ardışık karelerde. Çıktı data/cv_t184b/<ad>.json: {"kayma":[[t,dx,resp],...]} (px@640). Kullanım: python3 tjk/cv_t184b.py <parça> <parça_sayısı>"""
import os, sys, json, subprocess, tempfile, time, glob
import numpy as np, cv2
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
p, n = int(sys.argv[1]), int(sys.argv[2])
L = [s.split() for s in open("data/cv_t184/liste.txt").read().split("\n") if s.strip()][p::n]
for ad, url in L:
    if os.path.exists(f"data/cv_t184b/{ad}.json") or not os.path.exists(f"data/cv_t184/{ad}.json"): continue
    t0 = time.time()
    with tempfile.TemporaryDirectory() as d:
        mp4 = f"{d}/v.mp4"; ok = False
        for u in (url, url.replace(".mp4", "_m.mp4")):
            r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", u], capture_output=True, text=True); time.sleep(1.5)
            if r.stdout.strip() == "200": ok = True; break
        if not ok: print(ad, "indirilemedi", flush=True); continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=10,scale=640:-2,format=gray", f"{d}/k_%05d.png"], check=True)
        K = sorted(glob.glob(f"{d}/k_*.png")); kayma = []; onceki = None; win = None
        for i, f in enumerate(K):
            g = cv2.imread(f, 0).astype(np.float32); h, w = g.shape
            g = g[: int(h * 0.75), int(w * 0.10): int(w * 0.90)]
            if win is None: win = cv2.createHanningWindow((g.shape[1], g.shape[0]), cv2.CV_32F)
            if onceki is not None and onceki.shape == g.shape:
                (dx, dy), resp = cv2.phaseCorrelate(onceki, g, win); kayma.append([round(i / 10, 1), round(float(dx), 2), round(float(resp), 2)])
            onceki = g
        json.dump({"ad": ad, "kayma": kayma}, open(f"data/cv_t184b/{ad}.json", "w"), separators=(",", ":"))
        a = np.abs(np.array(kayma)[:, 1]) if kayma else np.zeros(1)
        print(ad, len(kayma), "kare | medyan |dx|", round(float(np.median(a)), 2), "| %", round(float((a > 1).mean()), 2), "| ", round(time.time() - t0), "sn", flush=True)
