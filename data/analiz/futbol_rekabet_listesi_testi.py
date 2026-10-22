import pandas as pd,numpy as np,json,warnings;warnings.filterwarnings('ignore')
from sklearn.linear_model import PoissonRegressor
S='/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad'
X=pd.read_pickle(S+'/X.pkl')
d=pd.read_pickle(S+'/fd.pkl').sort_values('Date').reset_index(drop=True)
d=d.dropna(subset=['HC','AC','HY','AY','HF','AF','HS','AS','HST','AST']).reset_index(drop=True)
X=X.dropna(subset=[c for c in X.columns if c!='ref'])
H=d.HomeTeam.reindex(X.idx.values).values;A=d.AwayTeam.reindex(X.idx.values).values
G=(d.FTHG+d.FTAG).reindex(X.idx.values).values;X['gol']=G
R={tuple(p) for p in json.load(open('data/futbol/rekabet.json'))['ciftler']}
X['rek']=[1. if tuple(sorted((h,a))) in R else 0. for h,a in zip(H,A)]
T=X[X.lig=='T1'];a=T[T.rek==1];b=T[T.rek==0]
print('rekabet maçı',len(a))
for c in ('kart','faul','kor','gol'): print(c,'%.2f vs %.2f'%(a[c].mean(),b[c].mean()))
fe=[c for c in X.columns if c.startswith(('h_','a_','ref_','lig_','h2h','o_'))]
cut=pd.Timestamp('2025-07-01');tr=X[X.Date<cut];te=X[X.Date>=cut]
def dev(y,mu):
    y=np.asarray(y,float);mu=np.maximum(mu,1e-6);return np.mean(2*(np.where(y>0,y*np.log(y/mu),0)-(y-mu)))
for t in ('kart','faul','kor','gol'):
    m1=PoissonRegressor(alpha=3e-3,max_iter=500).fit(tr[fe],tr[t]);m2=PoissonRegressor(alpha=3e-3,max_iter=500).fit(tr[fe+['rek']],tr[t])
    print(t,'katsayı rek %.3f'%m2.coef_[-1],'test sapma %.4f -> %.4f'%(dev(te[t],m1.predict(te[fe])),dev(te[t],m2.predict(te[fe+['rek']]))))
