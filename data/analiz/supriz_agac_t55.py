"""T55: oran>=15 ağaç modeli. python3 data/analiz/supriz_agac_t55.py"""
import sys,numpy as np,pandas as pd,lightgbm as lgb
sys.path.insert(0,'data/analiz')
import video_ozellik as VO
np.random.seed(55)
d=pd.read_pickle('/tmp/claude-0/jason_d.pkl')
d=d[(d.kosmadi==False)|d.kosmadi.isna()].copy()
d=VO.ekle(d)
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
d['key']=d['at'].astype(str)+'|'+d['baba'].astype(str);g=d.groupby('key',sort=False)
d['on_ganyan']=g.ganyan.shift(1);d['on_kapi']=g.st.shift(1)/g.n_at.shift(1);d['on_hnd']=g.hnd.shift(1)
d['lp0']=np.log(d.p_piyasa.clip(1e-6));d['gevsek']=np.log(d.ganyan)-np.log(d.on_ganyan)
d['kapi']=d.st/d.n_at;d['kapi_iy']=d.on_kapi-d.kapi;d['jok_deg']=((d.jokey!=d.son_jokey)&d.son_jokey.notna()).astype(float)
d['kilo_f']=d.kilo-d.son_kilo;d['hnd_f']=d.hnd-d.on_hnd;d['dinlenme']=np.log1p(d.kgs)
d['pist_k']=d.pist.astype('category').cat.codes;d['hip_k']=d.hipodrom.astype('category').cat.codes
FV=[f'f_v{i}' for i in range(1,9)]
FN=[c for c in d.columns if c.startswith('f_') and c not in FV]+['lp0','n_at','mesafe','kapi','kapi_iy','gevsek','jok_deg','kilo_f','hnd_f','dinlenme','yas','pist_k','hip_k','kilo','hnd','st']
FN=list(dict.fromkeys(FN))
U=d[d.ganyan>=15].copy()
P=dict(objective='binary',num_leaves=8,min_data_in_leaf=100,learning_rate=0.03,feature_fraction=0.7,lambda_l2=10.0,verbose=-1,seed=55)
def kos(tr,te,F):
    # taban: lp0 lojistik
    from scipy.optimize import minimize
    X=np.c_[np.ones(len(tr)),tr.lp0.values];y=tr.kazandi.values.astype(float)
    f=lambda b:(-(y*np.log(1/(1+np.exp(-X@b))+1e-12)+(1-y)*np.log(1-1/(1+np.exp(-X@b))+1e-12)).sum())
    b=minimize(f,[-3,1.0],method='Nelder-Mead').x
    base=lambda df:b[0]+b[1]*df.lp0.values
    ds=lgb.Dataset(tr[F].values,label=y,init_score=base(tr));m=lgb.train(P,ds,300)
    z=base(te)+m.predict(te[F].values,raw_score=True)
    return m,base(te),z
def ll(z,y): p=1/(1+np.exp(-z));return -(y*np.log(p+1e-12)+(1-y)*np.log(1-p+1e-12))
def rapor(ad,te,zb,zm,F,m):
    y=te.kazandi.values.astype(float);dl=ll(zb,y)-ll(zm,y);ug=te.tarih.unique();gi={t:np.where(te.tarih.values==t)[0] for t in ug}
    bs=[dl[np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))])].mean() for _ in range(1000)]
    pb=1/(1+np.exp(-zb));pm=1/(1+np.exp(-zm));r=pm/pb;top=r>=np.quantile(r,0.95)
    ex=(y[top]-pb[top]).mean()*100
    print(f"{ad}: test {len(te)} at/{int(y.sum())} kazanan | log-kayıp iyileşmesi {dl.mean()*1000:+.3f} milli-nats/at [{np.percentile(bs,2.5)*1000:+.3f},{np.percentile(bs,97.5)*1000:+.3f}] | en yüksek %5: kazanma {y[top].mean()*100:.2f}% taban {pb[top].mean()*100:.2f}% fark {ex:+.2f}pp",flush=True)
    return dl
def onem(m,F):
    imp=sorted(zip(m.feature_importance('gain'),F),reverse=True)[:10];print('  önem (gain):',', '.join(f"{n} {g:.0f}" for g,n in imp),flush=True)
A=U[(U.tarih>='2023-06-01')&(U.tarih<='2025-09-30')];T1=U[(U.tarih>='2025-10-01')&(U.tarih<='2026-03-31')]
A2=U[(U.tarih>='2023-06-01')&(U.tarih<='2026-03-31')];T2=U[U.tarih>='2026-04-01']
m,zb,zm=kos(A,T1,FN);rapor('F1 N',T1,zb,zm,FN,m);onem(m,FN)
m,zb,zm=kos(A2,T2,FN);dN=rapor('F2 N',T2,zb,zm,FN,m);onem(m,FN)
FV2=FN+FV;m2,zb2,zm2=kos(A2,T2,FV2);dV=rapor('F2 V',T2,zb2,zm2,FV2,m2);onem(m2,FV2)
y=T2.kazandi.values.astype(float);dd=ll(zm,y)-ll(zm2,y);ug=T2.tarih.unique();gi={t:np.where(T2.tarih.values==t)[0] for t in ug}
bs=[dd[np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))])].mean() for _ in range(1000)]
print(f"F2 V−N: {dd.mean()*1000:+.3f} milli-nats/at [{np.percentile(bs,2.5)*1000:+.3f},{np.percentile(bs,97.5)*1000:+.3f}]")
# KEŞİF eki (ön kayıtta yok): en yüksek %5 (model/taban oranı) atlara 1 TL ganyan, gerçek getiri
def roi_ek(ad,te,zb,zm):
    pb=1/(1+np.exp(-zb));pm=1/(1+np.exp(-zm));r=pm/pb;top=(r>=np.quantile(r,0.95))
    s=te[top];ret=s.kazandi.values*s.ganyan.values-1.0;ug=s.tarih.unique();gi={t:np.where(s.tarih.values==t)[0] for t in ug}
    bs=[ret[np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))])].mean() for _ in range(1000)]
    srt=np.sort(s.kazandi.values*s.ganyan.values)[::-1];r3=(ret.sum()-srt[:3].sum()+0)/(len(s)) 
    print(f"{ad}: bayraklı {len(s)} at, kazanan {int(s.kazandi.sum())}, ort. oran {s.ganyan.mean():.1f} | ROI {ret.mean():+.1%} [{np.percentile(bs,2.5):+.1%},{np.percentile(bs,97.5):+.1%}] | en büyük 3 ödeme çıkarılırsa ≈{(ret.sum()-srt[:3].sum())/len(s):+.1%}",flush=True)
mm,zb,zm=kos(A,T1,FN);roi_ek('F1 N ROI',T1,zb,zm)
mm,zb,zm=kos(A2,T2,FN);roi_ek('F2 N ROI',T2,zb,zm)
mm,zb,zm=kos(A2,T2,FV2);roi_ek('F2 V ROI',T2,zb,zm)
