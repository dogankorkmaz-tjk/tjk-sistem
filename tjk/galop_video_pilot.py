"""Galop videosu pilotu (yalnız betimleyici): ~20 at x 3 video; adım sıklığı (FFT) ve tutarlılık. GitHub Actions'ta çalışır (video-cdn yalnız oradan açık).
Çıktı: data/galop_video_pilot.csv"""
import os, glob, subprocess, json, re, sys, tempfile, numpy as np, pandas as pd
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
g = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/galop/20*.csv.gz"))], ignore_index=True)
g = g[g.video.notna() & g.p400.notna() & g.tur.astype(str).str.contains("Galop", case=False)].copy()
g = g[g.it >= sorted(g.it.unique())[-60]]                      # son 60 gün
g = g[g.hip.isin(["İstanbul", "Ankara", "İzmir", "Bursa"])]
c = g.groupby("at_id").video.nunique(); ids = list(c[c >= 3].index)
rng = np.random.default_rng(123); rng.shuffle(ids); ids = ids[:20]
S = g[g.at_id.isin(ids)].sort_values("it").groupby("at_id").head(3)
print("seçilen video", len(S), "at", S.at_id.nunique(), flush=True)
def bilgi(yol):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration", "-of", "json", yol], capture_output=True, text=True)
    try:
        s = json.loads(r.stdout)["streams"][0]; a, b = s["r_frame_rate"].split("/"); return int(s["width"]), int(s["height"]), float(a) / float(b), float(s.get("duration") or 0)
    except Exception: return 0, 0, 0.0, 0.0
def kareler(yol, w=320, h=180):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", yol, "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.uint8); n = len(a) // (w * h); return a[: n * w * h].reshape(n, h, w).astype(np.float32)
def adim(F, fps):
    """hareket enerjisi: ardışık kare farkının en hareketli bölgedeki ortalaması; zaman serisinin FFT tepe noktası (1,2-3,5 Hz)"""
    if len(F) < 40: return np.nan, np.nan, 0.0
    D = np.abs(np.diff(F, axis=0)); en = D.mean(axis=(1, 2)); aktif = en > np.percentile(en, 60)
    if aktif.sum() < 30: return np.nan, np.nan, float(aktif.mean())
    # atın geçtiği bölge: hareketin yoğun olduğu satır/sütun bandı
    Dm = D[aktif].mean(axis=0); ys, xs = np.where(Dm > np.percentile(Dm, 95)); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    s = D[:, y0:y1, x0:x1].mean(axis=(1, 2)); idx = np.where(aktif)[0]; seg = s[idx.min(): idx.max() + 1]
    if len(seg) < 30: return np.nan, np.nan, float(aktif.mean())
    seg = seg - np.convolve(seg, np.ones(15) / 15, mode="same"); seg = seg * np.hanning(len(seg))
    P = np.abs(np.fft.rfft(seg, n=max(512, 4 * len(seg)))) ** 2; f = np.fft.rfftfreq(max(512, 4 * len(seg)), d=1.0 / fps)
    m = (f >= 1.2) & (f <= 3.5); k = np.argmax(P[m]); tepe = P[m][k] / (P[m].sum() + 1e-9)
    return float(f[m][k]), float(tepe), float(aktif.mean())
rows = []
with tempfile.TemporaryDirectory() as td:
    for r in S.itertuples():
        yol = os.path.join(td, "v.mp4")
        k = subprocess.run(["curl", "-s", "-m", "120", "-A", UA, "-e", "https://www.tjk.org/", "-o", yol, "-w", "%{http_code}", r.video], capture_output=True, text=True).stdout.strip()
        if k != "200" or not os.path.exists(yol) or os.path.getsize(yol) < 50000:
            rows.append(dict(at_id=r.at_id, at=r.at, it=r.it, hip=r.hip, p400=r.p400, video=r.video, durum="indirilemedi " + k)); print("indirilemedi", k, r.video, flush=True); continue
        w, h, fps, dur = bilgi(yol)
        try:
            F = kareler(yol); hz, tepe, ak = adim(F, fps if fps > 0 else 25.0)
        except Exception as e:
            hz, tepe, ak = np.nan, np.nan, 0.0; print("hata", repr(e), flush=True)
        rows.append(dict(at_id=r.at_id, at=r.at, it=r.it, hip=r.hip, pist=r.pist, p400=r.p400, p600=r.p600, w=w, h=h, fps=round(fps, 2), sure=round(dur, 1), boyut=os.path.getsize(yol), kare=len(F) if 'F' in dir() else 0, adim_hz=hz, tepe=tepe, aktif=ak, video=r.video, durum="ok"))
        print(rows[-1]["at"], rows[-1]["it"], w, h, fps, round(dur, 1), hz, tepe, flush=True); os.remove(yol)
pd.DataFrame(rows).to_csv("data/galop_video_pilot.csv", index=False)
D = pd.DataFrame(rows); D = D[D.durum == "ok"]
print("başarılı", len(D), "| adım Hz ortalama", D.adim_hz.mean(), "std", D.adim_hz.std())
if len(D) > 10:
    gm = D.groupby("at_id").adim_hz.agg(["mean", "var", "count"]); gm = gm[gm["count"] >= 2]
    if len(gm) > 3:
        ic = (gm["mean"].var() - gm["var"].mean() / gm["count"].mean()) / (gm["mean"].var() + 1e-9); print("ICC kaba (at ortalaması varyansı / toplam):", round(float(ic), 3), "at sayısı", len(gm))
    print("adım Hz ile 400 m süre korelasyonu:", D[["adim_hz", "p400"]].corr().iloc[0, 1])
