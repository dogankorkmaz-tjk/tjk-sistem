"""T60: süpriz yedek ayak ROI. python3 data/analiz/supriz_sirali_t60.py"""
import sys,glob,numpy as np,pandas as pd
src=open('data/analiz/supriz_say_t56.py').read()
exec(src[:src.index('rF1=None')])
sys.path.insert(0,'.')
from tjk import besli as B
m,zb1,zm1=kos(A,T1,FN);pb1=1/(1+np.exp(-zb1));pm1=1/(1+np.exp(-zm1));esik=np.quantile(pm1/pb1,0.95)
T1=T1.copy();T1['bay']=(pm1/pb1)>=esik
m,zb,zm=kos(A2,T2,FN);pb=1/(1+np.exp(-zb));pm=1/(1+np.exp(-zm));T2=T2.copy();T2['bay']=(pm/pb)>=esik
F=pd.concat([T1,T2]);F=F[F.bay][['tarih','hipodrom','kosu','no']]
o=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('data/odeme/20*.csv.gz'))]);o=o[o.tur.str.contains('SIRALI 5')&~o.tur.str.contains('DEVİR')]
o=o[o.tarih>='2025-10-01'].drop_duplicates(['tarih','hipodrom','kosu'])
print('esik',esik,'bayrak',len(F),'odeme satiri',len(o),flush=True)
rows=[]
for (t,h,k),g in F.groupby(['tarih','hipodrom','kosu']):
    od=o[(o.tarih==t)&(o.hipodrom==h)&(o.kosu==k)]
    if not len(od): continue
    r=d[(d.tarih==t)&(d.hipodrom==h)&(d.kosu==k)].reset_index(drop=True)
    if len(r)<8: continue
    p=(r.p_piyasa/r.p_piyasa.sum()).values;nos=r.no.values
    kp=B.kupon_g(list(p),96,None)
    if not kp: continue
    S=[list(s) for s in kp[0]];S2=[list(s) for s in S]
    for no in g.no:
        ix=np.where(nos==no)[0]
        if not len(ix): continue
        for kk in (2,3,4):
            if ix[0] not in S2[kk]: S2[kk].append(ix[0])
    v1=B.gecerli_say(S);v2=B.gecerli_say(S2)
    win=[int(x) for x in str(od.kombo.iloc[0]).split('/')]
    wi=[int(np.where(nos==w)[0][0]) if w in nos else -1 for w in win]
    hit=lambda SS:all(wi[i]>=0 and wi[i] in SS[i] for i in range(5))
    pay=float(od.tutar.iloc[0])
    rows.append((t,h,k,v1,v2,pay*hit(S),pay*hit(S2)))
R=pd.DataFrame(rows,columns=['tarih','hip','kosu','v1','v2','r1','r2'])
R['dc']=(R.v2-R.v1)*1.25;R['dr']=R.r2-R.r1
print(f"koşu {len(R)} | taban maliyet {R.v1.sum()*1.25:.0f} getiri {R.r1.sum():.0f} ROI {R.r1.sum()/(R.v1.sum()*1.25):.3f} | varyant maliyet {R.v2.sum()*1.25:.0f} getiri {R.r2.sum():.0f}")
print(f"ek isabet {(R.dr>0).sum()} (taban isabet {(R.r1>0).sum()}, varyant {(R.r2>0).sum()}) | marjinal: ek maliyet {R.dc.sum():.0f} ek getiri {R.dr.sum():.0f} ROI {R.dr.sum()/max(R.dc.sum(),1e-9):.3f}")
ug=R.tarih.unique();gi={t:np.where(R.tarih.values==t)[0] for t in ug};np.random.seed(60);bs=[]
for _ in range(1000):
    ix=np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))]);bs.append(R.dr.values[ix].sum()/max(R.dc.values[ix].sum(),1e-9))
print(f"marjinal ROI %95 [{np.percentile(bs,2.5):.3f},{np.percentile(bs,97.5):.3f}]")
