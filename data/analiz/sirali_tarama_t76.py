"""T76: 2.–5. sıra ölçütüyle özellik taraması. python3 data/analiz/sirali_tarama_t76.py"""
import pickle,os,numpy as np,random,sys
random.seed(76)
def yukle(v,b): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}_{b}.pkl","rb"))
VARS=['MJH','MJC','MJK','MJK2','MJB','MJB2','MJM','MJV','MJV2','MJG','MJW']
for v in VARS:
  out=[]
  for ad,b,son in [("A","2025-03","2026-03"),("B","2026-04","9999"),("C","2024-04","2024-12")]:
    try: X=yukle(v,b);Y=yukle("MJ",b)
    except Exception: out.append(f"{ad}: yok");continue
    ays=[a for a in sorted(X) if a<=son and a in Y]
    if not ays: out.append(f"{ad}: yok");continue
    a_=np.concatenate([X[a][0] for a in ays]);b_=np.concatenate([Y[a][0] for a in ays]);gun=np.array(sum([X[a][1] for a in ays],[]))
    if len(a_)!=len(b_): out.append(f"{ad}: boyut uyumsuz");continue
    dd=(a_[:,4]-a_[:,0])-(b_[:,4]-b_[:,0]);ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug}
    bs=[dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(700)]
    out.append(f"{ad} n={len(gun)} 2-5: {dd.mean():+.4f} [{np.percentile(bs,0.25):+.4f},{np.percentile(bs,99.75):+.4f}]")
  print(v,'|',' | '.join(out))
