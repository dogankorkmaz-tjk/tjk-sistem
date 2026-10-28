"""T35/T36 karşılaştırma: VAR (MJK/MJK2) − MJ. python3 data/analiz/k13_karsilastir.py"""
import pickle,numpy as np,random
random.seed(3)
def yukle(v,b): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}_{b}.pkl","rb"))
import sys
for v in sys.argv[1:]:
  for ad,b,son in [("A","2025-03","2026-03"),("B","2026-04","9999"),("C","2024-04","2024-12")]:
    try: X=yukle(v,b);Y=yukle("MJ",b)
    except Exception as e: print(v,ad,"yok");continue
    ays=[a for a in sorted(X) if a<=son and a in Y]
    a_=np.concatenate([X[a][0] for a in ays]);b_=np.concatenate([Y[a][0] for a in ays]);gun=np.array(sum([X[a][1] for a in ays],[]))
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};print(f"{v}−MJ [{ad} {ays[0]}..{ays[-1]}] {len(gun)} koşu")
    for j,n in enumerate(["kazanan","ikili","üçlü","ilk4","ilk5"]):
        dd=a_[:,j]-b_[:,j];bs=[dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(700)]
        print(f"   {n:8s} {dd.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
