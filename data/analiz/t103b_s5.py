"""T103b: sıralı 5'li alan büyüklüğü/devir/filtre (ön kayıt hipotez_defteri T103b). python3 data/analiz/t103b_s5.py"""
"""v3 doğrulama: aylık işaret tutarlılığı + egzotik ROI (v2 vs v3). Ön kayıt: hipotez_defteri 2026-10-24 12:45 (sızıntı denetimi/tutarlılık/ROI maddeleri)."""
import os, sys, glob, itertools, random
from multiprocessing import Pool
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_v3.py")).read(), "entegre_v3", "exec"))
from tjk import besli, tabela, egzotik as E
def smx(s): e = np.exp(s - s.max()); return e / e.sum()
print("\n== AYLIK TUTARLILIK (v3 − v2, ortalama nats/koşu) ==")
for a in test:
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
with Pool(2) as pool: out = pool.map(kup5, [(smx(x[3]), smx(x[1]["lm"]), x[4]) for x in POOL], chunksize=8)
rows = []
for x, o in zip(POOL, out):
    if o is None: continue
    sets, pm_, pq = o; pr = x[2]; hit = all(i in sets[i] for i in range(5)); n = len(x[1]["lm"]); key = x[1]["key"]
    pay = max([t for _, t in pr.get("SIRALI 5 Lİ BAHİS", [(0, 0.0)])]); v = besli.gecerli_say(sets)
    rows.append((x[1]["gun"], x[0], key[1], int(key[2]), n, v * 1.25, pay if hit else 0.0, int(hit), pm_ / max(pq, 1e-9), pm_, pq, "DEVİR" in " ".join(pr)))
import pandas as pd
D = pd.DataFrame(rows, columns=["gun", "ay", "hip", "kosu", "n", "bedel", "kz", "tuttu", "oran", "pm", "pq", "kendi_devir"])
D = D.sort_values(["hip", "gun", "kosu"]).reset_index(drop=True)
dv = []
for h, g in D.groupby("hip", sort=False):
    last = None; lastd = None
    for r in g.itertuples():
        d = (last is not None and last[1] and (pd.Timestamp(r.gun) - pd.Timestamp(last[0])).days <= 3); dv.append((r.Index, bool(d))); last = (r.gun, r.kendi_devir)
D["devirli"] = pd.Series(dict(dv))
D.to_pickle("/tmp/claude-0/t103b.pkl")
D["sinif"] = pd.cut(D.n, [0, 12, 15, 99], labels=["<=12", "13-15", ">=16"]); D["filt"] = np.where(D.oran >= 1.15, "oran>=1.15", "oran<1.15"); D["yari"] = np.where(D.ay <= "2026-07", "Nis-Tem", "Agu-Eki")
rr = np.random.default_rng(31)
def roi_ga(df, B=3000):
    ix = df.groupby("gun").indices; ds = list(ix); b = df.bedel.values; k = df.kz.values; v = []
    for _ in range(B):
        s = rr.choice(len(ds), len(ds)); idx = np.concatenate([ix[ds[j]] for j in s]); v.append((k[idx].sum() - b[idx].sum()) / b[idx].sum())
    return (k.sum() - b.sum()) / b.sum(), np.percentile(v, [2.5, 97.5])
def satir(ad, Y):
    if len(Y) == 0: return f"   {ad}: n=0"
    r = roi_ga(Y); return f"   {ad:22s} n={len(Y):4d} vuruş {int(Y.tuttu.sum()):2d} (model {Y.pm.sum():.1f}, piyasa {Y.pq.sum():.1f}) ROI {r[0]:+.1%} [{r[1][0]:+.1%},{r[1][1]:+.1%}]"
out = [f"T103b: sıralı 5'li havuz koşusu {len(D)}, devirli {int(D.devirli.sum())}; kupon b96 (v3), bilet 1,25 TL"]
out.append(satir("HEPSİ", D))
for dvl, ad in ((False, "devirsiz"), (True, "devirli")): out.append(satir(ad, D[D.devirli == dvl]))
for s_ in ("<=12", "13-15", ">=16"):
    Y = D[D.sinif == s_]; out.append(satir(f"alan {s_}", Y))
    for yr in ("Nis-Tem", "Agu-Eki"): out.append(f"        {yr}: n={len(Y[Y.yari==yr])} vuruş {int(Y[Y.yari==yr].tuttu.sum())} ROI {((Y[Y.yari==yr].kz.sum()-Y[Y.yari==yr].bedel.sum())/max(Y[Y.yari==yr].bedel.sum(),1e-9)):+.1%}")
for f_ in ("oran>=1.15", "oran<1.15"):
    Y = D[D.filt == f_]; out.append(satir(f_, Y)); out.append(f"      KALİBRASYON gerçek {Y.tuttu.mean():.2%} | model {Y.pm.mean():.2%} | piyasa {Y.pq.mean():.2%}")
open("data/analiz/t103b_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
