"""T184 analiz (ön kayıt hipotez_defteri; algılama sonuçları GÖRÜLMEDEN yazıldı). Videodan yan konum (LAT) vs Accurace fazladan mesafe (FM).
Çalıştır: python3 data/analiz/t184_analiz.py  → data/analiz/t184b_sonuc.txt"""
import json, glob, gzip, os, re
import numpy as np
from scipy.stats import spearmanr, rankdata
rng = np.random.default_rng(1841)

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

D = []; R = []; say = dict(koşu=0, kare_toplam=0, kare_yonlu=0, kare_kullanilan=0)
for f in sorted(glob.glob("data/cv_t184/20*.json")):
    ad = os.path.basename(f)[:-5]
    if not os.path.exists(f"data/accurace/{ad}.json") or not os.path.exists(f"data/video_seyir/{ad}.json"): continue
    A = json.load(open(f"data/accurace/{ad}.json")); V = json.load(open(f"data/video_seyir/{ad}.json")); C = json.load(open(f))
    km = {int(a["no"]): float(a["kosulan_mesafe"]) for a in A.get("atlar", []) if a.get("no") is not None and isinstance(a.get("kosulan_mesafe"), (int, float)) and a["kosulan_mesafe"] > 0}
    if len(km) < 5: continue
    mn = min(km.values()); FM = {n: v - mn for n, v in km.items()}
    alan = len(V.get("numaralar") or km)
    Z = {round(z["t"] * 2) / 2: z["sira"] for z in (V.get("zaman") or []) if z.get("sira")}
    kay = np.array(json.load(open(f"data/cv_t184b/{ad}.json")).get("kayma") or [[0, 0, 0]], float) if os.path.exists(f"data/cv_t184b/{ad}.json") else np.array([[0, 0, 0]], float)
    dur = C.get("sure") or (C["kare"][-1]["t"] if C["kare"] else 0)
    say["koşu"] += 1; lat = {}; RK = {}; YB = {}
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
            lat.setdefault(int(s[i]), []).append(float(np.log(h[i] / mh))); RK.setdefault(int(s[i]), []).append(i / max(1, len(B) - 1)); YB.setdefault(int(s[i]), []).append((B[i][3] - np.median([b[3] for b in B])) / mh)
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
    _rk = np.array([np.mean(RK[n]) for n in ns]); _yb = np.array([np.mean(YB[n]) for n in ns]); D.append((spearmanr(x, _rk)[0], spearmanr(_rk, y)[0], spearmanr(_yb, y)[0], spearmanr(x, _yb)[0]))
    if not np.isnan(rho): R.append(dict(ad=ad, gun=ad[:10], n=len(ns), alan=alan, rho=float(rho), kismi=kr, kapi_rho=rs))

D = np.array(D, float)
print("TEŞHİS (koşu içi Spearman ortalamaları, n=%d):" % len(D))
print("  LAT ~ şeritte öndelik sırası (0=önde)      %+.3f" % np.nanmean(D[:,0]))
print("  sıra (öndelik) ~ fazladan mesafe           %+.3f" % np.nanmean(D[:,1]))
print("  kutu tabanı düşey konumu ~ fazladan mesafe %+.3f" % np.nanmean(D[:,2]))
print("  LAT ~ kutu tabanı düşey konumu             %+.3f" % np.nanmean(D[:,3]))
