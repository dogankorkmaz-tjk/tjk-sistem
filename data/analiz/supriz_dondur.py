"""T57: süpriz modelini (T55 N, F2 eğitimi: 2023-06..2026-03) dondur -> data/supriz/model_n.json. python3 data/analiz/supriz_dondur.py"""
import sys,json,numpy as np,pandas as pd,lightgbm as lgb
from scipy.optimize import minimize
d=pd.read_pickle('/tmp/claude-0/jason_d.pkl')
d=d[(d.kosmadi==False)|d.kosmadi.isna()].copy()
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
d['key']=d['at'].astype(str)+'|'+d['baba'].astype(str);g=d.groupby('key',sort=False)
d['on_ganyan']=g.ganyan.shift(1);d['on_kapi']=g.st.shift(1)/g.n_at.shift(1);d['on_hnd']=g.hnd.shift(1)
d['lp0']=np.log(d.p_piyasa.clip(1e-6));d['gevsek']=np.log(d.ganyan)-np.log(d.on_ganyan)
d['kapi']=d.st/d.n_at;d['kapi_iy']=d.on_kapi-d.kapi;d['jok_deg']=((d.jokey!=d.son_jokey)&d.son_jokey.notna()).astype(float)
d['kilo_f']=d.kilo-d.son_kilo;d['hnd_f']=d.hnd-d.on_hnd;d['dinlenme']=np.log1p(d.kgs)
PIST=sorted(d.pist.dropna().unique().tolist());HIP=sorted(d.hipodrom.dropna().unique().tolist())
d['pist_k']=d.pist.map({p:i for i,p in enumerate(PIST)}).fillna(-1);d['hip_k']=d.hipodrom.map({p:i for i,p in enumerate(HIP)}).fillna(-1)
FN=[c for c in d.columns if c.startswith('f_')]+['lp0','n_at','mesafe','kapi','kapi_iy','gevsek','jok_deg','kilo_f','hnd_f','dinlenme','yas','pist_k','hip_k','kilo','hnd','st']
FN=list(dict.fromkeys(FN))
U=d[d.ganyan>=15].copy();A2=U[(U.tarih>='2023-06-01')&(U.tarih<='2026-03-31')];y=A2.kazandi.values.astype(float)
X=np.c_[np.ones(len(A2)),A2.lp0.values]
f=lambda b:(-(y*np.log(1/(1+np.exp(-X@b))+1e-12)+(1-y)*np.log(1-1/(1+np.exp(-X@b))+1e-12)).sum())
b=minimize(f,[-3,1.0],method='Nelder-Mead').x
P=dict(objective='binary',num_leaves=8,min_data_in_leaf=100,learning_rate=0.03,feature_fraction=0.7,lambda_l2=10.0,verbose=-1,seed=55)
m=lgb.train(P,lgb.Dataset(A2[FN].values,label=y,init_score=b[0]+b[1]*A2.lp0.values),300)
T1=U[(U.tarih>='2025-10-01')&(U.tarih<='2026-03-31')]
# F1 eşiği (T56): ayrı F1 modeli
A1=U[(U.tarih>='2023-06-01')&(U.tarih<='2025-09-30')];y1=A1.kazandi.values.astype(float);X1=np.c_[np.ones(len(A1)),A1.lp0.values]
f1=lambda bb:(-(y1*np.log(1/(1+np.exp(-X1@bb))+1e-12)+(1-y1)*np.log(1-1/(1+np.exp(-X1@bb))+1e-12)).sum());b1=minimize(f1,[-3,1.0],method='Nelder-Mead').x
m1=lgb.train(P,lgb.Dataset(A1[FN].values,label=y1,init_score=b1[0]+b1[1]*A1.lp0.values),300)
zb=b1[0]+b1[1]*T1.lp0.values;zm=zb+m1.predict(T1[FN].values,raw_score=True);esik=float(np.quantile(np.exp(zm-zb)*(1+np.exp(zb))/(1+np.exp(zm)),0.95))
print('eşik',esik,'(T56: 1.686)')
out=dict(b=[float(b[0]),float(b[1])],feat=FN,pist=PIST,hip=HIP,esik=1.686,esik_yeniden=esik,egitim='2023-06..2026-03',n_egitim=int(len(A2)),agaclar=[t['tree_structure'] for t in m.dump_model()['tree_info']])
json.dump(out,open('data/supriz/model_n.json','w'),separators=(',',':'))
Z=A2[FN].values[:2000];np.save('/tmp/claude-0/supriz_dogrulama_X.npy',Z);np.save('/tmp/claude-0/supriz_dogrulama_y.npy',m.predict(Z,raw_score=True))
print('kaydedildi',len(FN),'özellik',len(out['agaclar']),'ağaç')
