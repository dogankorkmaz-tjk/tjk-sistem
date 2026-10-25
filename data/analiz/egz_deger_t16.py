"""T8: Jason ekstra özellikleri sıraya özel (ön-kayıt: hipotez_defteri.md 25 Ekim 2026 02:45). python3 -I ilk5_jason_ek.py <oos_p.pkl> <ek3.pkl>"""
import sys,glob,os,numpy as np,pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str)
P=P.dropna(subset=['sira','p_Jason','p_piyasa']);P=P[(P.p_Jason>0)&(P.p_piyasa>0)]
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','at','jokey','apranti','kilo']) for f in glob.glob(R+'data/temiz/*.csv.gz')]);T['tarih']=T.tarih.astype(str)
P=P.merge(T.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left')
# dinlenme
H=T[['at','tarih']].drop_duplicates().sort_values(['at','tarih']);H['onc']=H.groupby('at').tarih.shift()
H['gun']=(pd.to_datetime(H.tarih)-pd.to_datetime(H.onc)).dt.days;P=P.merge(H[['at','tarih','gun']],on=['at','tarih'],how='left')
P['ilk']=P.gun.isna().astype(float);P['lrest']=np.log1p(P.gun.clip(7,150).fillna(30))
P['idm']=0.0;P['p400']=np.nan
E=pd.read_pickle(sys.argv[2]).drop_duplicates(['tarih','hipodrom','kosu','no'])
P=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left')
muE={c:[float(P[c].mean()),float(P[c].std())] for c in ['f_dp150_m','f_jgen100','f_fig3']}
for c in ['f_dp150_m','f_jgen100','f_fig3']:P[c]=((P[c]-P[c].mean())/P[c].std()).fillna(0.0)
hips=[]
def build(P_,cols):
    R_=[]
    for (t,h,k),g in P_.groupby(['tarih','hipodrom','kosu']):
        g=g.sort_values('sira')
        if len(g)<6 or g.sira.iloc[:6].nunique()<6 or g.sira.iloc[0]!=1: continue
        lj=np.log(g.p_Jason/g.p_Jason.sum()).values;lm=np.log(g.p_piyasa/g.p_piyasa.sum()).values;n=len(g)
        F={'lj':lj,'lm':lm,'n':lj*(n-10)/3.0,'rest':g.lrest.values,'ilk':g.ilk.values,'idm':g.idm.values}
        p4=g.p400.values.astype(float);F['p4']=np.where(np.isnan(p4),0.0,-(p4-np.nanmean(p4)) if np.isfinite(np.nanmean(p4)) else 0.0)
        F['p4n']=np.isnan(p4).astype(float);F['e1']=g.f_dp150_m.values;F['e2']=g.f_jgen100.values;F['e3']=g.f_fig3.values
        for hh in hips:F['h_'+hh]=lm*(g.hipodrom.values==hh)
        R_.append((t,h,np.vstack([F[c] for c in cols]),g))
    return R_
def pack(R_):
    N=max(r[2].shape[1] for r in R_);nf=R_[0][2].shape[0];X=np.zeros((len(R_),N,nf));M=np.zeros((len(R_),N),bool)
    for i,r in enumerate(R_):n=r[2].shape[1];X[i,:n]=r[2].T;M[i,:n]=True
    return X,M
def nll_grad(th,X,M):   # th (5,nf); sıra s: kalan = konum>=s
    R_,N,nf=X.shape;tot=np.zeros((R_,5));gr=np.zeros_like(th);pos=np.arange(N)[None,:]
    for s in range(5):
        S=X@th[s];alive=(pos>=s)&M;Sm=np.where(alive,S,-1e30);mx=Sm.max(1,keepdims=True);E=np.where(alive,np.exp(Sm-mx),0);Z=E.sum(1,keepdims=True)
        tot[:,s]=-(S[:,s]-(mx[:,0]+np.log(Z[:,0])));pr=E/Z
        gr[s]=(pr[:,:,None]*X).sum((0,1))-X[:,s,:].sum(0)
    return tot,gr
def fit(X,M,nf,lam=1.0,base_idx=(0,1)):
    v0=np.zeros((5,nf));v0[:,0]=1.0
    f=lambda v:(lambda t,g:(t.sum()+0.5*lam*np.sum((v-v0.ravel())**2),g.ravel()+lam*(v-v0.ravel())))(*nll_grad(v.reshape(5,nf),X,M))
    return minimize(f,v0.ravel(),jac=True,method='L-BFGS-B').x.reshape(5,nf)
rng=np.random.default_rng(21)
def ci(x,g):
    s=pd.DataFrame({'g':g,'x':x}).groupby('g').x.agg(['sum','size']);o=[]
    for _ in range(3000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
def teste(ad,cols_extra,P_,etiket):
    cols=['lj','lm']+cols_extra;R_=build(P_,cols);R_.sort(key=lambda r:r[0]);days=sorted({r[0] for r in R_});cut=days[int(len(days)*0.6)]
    fi=[r for r in R_ if r[0]<cut];te=[r for r in R_ if r[0]>=cut];Xf,Mf=pack(fi);Xt,Mt=pack(te)
    thB=fit(Xf[:,:,:2],Mf,2);thN=fit(Xf,Mf,len(cols))
    nb=nll_grad(thB,Xt[:,:,:2],Mt)[0][:,1:].sum(1);nn=nll_grad(thN,Xt,Mt)[0][:,1:].sum(1);d=nb-nn;g=np.array([r[0] for r in te]);lo,hi=ci(d,g)
    print(f'{etiket:34s} koşu fit {len(fi)} test {len(te)} | ek kazanç {d.mean():+.4f} [{lo:+.4f},{hi:+.4f}]')
    return thN,te,Xt,Mt



import json as _j, unicodedata
asc2=lambda x:unicodedata.normalize('NFKD',str(x).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
H={}
for f in sorted(glob.glob(R+'data/muh_gecmis/*.json')):
    gg=os.path.basename(f)[:-5];o=_j.load(open(f))
    for key,e in o.items():
        hip,kn=key.rsplit('-',1);H[(gg,asc2(hip),int(kn))]=e
cols=['lj','lm','rest','ilk','e1','e2','e3'];R_=build(P,cols);R_.sort(key=lambda r:r[0]);days=sorted({r[0] for r in R_});cut=days[int(len(days)*0.6)]
fi=[r for r in R_ if r[0]<cut];Xf,Mf=pack(fi);thD=fit(Xf,Mf,len(cols))
def fitm(X,M,lam=1.0):
    v0=np.ones((5,1));f=lambda v:(lambda t,g:(t.sum()+0.5*lam*np.sum((v-v0.ravel())**2),g.ravel()+lam*(v-v0.ravel())))(*nll_grad(v.reshape(5,1),X,M))
    return minimize(f,v0.ravel(),jac=True,method='L-BFGS-B').x.reshape(5,1)
thM=fitm(Xf[:,:,[1]],Mf)
def sm(sc):
    sc=sc-sc.max();e=np.exp(sc);return e/e.sum()
rows=[]
for t,h,X,g in R_:
    if t<cut:continue
    e=H.get((t,asc2(h),int(g.kosu.iloc[0])))
    if not e or 'si' not in e or 'ik' not in e:continue
    no=[int(v) for v in g.no];ix={n:i for i,n in enumerate(no)};n=len(no)
    def qs(th,Xs):
        p1=sm(Xs.T@th[0]);Q=np.zeros((n,n))
        for a in range(n):
            rest_=[j for j in range(n) if j!=a];p2=sm((Xs.T@th[1])[rest_])
            for k,b in enumerate(rest_):Q[a,b]=p1[a]*p2[k]
        return Q
    QD=qs(thD,X);QM=qs(thM,X[[1]]) if False else None
    # piyasa-tek-başına: sadece lm
    QM=qs(thM,X[[1],:])
    try:
        for tur,key in (('si','si'),('ik','ik')):
            lst=[(ix[int(a)],ix[int(b)],float(G)) for a,b,G in e[key]]
            for a,b,G in lst:
                if tur=='si':hit=(a==0 and b==1);qd=QD[a,b];qm=QM[a,b]
                else:hit=({a,b}=={0,1});qd=QD[a,b]+QD[b,a];qm=QM[a,b]+QM[b,a]
                rows.append((t,tur,n,qd*G,qm*G,float(hit)*G,float(hit)))
    except Exception:continue
Z=pd.DataFrame(rows,columns=['t','tur','n','evD','evM','ret','hit']);print('satır',len(Z),'koşu-gün',Z.t.nunique())
rng3=np.random.default_rng(31)
def roi_ci(sel,B=1500):
    s=Z[sel].groupby('t').agg(r=('ret','sum'),c=('ret','size'));o=[]
    for _ in range(B):
        x=s.iloc[rng3.integers(0,len(s),len(s))];o.append(x.r.sum()/x.c.sum())
    return s.r.sum()/s.c.sum(),np.percentile(o,[2.5,97.5]),int(s.c.sum())
def fark_ci(sel,tabansel,B=1500):
    a=Z[sel].groupby('t').agg(r=('ret','sum'),c=('ret','size'));b=Z[tabansel].groupby('t').agg(r=('ret','sum'),c=('ret','size'));j=a.join(b,lsuffix='1',rsuffix='2',how='inner');o=[]
    for _ in range(B):
        x=j.iloc[rng3.integers(0,len(j),len(j))];o.append(x.r1.sum()/x.c1.sum()-x.r2.sum()/x.c2.sum())
    return j.r1.sum()/j.c1.sum()-j.r2.sum()/j.c2.sum(),np.percentile(o,[2.5,97.5])
for tur in ('si','ik'):
    T_=Z.tur==tur;rb,cb,nb=roi_ci(T_);print(f'\n[{tur}] TABAN (22 liste, hepsi): ROI {rb:.3f} [{cb[0]:.3f},{cb[1]:.3f}] bahis {nb}')
    for ev,ad in (('evD','D+'),('evM','M kontrol')):
        for th in (1.0,1.15,1.3,1.5):
            sel=T_&(Z[ev]>=th)
            if sel.sum()<50:print(f'  {ad:10s} θ={th}: bahis {int(sel.sum())} (az)');continue
            r,c,nbet=roi_ci(sel);d,dc=fark_ci(sel,T_);print(f'  {ad:10s} θ={th}: bahis {nbet:6d} isabet {Z[sel].hit.mean():.3f} ROI {r:.3f} [{c[0]:.3f},{c[1]:.3f}] | fark(taban) {d:+.3f} [{dc[0]:+.3f},{dc[1]:+.3f}]')
    for ad,m in (('alan≤8',Z.n<=8),('alan 9–11',(Z.n>=9)&(Z.n<=11)),('alan≥12',Z.n>=12)):
        sel=T_&m&(Z.evD>=1.15)
        if sel.sum()>=50:r,c,nbet=roi_ci(sel);print(f'  D+ θ=1.15 {ad:10s}: bahis {nbet:6d} ROI {r:.3f} [{c[0]:.3f},{c[1]:.3f}]')
