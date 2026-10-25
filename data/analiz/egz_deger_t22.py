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
        F['p4n']=np.isnan(p4).astype(float);F['e1']=g.f_dp150_m.values;F['e2']=g.f_jgen100.values;F['e3']=g.f_fig3.values;F['s2'],F['sq'],F['hv']=pool_feats(t,h,g)
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

def pool_feats(t,h,g):
    n=len(g);e=H.get((t,asc2(h),int(g.kosu.iloc[0])))
    if not e or 'si' not in e or 'ik' not in e:return np.zeros(n),np.zeros(n),np.zeros(n)
    ix={int(x):i for i,x in enumerate(g.no)};s2=np.zeros(n);sq=np.zeros(n)
    try:
        for a,b,G in e['si']:s2[ix[int(b)]]+=1/float(G)
        for a,b,G in e['ik']:sq[ix[int(a)]]+=1/float(G);sq[ix[int(b)]]+=1/float(G)
    except Exception:return np.zeros(n),np.zeros(n),np.zeros(n)
    if s2.sum()<=0 or sq.sum()<=0:return np.zeros(n),np.zeros(n),np.zeros(n)
    f=lambda v:np.log((v+1e-3*v.mean())/(v+1e-3*v.mean()).sum())
    return f(s2),f(sq),np.ones(n)
cols=['lj','lm','rest','ilk','e1','e2','e3','s2','sq','hv'];R_=build(P,cols);R_.sort(key=lambda r:r[0]);days=sorted({r[0] for r in R_});cut=days[int(len(days)*0.6)]
fi=[r for r in R_ if r[0]<cut];fv=[r for r in fi if r[2][-1].max()>0]
Xf,Mf=pack(fi);thD=fit(Xf[:,:,:7],Mf,7);Xv,Mv=pack(fv);th3=fit(Xv[:,:,:9],Mv,9);print('fit D+',len(fi),'fit v3',len(fv))
def sm(sc):
    sc=sc-sc.max();e=np.exp(sc);return e/e.sum()
def qs(th,Xs,n):
    p1=sm(Xs.T@th[0]);Q=np.zeros((n,n))
    for a in range(n):
        rest_=[j for j in range(n) if j!=a];p2=sm((Xs.T@th[1])[rest_])
        for k,b in enumerate(rest_):Q[a,b]=p1[a]*p2[k]
    return Q

rows=[]
for t,h,X,g in R_:
    if X[-1].max()<=0:continue
    e=H.get((t,asc2(h),int(g.kosu.iloc[0])));n=X.shape[1]
    ix={int(v):i for i,v in enumerate(g.no)}
    QD=qs(thD,X[:7],n);Q3=qs(th3,X[:9],n)
    try:
        for tur in ('si','ik'):
            for a,b,G in e[tur]:
                a_,b_=ix[int(a)],ix[int(b)];G=float(G)
                if tur=='si':hit=(a_==0 and b_==1);qd=QD[a_,b_];q3=Q3[a_,b_]
                else:hit=({a_,b_}=={0,1});qd=QD[a_,b_]+QD[b_,a_];q3=Q3[a_,b_]+Q3[b_,a_]
                rows.append((t,tur,qd,q3,G,float(hit),t>=cut))
    except Exception:continue
Z=pd.DataFrame(rows,columns=['t','tur','qd','q3','G','y','test']);print('satır',len(Z),'fit satır',int((~Z.test).sum()),'test',int(Z.test.sum()))
from scipy.optimize import minimize as _mn
def lojit(F,y):
    F=np.column_stack([np.ones(len(F)),F])
    def f(w):
        z=F@w;ll=np.logaddexp(0,z)-y*z;p=1/(1+np.exp(-z));return ll.sum(),F.T@(p-y)
    return _mn(f,np.zeros(F.shape[1]),jac=True,method='L-BFGS-B').x
def loss(w,F,y):
    F=np.column_stack([np.ones(len(F)),F]);z=F@w;return np.logaddexp(0,z)-y*z
rng3=np.random.default_rng(53)
def bs(x,g,B=1000):
    s=pd.DataFrame({'g':g.values,'x':x.values}).groupby('g').x.agg(['sum','size']);o=[]
    for _ in range(B):
        t=s.iloc[rng3.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
for tur,ad in (('si','SIRALI İKİLİ'),('ik','İKİLİ')):
    X=Z[Z.tur==tur].copy();taban=(X.y*X.G).sum()/len(X);X['lp']=np.log((1/X.G*taban).clip(1e-6,0.999));X['ld']=np.log(X.qd.clip(1e-6,0.999));X['l3']=np.log(X.q3.clip(1e-6,0.999))
    tr=X[~X.test];te=X[X.test];y=tr.y.values;yt=te.y.values
    sp={'P (havuz)':['lp'],'Md (D+)':['ld'],'M3 (v3)':['l3'],'C_d (D+ + havuz)':['ld','lp'],'C_3 (v3 + havuz)':['l3','lp']}
    W={};L_={}
    print(f'\n[{ad}] fit {len(tr)} test {len(te)} bahis | taban ROI {taban:.3f}')
    for k,c in sp.items():
        w=lojit(tr[c].values,y);W[k]=w;L_[k]=loss(w,te[c].values,yt)
        print(f'  {k:18s} katsayılar(const,{",".join(c)}) {np.round(w,3)} | test log-kayıp/bahis {L_[k].mean()*1000:.3f}e-3')
    for k in ('Md (D+)','M3 (v3)','C_d (D+ + havuz)','C_3 (v3 + havuz)'):
        d=(L_['P (havuz)']-L_[k])*1000;a=bs(pd.Series(d),te.t);print(f'  P − {k:18s} kazanç {d.mean():+.3f}e-3 [{a[0]:+.3f},{a[1]:+.3f}]  (+ = {k.split()[0]} daha iyi)')
    # ikincil: C_3 EV kuralı
    z=np.column_stack([np.ones(len(te)),te.l3.values,te.lp.values])@W['C_3 (v3 + havuz)'];qc=1/(1+np.exp(-z));te=te.assign(evc=qc*te.G.values,ret=te.y*te.G)
    print(f'  taban ROI (test) {te.ret.mean():.3f}')
    for th in (1.0,1.15,1.3):
        sel=te[te.evc>=th]
        if len(sel)>=50:
            a=bs(sel.ret,sel.t);print(f'  C_3 EV≥{th}: bahis {len(sel)} isabet {sel.y.mean():.4f} ROI {sel.ret.mean():.3f} [{a[0]:.3f},{a[1]:.3f}]')
