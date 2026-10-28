"""T43 hipodrom kalibrasyonu. python3 data/analiz/hip_kalibrasyon.py <scratchpad>"""
import sys,numpy as np,pandas as pd
P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
P=P[P.p_Jason.notna()&P.p_piyasa.notna()&P.kazandi.notna()].copy()
P['g']=P.groupby(['tarih','hipodrom','kosu']).ngroup();n=P.groupby('g').no.transform('size');P=P[n>=6]
P['pm']=P.p_piyasa/P.groupby('g').p_piyasa.transform('sum');P['pj']=P.p_Jason/P.groupby('g').p_Jason.transform('sum');P['y']=P.kazandi.astype(float)
P['d']=P.y-P.pj;P['dm']=P.y-P.pm
rng=np.random.default_rng(5)
def ci(g,col,lvl=99.4):
    gun=g.tarih.values;ug=np.unique(gun);ix={u:np.where(gun==u)[0] for u in ug};v=g[col].values
    bs=[v[np.concatenate([ix[ug[i]] for i in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(1000)]
    a=(100-lvl)/2;return v.mean()*100,np.percentile(bs,a)*100,np.percentile(bs,100-a)*100
def egim(g):
    x=np.log(g.pj.clip(1e-6,1-1e-6)/(1-g.pj.clip(1e-6,1-1e-6))).values;y=g.y.values
    b=0.0;a=0.0
    for _ in range(30):
        p=1/(1+np.exp(-(a+b*x)));w=p*(1-p)+1e-9;X=np.c_[np.ones_like(x),x];H=X.T@(X*w[:,None]);gr=X.T@(y-p)
        s=np.linalg.solve(H,gr);a+=s[0];b+=s[1] if _>0 or True else 0
        if abs(s).max()<1e-8:break
    return b
print('at',len(P),'koşu',P.g.nunique(),P.tarih.min(),P.tarih.max())
print('hip | koşu | sapma(kazandi−pj) puan [%99,4 GA] | I.yarı | II.yarı | piyasa farkı | eğim')
for h,g in P.groupby('hipodrom'):
    m,lo,hi=ci(g,'d');m1=g[g.tarih<'2025-10'].d.mean()*100;m2=g[g.tarih>='2025-10'].d.mean()*100;mm=g.dm.mean()*100
    try:e=egim(g)
    except Exception:e=float('nan')
    ad='ADAY' if (lo>0 or hi<0) and np.sign(m1)==np.sign(m2) and np.sign(m)==np.sign(m1) and min(abs(m1),abs(m2))>=abs(m)/2 else ''
    print(f'{h:12s} {g.g.nunique():6d} {m:+.2f} [{lo:+.2f},{hi:+.2f}] {m1:+.2f} {m2:+.2f} {mm:+.2f} {e:.2f} {ad}',flush=True)
