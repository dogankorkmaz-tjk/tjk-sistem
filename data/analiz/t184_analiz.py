"""T184 analiz (ön kayıt hipotez_defteri; algılama sonuçları GÖRÜLMEDEN yazıldı). Videodan yan konum (LAT) vs Accurace fazladan mesafe (FM).
Çalıştır: python3 data/analiz/t184_analiz.py  → data/analiz/t184_sonuc.txt"""
import json, glob, gzip, os, re
import numpy as np
from scipy.stats import spearmanr, rankdata
rng = np.random.default_rng(184)

def start_no(gun, hip, k):
    f = f"data/atyarisi/{gun}.json.gz"
    if not os.path.exists(f): return {}
    try: x = json.load(gzip.open(f))
    except Exception: return {}
    for r in (x.get("program") or {}).get(hip) or []:
        if int(r.get("number") or 0) == k:
            out = {}
            for h in r.get("horses") or []:
                try: out[int(h["number"])] = int(h.get("start"))
                except Exception: pass
            return out
    return {}

R = []; say = dict(koşu=0, kare_toplam=0, kare_yonlu=0, kare_kullanilan=0)
for f in sorted(glob.glob("data/cv_t184/20*.json")):
    ad = os.path.basename(f)[:-5]
    if not os.path.exists(f"data/accurace/{ad}.json") or not os.path.exists(f"data/video_seyir/{ad}.json"): continue
    A = json.load(open(f"data/accurace/{ad}.json")); V = json.load(open(f"data/video_seyir/{ad}.json")); C = json.load(open(f))
    km = {int(a["no"]): float(a["kosulan_mesafe"]) for a in A.get("atlar", []) if a.get("no") is not None and isinstance(a.get("kosulan_mesafe"), (int, float)) and a["kosulan_mesafe"] > 0}
    if len(km) < 5: continue
    mn = min(km.values()); FM = {n: v - mn for n, v in km.items()}
    alan = len(V.get("numaralar") or km)
    Z = {round(z["t"] * 2) / 2: z["sira"] for z in (V.get("zaman") or []) if z.get("sira")}
    kay = np.array(C.get("kayma") or [[0, 0, 0]], float)
    dur = C.get("sure") or (C["kare"][-1]["t"] if C["kare"] else 0)
    say["koşu"] += 1; lat = {}
    for fr in C["kare"]:
        t = fr["t"]; say["kare_toplam"] += 1
        if t > 0.85 * dur: continue
        w = kay[(kay[:, 0] >= t - 1) & (kay[:, 0] <= t + 1), 1].sum()
        if abs(w) < 5: continue
        say["kare_yonlu"] += 1; yon = -np.sign(w)           # +1: atlar sağa koşuyor
        B = [b for b in fr["kutu"] if (b[3] - b[1]) > 4]
        s = Z.get(round(t * 2) / 2)
        if not s or len(B) < 3 or len(B) < 0.75 * alan: continue
        B = sorted(B, key=lambda b: -yon * (b[0] + b[2]) / 2)    # koşu yönünde önden arkaya
        h = np.array([b[3] - b[1] for b in B]); mh = np.median(h)
        say["kare_kullanilan"] += 1
        for i in range(min(len(B), len(s))):
            lat.setdefault(int(s[i]), []).append(float(np.log(h[i] / mh)))
    LAT = {n: float(np.mean(v)) for n, v in lat.items() if len(v) >= 5 and n in FM}
    if len(LAT) < 5: continue
    ns = sorted(LAT); x = np.array([LAT[n] for n in ns]); y = np.array([FM[n] for n in ns])
    rho = spearmanr(x, y)[0]
    st = start_no(ad[:10], ad[11:].rsplit("_", 1)[0], int(ad.rsplit("_", 1)[1])); kr = None; rs = None
    if all(n in st for n in ns):
        g = np.array([st[n] for n in ns], float)
        def art(v):   # sıra dönüşümü, kapıya göre doğrusal artık
            r_ = rankdata(v); gr = rankdata(g); b = np.polyfit(gr, r_, 1); return r_ - np.polyval(b, gr)
        if np.std(g) > 0: kr = float(np.corrcoef(art(x), art(y))[0, 1]); rs = spearmanr(g, y)[0]
    if not np.isnan(rho): R.append(dict(ad=ad, gun=ad[:10], n=len(ns), alan=alan, rho=float(rho), kismi=kr, kapi_rho=rs))

out = [f"koşu (analize giren, ≥5 ölçülmüş at) {len(R)} / algılanan {say['koşu']}; kare: toplam {say['kare_toplam']}, yönlü {say['kare_yonlu']}, kullanılan {say['kare_kullanilan']}"]
def boot(v, g):
    v = np.asarray(v, float); g = np.asarray(g); ug = np.unique(g); idx = {u: np.where(g == u)[0] for u in ug}; b = []
    for _ in range(3000):
        s = np.concatenate([idx[u] for u in rng.choice(ug, len(ug))]); b.append(v[s].mean())
    return np.percentile(b, [2.5, 97.5])
if R:
    rho = [r["rho"] for r in R]; g = [r["gun"] for r in R]; lo, hi = boot(rho, g)
    out.append(f"BİRİNCİL koşu içi Spearman(LAT, FM) ort {np.mean(rho):+.3f} [{lo:+.3f}; {hi:+.3f}] medyan {np.median(rho):+.3f}")
    K = [r for r in R if r["kismi"] is not None and not np.isnan(r["kismi"])]
    if K:
        lo2, hi2 = boot([r["kismi"] for r in K], [r["gun"] for r in K])
        out.append(f"İKİNCİL kapı kontrollü kısmi korelasyon ort {np.mean([r['kismi'] for r in K]):+.3f} [{lo2:+.3f}; {hi2:+.3f}] (n {len(K)}) | karşılaştırma: Spearman(kapı, FM) ort {np.nanmean([r['kapi_rho'] for r in K]):+.3f}")
    out.append(f"kapsama: ölçülmüş at / alan ortalama {np.mean([r['n']/r['alan'] for r in R]):.2f}")
    for hp in sorted({r["ad"][11:].rsplit('_',1)[0] for r in R}):
        q = [r["rho"] for r in R if r["ad"][11:].rsplit('_',1)[0] == hp]; out.append(f"  {hp}: n {len(q)} ort {np.mean(q):+.3f}")
    m = np.mean(rho)
    out.append("KARAR: " + ("ÖLÇÜLEBİLİR → T185 (ön kayıtla)" if m >= 0.50 and lo > 0.35 else "ZAYIF ÖLÇÜM → tek iyileştirme denemesi (ayrı ön kayıt)" if m >= 0.25 else "TERS İŞARET (kamera konumu varsayımı yanlış?) → ayrı ön kayıt" if m <= -0.25 else "ÖLÇÜLEMEDİ → teşhis"))
open("data/analiz/t184_sonuc.txt", "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
