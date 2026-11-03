"""T107: genişletilmiş pencerede Benter v3 ileri-yürüyüş puanlarını üretir ve /tmp/claude-0/pool_v3b.pkl'e yazar. python3 data/analiz/t107_havuz_uret.py"""
import os, sys, glob, pickle
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_v3.py")).read().split("\naylar = sorted")[0]
exec(compile(src, "entegre_v3", "exec"))
from tjk import egzotik as E
O = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/20*.csv.gz"))]); PAY = {}
for q in O.itertuples():
    if str(q.tur).startswith("SIRALI 5"): PAY.setdefault((q.tarih, q.hipodrom, int(q.kosu)), []).append((str(q.tur), str(q.kombo), float(q.tutar)))
ODM = sorted({f[-14:-7] for f in glob.glob("data/odeme/20*.csv.gz")})
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a in ODM and a >= "2024-01"]
print("test ayları", test, flush=True); POOLS = []
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    if not te or len(tr) < 1500: continue
    tm = fitJ(tr); S3, g3, FF3 = scoreJ(te, tm); trg = [r for r in tr if r["F"] is not None]; galop = len(trg) >= 800
    if galop: S3tr, _, FF3tr = scoreJ(trg, tm); bg3 = fit2S(S3tr, FF3tr); S = S3 + ((FF3 - bg3[1]) / bg3[2]) @ bg3[0]
    else: S = S3
    for k, r in enumerate(te):
        pr = PAY.get(r["key"])
        if not pr: continue
        n = len(r["lm"])
        if n < 5: continue
        POOLS.append(dict(key=r["key"], gun=r["gun"], ay=a, lm=r["lm"], S=S[k, :n].copy(), gam=g3, galop=galop, pay=pr))
    print(a, len(te), "koşu;", len([p for p in POOLS if p["ay"] == a]), "havuz; galop", galop, flush=True)
pickle.dump(POOLS, open("/tmp/claude-0/pool_v3b.pkl", "wb")); print("toplam havuz", len(POOLS))
