import pandas as pd,numpy as np,warnings;warnings.filterwarnings('ignore')
from sklearn.linear_model import PoissonRegressor
X=pd.read_pickle('X.pkl')
d=pd.read_pickle('fd.pkl').sort_values('Date').reset_index(drop=True)
d=d.dropna(subset=['HC','AC','HY','AY','HF','AF','HS','AS','HST','AST']).reset_index(drop=True)
X=X.dropna(subset=[c for c in X.columns if c!='ref'])
B4={'Galatasaray','Fenerbahce','Besiktas','Trabzonspor'}; FK={'Goztep','Samsunspor','Kocaelispor'}
H=d.HomeTeam.reindex(X.idx.values).values;A=d.AwayTeam.reindex(X.idx.values).values
X['derbi4']=[(h in B4 and a in B4)*1. for h,a in zip(H,A)]
X['derbi_goz_fk']=[((h in FK and a in FK))*1. for h,a in zip(H,A)]
X['fk_ev_buyuk']=[(h in FK and a in B4)*1. for h,a in zip(H,A)]
X['fk_dep_buyuk']=[(a in FK and h in B4)*1. for h,a in zip(H,A)]
for c in ('derbi4','derbi_goz_fk','fk_ev_buyuk','fk_dep_buyuk'): print(c,int(X[c].sum()))
fe=[c for c in X.columns if c.startswith(('h_','a_','ref_','lig_','h2h','o_'))]
fe2=fe+['derbi4','derbi_goz_fk','fk_ev_buyuk','fk_dep_buyuk']
cut=pd.Timestamp('2025-07-01');tr=X[X.Date<cut];te=X[X.Date>=cut]
def dev(y,mu):
    y=np.asarray(y,float);mu=np.maximum(mu,1e-6);return np.mean(2*(np.where(y>0,y*np.log(y/mu),0)-(y-mu)))
for t in ('kart','faul'):
    m1=PoissonRegressor(alpha=3e-3,max_iter=500).fit(tr[fe],tr[t]);m2=PoissonRegressor(alpha=3e-3,max_iter=500).fit(tr[fe2],tr[t])
    print(t,'dev derbisiz %.4f derbili %.4f'%(dev(te[t],m1.predict(te[fe])),dev(te[t],m2.predict(te[fe2]))),dict(zip(fe2[-4:],m2.coef_[-4:].round(3))))
# doğrudan farklar: tüm veri, yalnız Süper Lig, ortalama kart
T=X[X.lig=='T1']
for c in ('derbi4','derbi_goz_fk','fk_ev_buyuk','fk_dep_buyuk'):
    a=T[T[c]==1];b=T[T[c]==0]
    if len(a): print(c,len(a),'ort kart %.2f (diğer %.2f)'%(a.kart.mean(),b.kart.mean()),'faul %.1f (%.1f)'%(a.faul.mean(),b.faul.mean()),'kor %.1f (%.1f)'%(a.kor.mean(),b.kor.mean()))
