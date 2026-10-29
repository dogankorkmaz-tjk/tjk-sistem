"""T41: MJV − MJ. Dönemler: B 2026-04.. ve H 2025-12..2026-03 (yarı-dönem). python3 data/analiz/v_karsilastir.py"""
import pickle,numpy as np,random
random.seed(3)
def yukle(v,b): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}_{b}.pkl","rb"))
for ad,b,bas,son in [("H","2025-12","2025-12","2026-03"),("B","2026-04","2026-04","9999")]:
    X=yukle("MJV",b);Y=yukle("MJ","2026-04" if b=="2026-04" else "2025-03")
    ays=[a for a in sorted(X) if bas<=a<=son and a in Y]
    a_=np.concatenate([X[a][0] for a in ays]);b_=np.concatenate([Y[a][0] for a in ays]);gun=np.array(sum([X[a][1] for a in ays],[]))
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};print(f"MJV−MJ [{ad} {ays[0]}..{ays[-1]}] {len(gun)} koşu")
    for j,n in enumerate(["kazanan","ikili","üçlü","ilk4","ilk5"]):
        dd=a_[:,j]-b_[:,j];bs=[dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(700)]
        print(f"   {n:8s} {dd.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
