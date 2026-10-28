"""T47 yürüyen yeniden kalibrasyon (önceki koşu<=2). python3 data/analiz/kalibre_az_kosmus.py <scratchpad>"""
import sys,numpy as np,pandas as pd
P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
D=pd.read_pickle('/tmp/claude-0/jason_d.pkl');D['tarih']=D.tarih.astype(str)
D=D.drop_duplicates(['tarih','hipodrom','kosu','no'])[['tarih','hipodrom','kosu','no','h_n']]
P=P.merge(D,on=['tarih','hipodrom','kosu','no'],how='left')
P=P[P.p_Jason.notna()&P.kazandi.notna()&P.h_n.notna()].copy()
P['g']=P.groupby(['tarih','hipodrom','kosu']).ngroup();n=P.groupby('g').no.transform('size');P=P[n>=6]
P['pj']=P.p_Jason/P.groupby('g').p_Jason.transform('sum');P['y']=P.kazandi.astype(float);P['ay']=P.tarih.str[:7]
P['G']=P.h_n<=2;p=P.pj.clip(1e-6,1-1e-6);P['lg']=np.log(p/(1-p))
def fit(x,y):
    a=b=0.0
    for _ in range(30):
        q=1/(1+np.exp(-(a+b*x)));w=q*(1-q)+1e-9;X=np.c_[np.ones_like(x),x];s=np.linalg.solve(X.T@(X*w[:,None]),X.T@(y-q));a+=s[0];b+=s[1]
        if abs(s).max()<1e-8:break
    return a,b
P['pn']=P.pj
for m in sorted(P.ay.unique()):
    if m<'2025-01':continue
    tr=P[(P.ay<m)&P.G];a,b=fit(tr.lg.values,tr.y.values);ix=(P.ay==m)&P.G
    P.loc[ix,'pn']=1/(1+np.exp(-(a+b*P.loc[ix,'lg'])))
    print(m,'a=%.3f b=%.3f n_G=%d'%(a,b,ix.sum()),flush=True)
P=P[P.ay>='2025-01'].copy();P['pn']=P.pn/P.groupby('g').pn.transform('sum')
W=P[P.y==1].copy();W=W[W.pj>0];W['d']=-np.log(W.pn)+np.log(W.pj)
print('kazanan log-kaybı farkı (yeni−eski) koşu başına: %+.5f (n=%d)'%(W.d.mean(),len(W)))
rng=np.random.default_rng(3)
def ci(x,gun):
    ug=np.unique(gun);ix={u:np.where(gun==u)[0] for u in ug};bs=[x[np.concatenate([ix[ug[k]] for k in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(1000)];return np.percentile(bs,2.5),np.percentile(bs,97.5)
for ad,s in [('TÜM',W),('I (…2025-09)',W[W.tarih<'2025-10']),('II (2025-10…)',W[W.tarih>='2025-10'])]:
    lo,hi=ci(s.d.values,s.tarih.values);print('%-14s %+.5f [%+.5f,%+.5f] n=%d'%(ad,s.d.mean(),lo,hi,len(s)))
