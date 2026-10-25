"""T12: egzotik havuz fiyatlaması, sınıf-ROI. python3 -I egz_fiyat_t12.py"""
import glob,os,itertools,numpy as np,pandas as pd
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O['tarih']=O.tarih.astype(str)
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','ganyan','kosmadi','sira']) for f in glob.glob(R+'data/temiz/*.csv.gz')]);T['tarih']=T.tarih.astype(str)
T=T[(T.tarih>='2025-01-01')&(~T.kosmadi.fillna(False).astype(bool))&T.ganyan.notna()]
K=['tarih','hipodrom','kosu'];T['n']=T.groupby(K).no.transform('size');T=T[T.n>=5]
T['mr']=T.groupby(K).ganyan.rank(method='first').astype(int)       # 1=favori
rk={k:dict(zip(g.no,g.mr)) for k,g in T.groupby(K)};nn={k:g.n.iloc[0] for k,g in T.groupby(K)}
rng=np.random.default_rng(12)
def yukle(tur,adet):
    X=O[O.tur==tur].copy();c=X.groupby(K).seq.transform('max');X=X[(c==0)&(X.seq==0)]
    rows=[]
    for r in X.itertuples():
        k=(r.tarih,r.hipodrom,r.kosu)
        if k not in rk: continue
        try:no=[int(v) for v in str(r.kombo).split('/')]
        except: continue
        if len(no)!=adet or any(v not in rk[k] for v in no): continue
        rows.append((r.tarih,k,nn[k],tuple(rk[k][v] for v in no),float(r.tutar)))
    return rows
def sinif_roi(rows,adet,pred_fn,esle):
    """her koşu: sınıfa giren kombinasyon sayısı (pred_fn(n)) ; getiri: kazanan sınıftaysa ödeme"""
    d=[(t,esle(w),pay,pred_fn(n)) for t,k,n,w,pay in rows];return pd.DataFrame(d,columns=['t','hit','pay','cost'])
def boot(df,B=2000):
    s=df.assign(r=np.where(df.hit,df.pay,0.0)).groupby('t').agg(r=('r','sum'),c=('cost','sum'));o=[]
    for _ in range(B):
        x=s.iloc[rng.integers(0,len(s),len(s))];o.append(x.r.sum()/x.c.sum())
    return np.percentile(o,[2.5,97.5]),s.r.sum()/s.c.sum()
def fark(d1,d2,B=2000):
    a=d1.assign(r=np.where(d1.hit,d1.pay,0.0)).groupby('t').agg(r=('r','sum'),c=('cost','sum'));b=d2.assign(r=np.where(d2.hit,d2.pay,0.0)).groupby('t').agg(r=('r','sum'),c=('cost','sum'))
    j=a.join(b,lsuffix='1',rsuffix='2',how='inner');o=[]
    for _ in range(B):
        x=j.iloc[rng.integers(0,len(j),len(j))];o.append(x.r1.sum()/x.c1.sum()-x.r2.sum()/x.c2.sum())
    return np.percentile(o,[2.5,97.5]),j.r1.sum()/j.c1.sum()-j.r2.sum()/j.c2.sum(),len(j)
# --- sıralı ikili
SI=yukle('SIRALI İKİLİ',2);print('sıralı ikili koşu',len(SI),'| ödeme medyan',np.median([r[4] for r in SI]))
f1=sinif_roi(SI,2,lambda n:n-1,lambda w:w[0]==1);f2=sinif_roi(SI,2,lambda n:n-1,lambda w:w[1]==1)
for ad,d in (('fav 1. (fav,x)',f1),('fav 2. (x,fav)',f2)):
    ci,r=boot(d);print(f'  {ad:16s} ROI {r:.3f} [{ci[0]:.3f},{ci[1]:.3f}] isabet {d.hit.mean():.3f}')
ci,fr,n=fark(f2,f1);print(f'BİRİNCİL sıralı ikili: ROI(fav 2.) − ROI(fav 1.) = {fr:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}] n={n}')
# --- üçlü
UC=yukle('ÜÇLÜ BAHİS',3);print('üçlü koşu',len(UC))
c=lambda n:(n-1)*(n-2)
g1=sinif_roi(UC,3,c,lambda w:w[0]==1);g3=sinif_roi(UC,3,c,lambda w:w[2]==1);g2=sinif_roi(UC,3,c,lambda w:w[1]==1)
for ad,d in (('fav 1.',g1),('fav 2.',g2),('fav 3.',g3)):
    ci,r=boot(d);print(f'  {ad:16s} ROI {r:.3f} [{ci[0]:.3f},{ci[1]:.3f}] isabet {d.hit.mean():.3f}')
ci,fr,n=fark(g3,g1);print(f'BİRİNCİL üçlü: ROI(fav 3.) − ROI(fav 1.) = {fr:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}] n={n}')
# --- ikincil: sıralı ikili piyasa-sıra çiftleri
res=[]
for a,b in itertools.permutations(range(1,6),2):
    d=sinif_roi(SI,2,lambda n:1,lambda w:w==(a,b));ci,r=boot(d,800);res.append((a,b,d.hit.mean(),r,ci[0],ci[1]))
Q=pd.DataFrame(res,columns=['a','b','isabet','roi','lo','hi']);print('\nİKİNCİL sıralı ikili (a=1.,b=2. piyasa sırası) ROI:');print(Q.round(3).to_string(index=False))
