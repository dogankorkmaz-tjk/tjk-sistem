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

rF1=None
m,zb1,zm1=kos(A,T1,FN);pb1=1/(1+np.exp(-zb1));pm1=1/(1+np.exp(-zm1));esik=np.quantile(pm1/pb1,0.95)
m,zb,zm=kos(A2,T2,FN);pb=1/(1+np.exp(-zb));pm=1/(1+np.exp(-zm));T=T2.copy();T['pb']=pb;T['pm']=pm;T['r']=pm/pb
print(f"mutlak eşik r>={esik:.3f} (F1 %95)")
bay=T[T.r>=esik];gn=bay.groupby('tarih').size().reindex(T.tarih.unique(),fill_value=0)
print("günlük bayrak sayısı: ort %.2f, dağılım"%gn.mean(),gn.value_counts().sort_index().to_dict(), "| gün sayısı",len(gn))
ug=bay.tarih.unique();gi={t:np.where(bay.tarih.values==t)[0] for t in ug}
ex=(bay.kazandi.values-bay.pb.values)
bs=[ex[np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))])].mean()*100 for _ in range(1000)]
print(f"bayraklı {len(bay)} at: kazanma {bay.kazandi.mean()*100:.2f}% taban {bay.pb.mean()*100:.2f}% fark {ex.mean()*100:+.2f}pp [{np.percentile(bs,2.5):+.2f},{np.percentile(bs,97.5):+.2f}]")
# (b) gün düzeyi
G=T.groupby('tarih').agg(bek=('pm','sum'),bekb=('pb','sum'),ger=('kazandi','sum'))
G['q']=pd.qcut(G.bek,4,labels=False,duplicates='drop')
print("gün dörtte birlikleri (beklenen Σp_model → gerçek ortalama / taban beklentisi):")
for q,gg in G.groupby('q'): print(f"  Q{int(q)+1}: {len(gg)} gün, beklenen {gg.bek.mean():.2f}, taban {gg.bekb.mean():.2f}, GERÇEK {gg.ger.mean():.2f}")
dif=[];gl=list(G.index)
for _ in range(1000):
    s_=G.loc[np.random.choice(gl,len(gl))];hi=s_[s_.q==s_.q.max()].ger.mean();lo=s_[s_.q==0].ger.mean();dif.append(hi-lo)
print(f"üst−alt dörtte bir (gerçek sayı): {G[G.q==G.q.max()].ger.mean()-G[G.q==0].ger.mean():+.2f} [{np.percentile(dif,2.5):+.2f},{np.percentile(dif,97.5):+.2f}]")
# (c) koşu düzeyi AUC
from sklearn.metrics import roc_auc_score
R=T.groupby(['tarih','hipodrom','kosu']).agg(sm=('pm','sum'),sb=('pb','sum'),ger=('kazandi','max')).reset_index()
a1=roc_auc_score(R.ger,R.sm);a0=roc_auc_score(R.ger,R.sb);ugr=R.tarih.unique();d_=[]
for _ in range(500):
    s_=pd.concat([R[R.tarih==t] for t in np.random.choice(ugr,len(ugr))]);
    d_.append(roc_auc_score(s_.ger,s_.sm)-roc_auc_score(s_.ger,s_.sb))
print(f"koşu düzeyi AUC model {a1:.4f} taban {a0:.4f} fark {a1-a0:+.4f} [{np.percentile(d_,2.5):+.4f},{np.percentile(d_,97.5):+.4f}] | koşu {len(R)} süprizli {int(R.ger.sum())}")
