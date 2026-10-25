"""T13: havuz-ima edilen 2. sıra / ilk-2 bilgisi. python3 -I egz_havuz_t13.py <oos_p.pkl>"""
import sys,glob,json,os,numpy as np,pandas as pd,unicodedata
from scipy.optimize import minimize
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str);P=P.dropna(subset=['sira','p_Jason','p_piyasa']);P=P[(P.p_Jason>0)&(P.p_piyasa>0)]
H={}
for f in sorted(glob.glob(R+'data/muh_gecmis/*.json')):
    g=os.path.basename(f)[:-5];o=json.load(open(f))
    for key,e in o.items():
        hip,kn=key.rsplit('-',1);H[(g,asc(hip),int(kn))]=e
print('havuz verili koşu',len(H),'| gün',len({k[0] for k in H}))
races=[];drop=0
for (t,h,k),g in P.groupby(['tarih','hipodrom','kosu']):
    e=H.get((t,asc(h),int(k)))
    if not e or 'si' not in e or 'ik' not in e: continue
    g=g.sort_values('sira')
    if len(g)<6 or g.sira.iloc[:6].nunique()<6 or g.sira.iloc[0]!=1: continue
    no=[int(x) for x in g.no];idx={n:i for i,n in enumerate(no)};n=len(no)
    s2=np.zeros(n);sq=np.zeros(n);ok=True
    try:
        for a,b,G in e['si']:
            q=1/float(G);s2[idx[int(b)]]+=q
        for a,b,G in e['ik']:
            q=1/float(G);sq[idx[int(a)]]+=q;sq[idx[int(b)]]+=q
    except Exception: drop+=1;continue
    if s2.sum()<=0 or sq.sum()<=0: drop+=1;continue
    f2=np.log((s2+1e-3*s2.mean())/ (s2+1e-3*s2.mean()).sum());fq=np.log((sq+1e-3*sq.mean())/(sq+1e-3*sq.mean()).sum())
    lj=np.log(g.p_Jason/g.p_Jason.sum()).values;lm=np.log(g.p_piyasa/g.p_piyasa.sum()).values
    races.append((t,np.vstack([lj,lm,f2,fq])))
print('kullanılan koşu',len(races),'atılan',drop)
races.sort(key=lambda r:r[0]);days=sorted({r[0] for r in races});cut=days[int(len(days)*0.6)];fi=[r for r in races if r[0]<cut];te=[r for r in races if r[0]>=cut];print('fit',len(fi),'test',len(te),'kesim',cut)
def pack(R_):
    N=max(r[1].shape[1] for r in R_);nf=R_[0][1].shape[0];X=np.zeros((len(R_),N,nf));M=np.zeros((len(R_),N),bool)
    for i,r in enumerate(R_):n=r[1].shape[1];X[i,:n]=r[1].T;M[i,:n]=True
    return X,M
def nll_grad(th,X,M):
    R_,N,nf=X.shape;tot=np.zeros((R_,5));gr=np.zeros_like(th);pos=np.arange(N)[None,:]
    for s in range(5):
        S=X@th[s];alive=(pos>=s)&M;Sm=np.where(alive,S,-1e30);mx=Sm.max(1,keepdims=True);E=np.where(alive,np.exp(Sm-mx),0);Z=E.sum(1,keepdims=True)
        tot[:,s]=-(S[:,s]-(mx[:,0]+np.log(Z[:,0])));pr=E/Z;gr[s]=(pr[:,:,None]*X).sum((0,1))-X[:,s,:].sum(0)
    return tot,gr
def fit(X,M,nf,lam=1.0):
    v0=np.zeros((5,nf));v0[:,0]=1.0
    f=lambda v:(lambda t,g:(t.sum()+0.5*lam*np.sum((v-v0.ravel())**2),g.ravel()+lam*(v-v0.ravel())))(*nll_grad(v.reshape(5,nf),X,M))
    return minimize(f,v0.ravel(),jac=True,method='L-BFGS-B').x.reshape(5,nf)
Xf,Mf=pack(fi);Xt,Mt=pack(te);g=np.array([r[0] for r in te]);rng=np.random.default_rng(13)
def ci(x):
    s=pd.DataFrame({'g':g,'x':x}).groupby('g').x.agg(['sum','size']);o=[]
    for _ in range(3000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
thB=fit(Xf[:,:,:2],Mf,2);nb=nll_grad(thB,Xt[:,:,:2],Mt)[0]
for ad,cols in (('+ 2. sıra marjinali (s2)',[0,1,2]),('+ ilk-2 küme marjinali (sq)',[0,1,3]),('+ ikisi',[0,1,2,3])):
    th=fit(Xf[:,:,cols],Mf,len(cols));nn=nll_grad(th,Xt[:,:,cols],Mt)[0];d2=nb[:,1]-nn[:,1];d25=(nb-nn)[:,1:].sum(1);a=ci(d2);b=ci(d25)
    print(f'{ad:30s} 2. sıra kazanç {d2.mean():+.4f} [{a[0]:+.4f},{a[1]:+.4f}] | 2.–5. toplam {d25.mean():+.4f} [{b[0]:+.4f},{b[1]:+.4f}]')
    if len(cols)==4:print(np.round(th,3))
