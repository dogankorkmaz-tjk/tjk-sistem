"""T105: sürpriz (değer-eğimli) sıralı 5'li (ön kayıt hipotez_defteri T105). python3 data/analiz/t105_surpriz_s5.py"""
"""v3 doğrulama: aylık işaret tutarlılığı + egzotik ROI (v2 vs v3). Ön kayıt: hipotez_defteri 2026-10-24 12:45 (sızıntı denetimi/tutarlılık/ROI maddeleri)."""
import os, sys, glob, itertools, random
from multiprocessing import Pool
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_v3.py")).read(), "entegre_v3", "exec"))
from tjk import besli, tabela, egzotik as E
def smx(s): e = np.exp(s - s.max()); return e / e.sum()
if 0: print("\n== AYLIK TUTARLILIK (v3 − v2, ortalama nats/koşu) ==")
for a in ([] if 1 else test):
    d_ = RES[a]["v3"] - RES[a]["v2"]; print(a, len(d_), " ".join(f"{x:+.4f}" for x in d_.mean(0)), "(kazanan ikili üçlü ilk4 ilk5)")
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/2026-*.csv.gz"))]); PAY = {}
for q in O.itertuples():
    kk = None
    if q.tur in E.K:
        kk = tuple(int(z) for z in str(q.kombo).split("/")); kk = tuple(sorted(kk)) if q.tur == "İKİLİ" else kk
    PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu)), {}).setdefault(q.tur, []).append((kk, float(q.tutar)))
from tjk.besli import G_P
def smx(s): e = np.exp(s - s.max()); return e / e.sum()
POOL = []
for a in test:
    for k, r in enumerate(RES[a]["te"]):
        pr = PAY.get(r["key"])
        if pr and ("SIRALI 5 Lİ BAHİS" in pr or "SIRALI 5 Lİ BAHİS DEVİR" in pr) and len(r["lm"]) >= 5: POOL.append((a, r, pr, RES[a]["S3g"][k, :len(r["lm"])], RES[a]["g3"]))
print("sıralı 5'li havuz koşusu", len(POOL), flush=True)
def kup5(args):
    p, pk, gam = args; G = list(gam); p = [float(x) for x in p]; pk = [float(x) for x in pk]
    o = besli.kupon_g(p, 96, G=G)
    if o is None: return None
    sets, pm_ = o; Wp, Tp = besli._W(pk, G_P); return sets, pm_, besli._prob(Wp, Tp, sets)

def tilt(p, pk, a):
    q = p * (p / pk) ** a; return q / q.sum()
ARGS = []
for al in (0.0, 1.0, 2.0):
    for x in POOL: ARGS.append((tilt(smx(x[3]), smx(x[1]["lm"]), al), smx(x[1]["lm"]), x[4]))
with Pool(2) as pool: out = pool.map(kup5, ARGS, chunksize=8)
import pandas as pd
n = len(POOL); res = {}
for ai, al in enumerate((0.0, 1.0, 2.0)):
    rows = []
    for j, x in enumerate(POOL):
        o = out[ai * n + j]
        if o is None: rows.append(None); continue
        sets, pm_, pq = o; pr = x[2]; hit = all(i in sets[i] for i in range(5)); pay = max([t for _, t in pr.get("SIRALI 5 Lİ BAHİS", [(0, 0.0)])]); v = besli.gecerli_say(sets)
        rows.append((x[1]["gun"], v * 1.25, pay if hit else 0.0, int(hit), "DEVİR" in " ".join(pr)))
    res[al] = rows
ok = [j for j in range(n) if all(res[a][j] is not None for a in res)]
rr = np.random.default_rng(41)
def boot(al, B=4000):
    gun = np.array([res[0.0][j][0] for j in ok]); ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}
    b0 = np.array([res[0.0][j][1] for j in ok]); k0 = np.array([res[0.0][j][2] for j in ok]); b1 = np.array([res[al][j][1] for j in ok]); k1 = np.array([res[al][j][2] for j in ok]); d = []
    for _ in range(B):
        idx = np.concatenate([gi[ug[i]] for i in rr.integers(0, len(ug), len(ug))]); d.append((k1[idx].sum() - b1[idx].sum()) / b1[idx].sum() - (k0[idx].sum() - b0[idx].sum()) / b0[idx].sum())
    return np.percentile(d, [2.5, 97.5]), (k1.sum() - b1.sum()) / b1.sum(), (k0.sum() - b0.sum()) / b0.sum(), int(sum(res[al][j][3] for j in ok)), int(sum(res[0.0][j][3] for j in ok)), b1.sum() / len(ok), b0.sum() / len(ok)
lines = [f"T105: sıralı 5'li, {len(ok)} havuz koşusu, b96 taban (α=0) vs değer-eğimli p'=p·(p/pm)^α"]
for al in (1.0, 2.0):
    ga, r1, r0, h1, h0, bb1, bb0 = boot(al)
    lines.append(f"{'BİRİNCİL' if al==1 else 'keşifsel'} α={al}: vuruş {h1} (taban {h0}) | ROI {r1:+.1%} (taban {r0:+.1%}) | fark GA95 [{ga[0]:+.1%},{ga[1]:+.1%}] | ort bedel {bb1:.0f} vs {bb0:.0f} TL")
    dv = [j for j in ok if res[al][j][4]]; 
    lines.append(f"     devirli {len(dv)}: vuruş {sum(res[al][j][3] for j in dv)} (taban {sum(res[0.0][j][3] for j in dv)})")
open("data/analiz/t105_sonuc.txt", "w").write("\n".join(lines)); print("\n".join(lines))
