"""T46 dilim kalibrasyonu (T43 yöntemi): Jason logit eğimi dilim bazında. python3 data/analiz/dilim_kalibrasyon.py <scratchpad>"""
import sys,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz')
P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
D=pd.read_pickle('/tmp/claude-0/jason_d.pkl');D['tarih']=D.tarih.astype(str)
D=D.drop_duplicates(['tarih','hipodrom','kosu','no'])[['tarih','hipodrom','kosu','no','h_n','yas','hnd_ok','mesafe','n_at','pist']]
P=P.merge(D,on=['tarih','hipodrom','kosu','no'],how='left')
P=P[P.p_Jason.notna()&P.p_piyasa.notna()&P.kazandi.notna()].copy()
P['g']=P.groupby(['tarih','hipodrom','kosu']).ngroup();n=P.groupby('g').no.transform('size');P=P[n>=6]
P['pj']=P.p_Jason/P.groupby('g').p_Jason.transform('sum');P['pm']=P.p_piyasa/P.groupby('g').p_piyasa.transform('sum');P['y']=P.kazandi.astype(float)
rng=np.random.default_rng(7)
def egim(g):
    p=g.pj.clip(1e-6,1-1e-6).values;x=np.log(p/(1-p));y=g.y.values;a=b=0.0
    for _ in range(30):
        q=1/(1+np.exp(-(a+b*x)));w=q*(1-q)+1e-9;X=np.c_[np.ones_like(x),x];s=np.linalg.solve(X.T@(X*w[:,None]),X.T@(y-q));a+=s[0];b+=s[1]
        if abs(s).max()<1e-8:break
    return b
def ci(g):
    gun=g.tarih.values;ug=np.unique(gun);ix={u:np.where(gun==u)[0] for u in ug};bs=[]
    for _ in range(200):bs.append(egim(g.iloc[np.concatenate([ix[ug[k]] for k in rng.integers(0,len(ug),len(ug))])]))
    return np.percentile(bs,0.1),np.percentile(bs,99.9)
band=lambda s,e,l:pd.cut(s,e,labels=l,right=True)
P['s_gecmis']=band(P.h_n,[-1,0,2,5,10,1000],['0 koşu','1-2','3-5','6-10','11+']);P['s_alan']=band(P.n_at,[0,7,10,100],['≤7','8-10','11+'])
P['s_mesafe']=band(P.mesafe,[0,1300,1600,1900,5000],['≤1300','1400-1600','1700-1900','≥2000']);P['s_pist']=P.pist;P['s_yas']=band(P.yas,[0,2,3,4,5,50],['2','3','4','5','6+'])
P['s_hnd']=np.where(P.hnd_ok.notna(),'handikap','diğer')
print('at',len(P),'koşu',P.g.nunique());print('dilim | koşu*at | eğim [%99,8 GA] | I.yarı | II.yarı | ADAY')
for c in ['s_gecmis','s_alan','s_mesafe','s_pist','s_yas','s_hnd']:
    for v,g in P.groupby(c,observed=True):
        if len(g)<3000:continue
        e=egim(g);lo,hi=ci(g);e1=egim(g[g.tarih<'2025-10']);e2=egim(g[g.tarih>='2025-10'])
        ad='ADAY' if (lo>1 or hi<1) and (e1-1)*(e2-1)>0 and (e-1)*(e1-1)>0 else ''
        print(f'{c[2:]:8s} {str(v):10s} {len(g):7d} {e:.2f} [{lo:.2f},{hi:.2f}] {e1:.2f} {e2:.2f} {ad}',flush=True)
