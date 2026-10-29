"""T50: MJV2 − MJV ve MJV2 − MJ (piyasalı) ve piyasasız (N). python3 data/analiz/v2_karsilastir.py"""
import pickle,numpy as np,random
random.seed(9)
def yk(v,b): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}_{b}.pkl","rb"))
def kars(A,B,ad,bas,son,ab,bb):
    X=yk(A,ab);Y=yk(B,bb);ays=[a for a in sorted(X) if bas<=a<=son and a in Y]
    a_=np.concatenate([X[a][0] for a in ays]);b_=np.concatenate([Y[a][0] for a in ays]);gun=np.array(sum([X[a][1] for a in ays],[]))
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};print(f"{A}−{B} [{ad}] {len(gun)} koşu")
    for j,n in enumerate(["kazanan","ikili","üçlü","ilk4","ilk5"]):
        dd=a_[:,j]-b_[:,j];bs=[dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(500)]
        print(f"   {n:8s} {dd.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
for suf,ad_ in [("","piyasalı"),("N","piyasasız")]:
    print("==",ad_)
    for ad,ab,bas,son,tb in [("H","2025-12","2025-12","2026-03","2025-03"),("B","2026-04","2026-04","9999","2026-04")]:
        kars("MJV2"+suf,"MJV"+suf,ad,bas,son,ab,ab)
        kars("MJV2"+suf,"MJ"+suf if suf==""else "MJN",ad+" (vs taban)",bas,son,ab,tb)
