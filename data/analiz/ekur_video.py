"""T51: ekür çift-içi bölüşüm: MJV − MJ. python3 data/analiz/ekur_video.py"""
import pickle,numpy as np,pandas as pd,random
random.seed(21)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl');E['tarih']=E.tarih.astype(str)
EK={(r.tarih,r.hipodrom,r.kosu,r.no):r.ekur for r in E.itertuples() if r.ekur>0}
def yukle(v,aylar):
    out={}
    for a in aylar:
        c=pickle.load(open(f"/tmp/claude-0/cache_{v}_{a}.pkl","rb"))
        for k,(key,nos) in enumerate(zip(c["keys"],c["nos"])): out[key]=(nos,c["S3"][k][:len(nos)])
    return out
def pairs(D,lm=False):
    rows=[]
    for key,(nos,S) in D.items():
        grp={}
        for i,n in enumerate(nos):
            e=EK.get((key[0],key[1],int(key[2]),n))
            if e: grp.setdefault(e,[]).append(i)
        for e,ix in grp.items():
            if len(ix)!=2: continue
            x,y=ix                                   # nos finiş sırasında: x<y => x önde
            rows.append((key[0],S[x]-S[y]))
    return rows
def kayip(rows): return np.array([np.log1p(np.exp(-d)) for _,d in rows])
def boot(d,gun):
    ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug}
    bs=[d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(1000)];return np.percentile(bs,[2.5,97.5])
for ad,aylar in [("H",["2025-12","2026-01","2026-02","2026-03"]),("B",["2026-04","2026-05","2026-06","2026-07","2026-08","2026-09","2026-10"])]:
    A=yukle("MJ",aylar);B=yukle("MJV",aylar);ks=sorted(set(A)&set(B))
    ra=pairs({k:A[k] for k in ks});rb=pairs({k:B[k] for k in ks})
    la=kayip(ra);lb=kayip(rb);gun=np.array([g for g,_ in ra])
    d=lb-la;lo,hi=boot(d,gun)
    print(f"[{ad}] ekür çifti {len(ra)}: MJ kayıp {la.mean():.4f}  MJV {lb.mean():.4f}  MJV−MJ {d.mean():+.4f} [{lo:+.4f},{hi:+.4f}]  (rastgele 0,6931)  isabet MJ {np.mean([x>0 for _,x in ra])*100:.1f}% MJV {np.mean([x>0 for _,x in rb])*100:.1f}%")
