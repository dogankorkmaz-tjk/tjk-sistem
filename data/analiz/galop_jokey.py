"""T31 idman jokeyi testi. python3 data/analiz/galop_jokey.py"""
import sys,glob,collections,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from scipy.optimize import minimize
from tjk import g1
GAM=np.array([1,0.80,0.67,0.59,0.52])
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P=P[P.tarih>='2026-02-01']
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','at','jokey']];J['tarih']=J.tarih.astype(str)
D=P.merge(J.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='inner')
D=D[D.sira.notna()].copy();print('satır',len(D),D.tarih.min(),D.tarih.max())
nrm=g1._nrm
def anah(s):
    s=nrm(s).replace('.',' ').split()
    s=[x for x in s if x!='AP']
    return (s[0][0]+s[-1]) if s else ''
gal=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('/home/claude/tjk-sistem/data/galop/*.csv.gz'))])
gal['atn']=gal['at'].map(nrm);gal['itd']=pd.to_datetime(gal.it);gal['jk']=gal.jokey.fillna('').map(anah);gal['apr']=gal.jokey.fillna('').str.upper().str.contains('APRANT').astype(float)
GA={a:x.sort_values('itd') for a,x in gal.groupby('atn')}
f7=[];fg=[]
for r in D.itertuples():
    t=pd.Timestamp(r.tarih);f7.append(g1.galop_f(r.at,pd.Timestamp(r.tarih).date()))
    x=GA.get(nrm(r.at));g=[0.0,0.0,0.0]
    if x is not None:
        y=x[(x.itd<t)&(x.itd>=t-pd.Timedelta(days=28))]
        if len(y):
            rk=anah(r.jokey);g=[min(float((y.jk==rk).sum()),3.0),float(y.apr.mean()),min(float(y.jk.nunique()),3.0)]
    fg.append(g)
D[[f'g{i}' for i in range(7)]]=np.array(f7);D[['gj_ayni','gj_apr','gj_ayrik']]=np.array(fg)
print('idmanı olan at oranı',(D.g0>0).mean().round(3),'| yarış jokeyi idmanda bindi',(D.gj_ayni>0).mean().round(3))
D['lp']=np.log(D.p_Jason.clip(lower=1e-6));D['ay']=D.tarih.str[:7]
ok=D.groupby(['tarih','hipodrom','kosu']).sira.apply(lambda s:all((s==k).sum()==1 for k in range(1,6)) and len(s)>=6)
D=D.join(ok.rename('ok'),on=['tarih','hipodrom','kosu']);D=D[D.ok].copy();D['rid']=D.groupby(['tarih','hipodrom','kosu']).ngroup();print('çözülmüş koşu',D.rid.nunique())
def pack(df,cols):
    r=df.rid.values;st=np.r_[0,np.nonzero(np.diff(r))[0]+1];n=np.diff(np.r_[st,len(df)]);N=len(st);M=n.max()
    LM=np.full((N,M),-1e9);X=np.zeros((N,M,len(cols)));SR=np.zeros((N,M));
    for k,(a,b) in enumerate(zip(st,np.r_[st[1:],len(df)])):
        LM[k,:b-a]=df.lp.values[a:b];SR[k,:b-a]=df.sira.values[a:b]
        if cols:X[k,:b-a]=df[cols].values[a:b]
    return LM,X,SR
def steps(S,SR):
    N=len(S);idx=np.arange(N);msk=S>-1e8;out=[]
    for j in range(5):
        z=np.where(msk,GAM[j]*S,-1e30);z-=z.max(1,keepdims=True);e=np.exp(z);p=e/e.sum(1,keepdims=True)
        w=np.argmax(SR==j+1,axis=1);out.append(np.log(p[idx,w]+1e-12));msk=msk&(SR!=j+1)
    return np.array(out)
def fit(df,cols,lam=50.0):
    LM,X,SR=pack(df,cols);msk=LM>-1e8;mu=X[msk].mean(0);sd=X[msk].std(0)+1e-9;Z=np.where(msk[...,None],(X-mu)/sd,0.0);N=len(LM);idx=np.arange(N)
    def f(b):
        S=np.where(msk,LM+Z@b,-1e9);m=msk.copy();L=0.0;gS=np.zeros_like(S)
        for j in range(5):
            z=np.where(m,GAM[j]*S,-1e30);z-=z.max(1,keepdims=True);e=np.exp(z);p=e/e.sum(1,keepdims=True);w=np.argmax(SR==j+1,axis=1)
            L-=np.log(p[idx,w]+1e-12).sum();d=p.copy();d[idx,w]-=1;gS+=GAM[j]*d;m=m&(SR!=j+1)
        return L+lam*(b@b),np.einsum('nm,nmk->k',gS,Z)+2*lam*b
    b=minimize(f,np.zeros(len(cols)),jac=True,method='L-BFGS-B').x;return b,mu,sd
def score(df,cols,t):
    b,mu,sd=t;LM,X,SR=pack(df,cols);msk=LM>-1e8;S=np.where(msk,LM+np.where(msk[...,None],(X-mu)/sd,0.0)@b,-1e9);return steps(S,SR)
G=[f'g{i}' for i in range(7)];GJ=['gj_ayni','gj_apr','gj_ayrik']
rows=[];ays=sorted(D.ay.unique())
for a in [x for x in ays if x>='2026-05']:
    tr=D[D.ay<a];te=D[D.ay==a]
    if tr.rid.nunique()<300 or te.rid.nunique()<30: continue
    A=score(te,G,fit(tr,G));B=score(te,G+GJ,fit(tr,G+GJ));C=score(te,[],(np.zeros(0),np.zeros(0),np.ones(0)) if False else (np.zeros(0),np.zeros(0),np.ones(0)))
    gun=te.groupby('rid').tarih.first().values
    rows.append((a,gun,B-A,A-C));print(a,te.rid.nunique(),'gj kazancı ilk5 %.4f'%((B-A).sum(0).mean()),'galop kazancı ilk5 (yaklaşık) %.4f'%((A-C).sum(0).mean()),flush=True)
gun=np.concatenate([r[1] for r in rows]);DB=np.concatenate([r[2] for r in rows],axis=1);DA=np.concatenate([r[3] for r in rows],axis=1)
ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};rng=np.random.default_rng(3)
def rap(Dm,ad):
    print(ad,'koşu',Dm.shape[1])
    for nm,ix in [('kazanan',[0]),('ikili',[0,1]),('üçlü',[0,1,2]),('ilk4',[0,1,2,3]),('ilk5',[0,1,2,3,4])]:
        x=Dm[ix].sum(0);bs=[x[np.concatenate([gi[ug[i]] for i in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(1000)]
        print(f'  {nm:8s} {x.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]')
rap(DB,'İDMAN JOKEYİ eklenince (G+GJ − G, pozitif=iyi)')
