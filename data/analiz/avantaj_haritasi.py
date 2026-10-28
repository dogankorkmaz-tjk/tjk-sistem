"""T48 avantaj haritası + güven filtresi. python3 data/analiz/avantaj_haritasi.py <scratchpad>"""
import sys,numpy as np,pandas as pd
P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
D=pd.read_pickle('/tmp/claude-0/jason_d.pkl');D['tarih']=D.tarih.astype(str)
D=D.drop_duplicates(['tarih','hipodrom','kosu','no'])[['tarih','hipodrom','kosu','no','yas','hnd_ok','mesafe','n_at','pist']]
P=P.merge(D,on=['tarih','hipodrom','kosu','no'],how='left')
P=P[P.p_Jason.notna()&P.p_piyasa.notna()&P.kazandi.notna()].copy()
P['g']=P.groupby(['tarih','hipodrom','kosu']).ngroup();n=P.groupby('g').no.transform('size');P=P[n>=6]
P['pj']=P.p_Jason/P.groupby('g').p_Jason.transform('sum');P['pm']=P.p_piyasa/P.groupby('g').p_piyasa.transform('sum')
P['rj']=P.groupby('g').pj.rank(ascending=False,method='first');P['rm']=P.groupby('g').pm.rank(ascending=False,method='first')
top=P[P.rj==1].set_index('g');mf=P[P.rm==1].set_index('g')
W=P[(P.kazandi==1)&(P.pj>0)&(P.pm>0)].drop_duplicates('g').set_index('g')
W['d']=np.log(W.pj)-np.log(W.pm);W['pj1']=top.pj.reindex(W.index);W['pm1']=mf.pm.reindex(W.index);W['uyus']=np.where(top.no.reindex(W.index)==mf.no.reindex(W.index),'uyuşuyor','ayrışıyor')
W['top_hit']=(top.kazandi.reindex(W.index)==1).astype(float)
W['gan']=np.where(top.kazandi.reindex(W.index)==1,top.ganyan.reindex(W.index),0.0)
b=lambda s,e,l:pd.cut(s,e,labels=l,right=False)
W['s_hip']=W.hipodrom;W['s_mesafe']=b(W.mesafe,[0,1301,1601,1901,5000],['≤1300','1400-1600','1700-1900','≥2000']);W['s_pist']=W.pist
W['s_alan']=b(W.n_at,[0,8,11,100],['≤7','8-10','11+']);W['s_hnd']=np.where(W.hnd_ok.notna(),'handikap','diğer')
W['s_modelp1']=b(W.pj1,[0,.2,.3,.4,1.01],['<0,20','0,20-0,30','0,30-0,40','≥0,40']);W['s_uyus']=W.uyus;W['s_pazarp1']=b(W.pm1,[0,.2,.3,.4,1.01],['<0,20','0,20-0,30','0,30-0,40','≥0,40'])
rng=np.random.default_rng(11)
def ci(s):
    gun=s.tarih.values;ug=np.unique(gun);ix={u:np.where(gun==u)[0] for u in ug};x=s.d.values
    bs=[x[np.concatenate([ix[ug[k]] for k in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(1000)];return np.percentile(bs,0.1),np.percentile(bs,99.9)
print('koşu',len(W),'ort d=%+.4f'%W.d.mean());print('dilim | koşu | ort d [GA %99,8] | I | II | model-1.sec isabet | ADAY')
for c in ['s_hip','s_mesafe','s_pist','s_alan','s_hnd','s_modelp1','s_uyus','s_pazarp1']:
    for v,s in W.groupby(c,observed=True):
        if len(s)<300:continue
        lo,hi=ci(s);m1=s[s.tarih<'2025-10'].d.mean();m2=s[s.tarih>='2025-10'].d.mean()
        ad='ADAY' if lo>0 and m1>0 and m2>0 else ''
        print(f'{c[2:]:9s} {str(v):10s} {len(s):5d} {s.d.mean():+.4f} [{lo:+.4f},{hi:+.4f}] {m1:+.4f} {m2:+.4f} {s.top_hit.mean()*100:.1f}% {ad}',flush=True)
