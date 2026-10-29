"""T54: oranı >=15 atlarda ayırt edici özellikler. python3 data/analiz/supriz_ozellik_t54.py"""
import numpy as np,pandas as pd,random
from scipy.optimize import minimize
random.seed(54)
d=pd.read_pickle('/tmp/claude-0/jason_d.pkl').sort_values(['tarih','hipodrom','kosu']).reset_index(drop=True)
d=d[(d.kosmadi==False)|d.kosmadi.isna()] if 'kosmadi' in d else d
d['key']=d['at'].astype(str)+'|'+d['baba'].astype(str)
g=d.groupby('key',sort=False)
d['on_ganyan']=g.ganyan.shift(1);d['on_kapi']=(g.st.shift(1)/g.n_at.shift(1));d['on_pct']=g.pct.shift(1);d['on_hnd']=g.hnd.shift(1)
d['lp0']=np.log(d.p_piyasa.clip(1e-6))
d['gevsek']=np.log(d.ganyan)-np.log(d.on_ganyan)                     # + = oran uzadı
d['kapi']=d.st/d.n_at
d['dis_kapi_iyi']=((d.on_kapi>0.7)&(d.on_pct<0.4)).astype(float)    # önceki koşuda dış kapı + üst yarı bitirme
d['jok_deg']=((d.jokey!=d.son_jokey)&d.son_jokey.notna()).astype(float)
d['kilo_f']=d.kilo-d.son_kilo
d['hnd_f']=d.hnd-d.on_hnd
d['dinlenme']=np.log1p(d.kgs)
d['kapi_iyilesme']=d.on_kapi-d.kapi                                  # + = bu koşuda daha içeri
ADAY=['gevsek','kapi','kapi_iyilesme','dis_kapi_iyi','jok_deg','kilo_f','hnd_f','dinlenme','yas','f_hpct3','f_jwin','f_st','f_kilodeg']
U=d[(d.ganyan>=15)].dropna(subset=ADAY+['lp0']).copy()
def fit(X,y,l2=5.0):
    n,k=X.shape
    def f(b):
        z=X@b;p=1/(1+np.exp(-z));ll=-(y*np.log(p+1e-12)+(1-y)*np.log(1-p+1e-12)).sum()+l2*(b[2:]@b[2:]);gr=X.T@(p-y)+2*l2*np.r_[0,0,b[2:]];return ll,gr
    return minimize(f,np.zeros(k),jac=True,method='L-BFGS-B').x
def mat(df,mu,sd): return np.c_[np.ones(len(df)),df.lp0.values,(df[ADAY].values-mu)/sd]
def llos(X,y,b): z=X@b;p=1/(1+np.exp(-z));return -(y*np.log(p+1e-12)+(1-y)*np.log(1-p+1e-12))
A=U[(U.tarih>='2023-06-01')&(U.tarih<='2025-12-31')];V=U[U.tarih>='2026-01-01']
mu=A[ADAY].values.mean(0);sd=A[ADAY].values.std(0)+1e-9
XA,yA=mat(A,mu,sd),A.kazandi.values.astype(float);XV,yV=mat(V,mu,sd),V.kazandi.values.astype(float)
print(f"Evren: oran>=15; keşif {len(A)} at ({int(yA.sum())} kazanan), doğrulama {len(V)} at ({int(yV.sum())} kazanan)")
def boot(df,B=300):
    ug=df.tarih.unique();gi={t:np.where(df.tarih.values==t)[0] for t in ug};out=[]
    X,y=mat(df,mu,sd),df.kazandi.values.astype(float)
    for _ in range(B):
        ix=np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))]);out.append(fit(X[ix],y[ix])[2:])
    return np.array(out)
np.random.seed(54)
bA=boot(A);bV=boot(V)
b=fit(XA,yA)
print("özellik            keşif katsayı [GA95]            2026 katsayı [GA99,5]")
for i,a in enumerate(ADAY):
    la,ha=np.percentile(bA[:,i],[2.5,97.5]);lv,hv=np.percentile(bV[:,i],[0.25,99.75]);bv=fit(XV,yV)[2+i]
    gerc='GERÇEK' if (la>0 or ha<0) and np.sign(b[2+i])==np.sign(bv) and (lv>0 or hv<0) else ''
    print(f"{a:16s} {b[2+i]:+.3f} [{la:+.3f},{ha:+.3f}]      {bv:+.3f} [{lv:+.3f},{hv:+.3f}] {gerc}")
sel=[i for i,a in enumerate(ADAY) if (np.percentile(bA[:,i],2.5)>0 or np.percentile(bA[:,i],97.5)<0)]
bb=np.zeros_like(b);bb[:2]=b[:2];bb[[2+i for i in sel]]=b[[2+i for i in sel]]
l0=llos(XV,yV,np.r_[fit(XA[:,:2],yA,0.0),np.zeros(len(ADAY))]);l1=llos(XV,yV,bb)
dl=l0-l1;ug=V.tarih.unique();gi={t:np.where(V.tarih.values==t)[0] for t in ug}
bs=[dl[np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))])].mean() for _ in range(1000)]
print(f"2026 log-kayıp iyileşmesi (seçilmiş özelliklerle, sabit model): {dl.mean()*1000:+.3f} milli-nats/at [{np.percentile(bs,2.5)*1000:+.3f},{np.percentile(bs,97.5)*1000:+.3f}]; seçilen: {[ADAY[i] for i in sel]}")
