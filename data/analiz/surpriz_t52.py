"""T52: piyasasız model süpriz bayrağı. python3 data/analiz/surpriz_t52.py"""
import pickle,numpy as np,random
random.seed(52)
def sm(x):
    x=np.where(x>-1e8,x,-1e9);x=x-x.max();e=np.exp(x);return e/e.sum()
def yukle(v,aylar):
    o={}
    for a in aylar:
        c=pickle.load(open(f"/tmp/claude-0/cache_{v}_{a}.pkl","rb"))
        for k,key in enumerate(c["keys"]):
            n=len(c["nos"][k]); o[key]=(c["S3"][k][:n],c["gun"][k],c.get("L0",[None]*len(c["keys"]))[k])
    return o
def boot(v,gun,B=1000):
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};v=np.asarray(v)
    bs=[v[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(B)];return np.percentile(bs,[2.5,97.5])
PER={"H":["2025-12","2026-01","2026-02","2026-03"],"A":[f"2025-{m:02d}" for m in range(3,13)]+["2026-01","2026-02","2026-03"],"B":[f"2026-{m:02d}" for m in range(4,11)]}
for ad,aylar in PER.items():
    F=yukle("MJN",aylar)
    try: J=yukle("MJ",aylar)
    except FileNotFoundError: J=None
    ks=sorted(set(F)&set(J)) if J else sorted(F)
    for ad2,esik in (("PM0",1.5),)+((("ANA(kontrol)",1.5),) if J else ()):
        rows=[]
        for k in ks:
            sf,g,L0=F[k];n=len(sf);sj=J[k][0] if J else sf
            if L0 is None: continue
            pm=sm(L0[:n]);pf=sm(sf);pj=sm(sj)
            q=pf if ad2=="PM0" else pj
            for i in range(n):
                if q[i]/pm[i]>=esik and pm[i]<=0.10: rows.append((g,float(i==0),pm[i],pj[i],pf[i]))
        if not rows: print(ad,ad2,"bayrak yok");continue
        r=np.array([x[1:] for x in rows]);gun=np.array([x[0] for x in rows])
        exm=r[:,0]-r[:,1];exj=r[:,0]-r[:,2]
        a,b=boot(exm,gun);c,d=boot(exj,gun) if J else (0,0)
        print(f"[{ad}] {ad2}: bayraklı {len(rows)} at, kazanma {r[:,0].mean()*100:.2f}% | piyasa {r[:,1].mean()*100:.2f}% ana {r[:,2].mean()*100:.2f}% PM0 {r[:,3].mean()*100:.2f}% | ex_m {exm.mean()*100:+.2f}pp [{a*100:+.2f},{b*100:+.2f}]  ex_j {exj.mean()*100:+.2f}pp [{c*100:+.2f},{d*100:+.2f}]")
