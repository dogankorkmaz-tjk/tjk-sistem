"""T49: piyasasız model. python3 data/analiz/nolp_karsilastir.py"""
import pickle,numpy as np,random
random.seed(5)
def yk(v,b): return pickle.load(open(f"/tmp/claude-0/v3_elo2{v}_{b}.pkl","rb"))
def rf(b): return pickle.load(open(f"/tmp/claude-0/v3_nolp_ref_{b}.pkl","rb"))
def boot(x,gi,ug,f=lambda v:v.mean()):
    return np.percentile([f(x[np.concatenate([gi[random.choice(ug)] for _ in ug])]) for _ in range(500)],[2.5,97.5])
for ad,b,bas,son in [("A","2025-03","2025-03","2026-03"),("B","2026-04","2026-04","9999")]:
    X=yk("MJN",b);R=rf(b);ays=[a for a in sorted(X) if bas<=a<=son]
    p=np.concatenate([X[a][0] for a in ays]);m=np.concatenate([R[a][0] for a in ays]);u=np.concatenate([R[a][1] for a in ays]);gun=np.array(sum([X[a][1] for a in ays],[]))
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};print(f"PM0 [{ad} {ays[0]}..{ays[-1]}] {len(gun)} koşu  (nats/koşu; kayıp, küçük=iyi)")
    for j,n in enumerate(["kazanan","ikili","üçlü","ilk4","ilk5"]):
        g_u=u[:,j]-p[:,j];g_m=m[:,j]-p[:,j];den=(u[:,j]-m[:,j]).mean()
        lo,hi=boot(g_u,gi,ug)
        print(f"   {n:8s} kayıp PM0 {p[:,j].mean():.4f} piyasa {m[:,j].mean():.4f} eşit {u[:,j].mean():.4f} | eşit−PM0 {g_u.mean():+.4f} [{lo:+.4f},{hi:+.4f}] piyasa−PM0 {g_m.mean():+.4f} Ρ={g_u.mean()/den:.2f}")
print("PMV−PM0:")
for ad,b,bas,son in [("H","2025-12","2025-12","2026-03"),("B","2026-04","2026-04","9999")]:
    X=yk("MJVN",b);Y=yk("MJN","2025-03" if b=="2025-12" else "2026-04");ays=[a for a in sorted(X) if bas<=a<=son and a in Y]
    a_=np.concatenate([X[a][0] for a in ays]);b_=np.concatenate([Y[a][0] for a in ays]);gun=np.array(sum([X[a][1] for a in ays],[]))
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};print(f" [{ad} {ays[0]}..{ays[-1]}] {len(gun)} koşu")
    for j,n in enumerate(["kazanan","ikili","üçlü","ilk4","ilk5"]):
        dd=a_[:,j]-b_[:,j];lo,hi=boot(dd,gi,ug);print(f"   {n:8s} {dd.mean():+.4f} [{lo:+.4f},{hi:+.4f}]")
