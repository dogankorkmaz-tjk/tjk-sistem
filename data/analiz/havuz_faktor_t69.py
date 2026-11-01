"""T69: havuz faktörü katsayıları (G sabit). python3 data/analiz/havuz_faktor_t69.py"""
import glob,json,os,unicodedata,numpy as np,pandas as pd
from scipy.optimize import minimize
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
G=np.array([1,0.80,0.69,0.69,0.69])
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P=P.dropna(subset=['sira','p_Jason']);P=P[P.p_Jason>0]
H={}
for f in sorted(glob.glob(R+'data/muh_gecmis/*.json')):
    g=os.path.basename(f)[:-5];o=json.load(open(f))
    for key,e in o.items():
        hip,kn=key.rsplit('-',1);H[(g,asc(hip),int(kn))]=e
races=[]
for (t,h,k),g in P.groupby(['tarih','hipodrom','kosu']):
    e=H.get((t,asc(h),int(k)))
    if not e or 'si' not in e or 'ik' not in e: continue
    g=g.sort_values('sira')
    if len(g)<6 or g.sira.iloc[:6].nunique()<6 or g.sira.iloc[0]!=1: continue
    no=[int(x) for x in g.no];idx={n:i for i,n in enumerate(no)};n=len(no);s2=np.zeros(n);sq=np.zeros(n)
    try:
        for a,b,Gv in e['si']: s2[idx[int(b)]]+=1/float(Gv)
        for a,b,Gv in e['ik']: sq[idx[int(a)]]+=1/float(Gv);sq[idx[int(b)]]+=1/float(Gv)
    except Exception: continue
    if s2.sum()<=0 or sq.sum()<=0: continue
    f2=np.log((s2+1e-3*s2.mean())/(s2+1e-3*s2.mean()).sum());fq=np.log((sq+1e-3*sq.mean())/(sq+1e-3*sq.mean()).sum())
    lj=np.log(g.p_Jason/g.p_Jason.sum()).values
    races.append((t,np.vstack([lj,f2,fq])))
races.sort(key=lambda r:r[0]);days=sorted({r[0] for r in races});cut=days[int(len(days)*0.6)]
fi=[r for r in races if r[0]<cut];te=[r for r in races if r[0]>=cut];print('koşu',len(races),'fit',len(fi),'test',len(te),'kesim',cut)
def pack(R_):
    N=max(r[1].shape[1] for r in R_);X=np.zeros((len(R_),N,3));M=np.zeros((len(R_),N),bool)
    for i,r in enumerate(R_):n=r[1].shape[1];X[i,:n]=r[1].T;M[i,:n]=True
    return X,M
def nll(b,X,M,use=True):   # b (5,2): sıra başına (β2,βq); sıra 0 için 0
    R_,N,_=X.shape;tot=np.zeros((R_,5));gr=np.zeros((5,2));pos=np.arange(N)[None,:]
    for s in range(5):
        S=G[s]*X[:,:,0]+(X[:,:,1]*b[s,0]+X[:,:,2]*b[s,1] if use else 0)
        alive=(pos>=s)&M;Sm=np.where(alive,S,-1e30);mx=Sm.max(1,keepdims=True);E=np.where(alive,np.exp(Sm-mx),0);Z=E.sum(1,keepdims=True)
        tot[:,s]=-(S[:,s]-(mx[:,0]+np.log(Z[:,0])))
        if use:
            pr=E/Z;gr[s,0]=(pr*X[:,:,1]).sum()-X[:,s,1].sum();gr[s,1]=(pr*X[:,:,2]).sum()-X[:,s,2].sum()
    return tot,gr
Xf,Mf=pack(fi);Xt,Mt=pack(te)
lam=1.0
def obj(v):
    b=v.reshape(5,2).copy();b[0]=0;t,g=nll(b,Xf,Mf);g[0]=0;return t.sum()+0.5*lam*np.sum(b**2),(g+lam*b).ravel()
v=minimize(obj,np.zeros(10),jac=True,method='L-BFGS-B').x.reshape(5,2);v[0]=0
nb=nll(np.zeros((5,2)),Xt,Mt,False)[0];nn=nll(v,Xt,Mt)[0];gday=np.array([r[0] for r in te]);rng=np.random.default_rng(69)
def ci(x):
    s=pd.DataFrame({'g':gday,'x':x}).groupby('g').x.agg(['sum','size']);o=[]
    for _ in range(3000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
print('katsayılar (sıra: β2,βq):',np.round(v,3).tolist())
d=(nb-nn)[:,1:].sum(1);lo,hi=ci(d);print('2.–5. toplam kazanç %+.4f [%+.4f,%+.4f]'%(d.mean(),lo,hi))
for s in range(1,5):
    d=(nb-nn)[:,s];lo,hi=ci(d);print('sıra',s+1,'%+.4f [%+.4f,%+.4f]'%(d.mean(),lo,hi))
json.dump({'G':G.tolist(),'beta':v.tolist(),'kesim':cut,'n_fit':len(fi)},open(R+'data/analiz/havuz_faktor_t69.json','w'))
