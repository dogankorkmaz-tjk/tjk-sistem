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
def egim_ci(g):
    gun=g.tarih.values;ug=np.unique(gun);ix={u:np.where(gun==u)[0] for u in ug};bs=[]
    for _ in range(200):
        j=np.concatenate([ix[ug[k]] for k in rng.integers(0,len(ug),len(ug))]);bs.append(egim(g.iloc[j]))
    return np.percentile(bs,0.3),np.percentile(bs,99.7)
P['fav']=P.groupby('g').pj.rank(ascending=False,method='first')==1
print('at',len(P),'koşu',P.g.nunique(),P.tarih.min(),P.tarih.max())
print('NOT: koşu içi normalize olduğu için hipodrom ortalaması sapması 0 çıkar (anlamsız); asıl ölçü logit eğimi (1=kalibre, <1 aşırı güven) ve favori sapması.')
print('hip | koşu | eğim [%99,4 GA] | I.yarı eğim | II.yarı eğim | favori sapması puan [GA] | piyasa farkı fav')
for h,g in P.groupby('hipodrom'):
    e=egim(g);lo,hi=egim_ci(g);e1=egim(g[g.tarih<'2025-10']);e2=egim(g[g.tarih>='2025-10'])
    f=g[g.fav];m,flo,fhi=ci(f,'d');mm=f.dm.mean()*100
    ad='ADAY' if (lo>1 or hi<1) and (e1-1)*(e2-1)>0 and (e-1)*(e1-1)>0 else ''
    print(f'{h:11s} {g.g.nunique():5d} {e:.2f} [{lo:.2f},{hi:.2f}] {e1:.2f} {e2:.2f} | {m:+.2f} [{flo:+.2f},{fhi:+.2f}] {mm:+.2f} {ad}',flush=True)
