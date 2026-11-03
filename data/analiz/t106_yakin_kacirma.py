"""T106: sıralı 5'li yakın kaçırma/sürpriz at kayıp analizi (ön kayıt hipotez_defteri T106)"""
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


ARGS = [(smx(x[3]), smx(x[1]["lm"]), x[4]) for x in POOL]
with Pool(2) as pool: out = pool.map(kup5, ARGS, chunksize=8)
rng = np.random.default_rng(11); NS = 300
obs_k = np.zeros(6); exp_k = np.zeros(6); obs = dict(n=0, kayip=0, outs=0, swap=0, other=0); exs = dict(outs=0.0, swap=0.0, other=0.0, kayip=0.0)
def tipler(perm, sets, rank):
    # perm[j] = j. sıradaki at; kaçan ayaklar için tip
    t = dict(outs=0, swap=0, other=0)
    for j in range(5):
        h = perm[j]
        if h in sets[j]: continue
        if rank[h] >= 6: t["outs"] += 1                      # modelin ilk 6'sı dışındaki at kazandı/girdi
        elif (j > 0 and h in sets[j - 1]) or (j < 4 and h in sets[j + 1]): t["swap"] += 1   # komşu ayağa yazılmış at yer değiştirdi
        else: t["other"] += 1
    return t
for x, o in zip(POOL, out):
    if o is None: continue
    sets, pm_, pq = o; p = smx(x[3]); gam = x[4]; n = len(p); rank = np.empty(n, int); rank[np.argsort(-p)] = np.arange(n)
    ident = list(range(n)); hits = sum(1 for j in range(5) if j in sets[j]); obs_k[hits] += 1; obs["n"] += 1; obs["kayip"] += int(hits < 5)
    t = tipler(ident, sets, rank); obs["outs"] += t["outs"]; obs["swap"] += t["swap"]; obs["other"] += t["other"]
    for _ in range(NS):
        w = np.log(np.clip(p, 1e-12, 1)); avail = list(range(n)); perm = []
        for j in range(5):
            z = np.array([gam[j] * w[i] for i in avail]); z -= z.max(); q = np.exp(z); q /= q.sum(); c = int(rng.choice(len(avail), p=q)); perm.append(avail.pop(c))
        h5 = sum(1 for j in range(5) if perm[j] in sets[j]); exp_k[h5] += 1.0 / NS; exs["kayip"] += float(h5 < 5) / NS
        tt = tipler(perm, sets, rank); exs["outs"] += tt["outs"] / NS; exs["swap"] += tt["swap"] / NS; exs["other"] += tt["other"] / NS
L = [f"T106: {obs['n']} sıralı 5'li havuz koşusu, b96 (v3); beklenen = modelin kendi olasılığından {NS} simülasyon/koşu"]
L.append("tutan ayak sayısı (0..5): gözlenen " + " ".join(f"{int(v)}" for v in obs_k) + " | beklenen " + " ".join(f"{v:.0f}" for v in exp_k))
L.append(f"kaçan ayaklar (toplam): gözlenen sürpriz-dışarıdan(model ilk6 dışı) {obs['outs']} | komşu-ayağa-yazılmış-yer-değişimi {obs['swap']} | diğer {obs['other']}")
L.append(f"                        beklenen   sürpriz-dışarıdan {exs['outs']:.0f} | yer-değişimi {exs['swap']:.0f} | diğer {exs['other']:.0f}")
L.append(f"4/5 tutan (yakın kaçırma) gözlenen {int(obs_k[4])} beklenen {exp_k[4]:.0f}; tam tutan gözlenen {int(obs_k[5])} beklenen {exp_k[5]:.1f}")
open("data/analiz/t106_sonuc.txt", "w").write("\n".join(L)); print("\n".join(L))
