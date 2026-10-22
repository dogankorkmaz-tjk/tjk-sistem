import pandas as pd,numpy as np,warnings;warnings.filterwarnings('ignore')
from scipy.sparse import csr_matrix,hstack
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor
d=pd.read_pickle('fd.pkl')
d=d.dropna(subset=['FTHG','FTAG','FTR','AvgH','AvgD','AvgA','Avg>2.5','Avg<2.5']).sort_values('Date').reset_index(drop=True)
d['key_h']=d.lig+'|'+d.HomeTeam;d['key_a']=d.lig+'|'+d.AwayTeam
teams=sorted(set(d.key_h)|set(d.key_a));ti={t:i for i,t in enumerate(teams)};T=len(teams)
cut=pd.Timestamp('2025-07-01');tr=d[d.Date<cut];te=d[d.Date>=cut]
def design(df):
    n=len(df);r=np.arange(n)
    # satır 1: ev golü: hücum=ev takımı(+1), savunma=dep takımı, ev avantajı
    def mk(att,dfn,home):
        rows=np.r_[r,r,r];cols=np.r_[[ti[x] for x in att],[T+ti[x] for x in dfn],np.full(n,2*T)];vals=np.r_[np.ones(n),np.ones(n),np.ones(n)*home]
        return csr_matrix((vals,(rows,cols)),shape=(n,2*T+1))
    return mk(df.key_h,df.key_a,1.0),mk(df.key_a,df.key_h,0.0)
Xh,Xa=design(tr);X=__import__('scipy.sparse',fromlist=['vstack']).vstack([Xh,Xa]);y=np.r_[tr.FTHG,tr.FTAG]
age=(cut-tr.Date).dt.days.values;w=np.exp(-age/540.);W=np.r_[w,w]
m=PoissonRegressor(alpha=2e-3,max_iter=1000).fit(X,y,sample_weight=W)
Xh2,Xa2=design(te);lh=m.predict(Xh2);la=m.predict(Xa2)
def mat(l1,l2,k=9):
    a=poisson.pmf(np.arange(k+1),l1);b=poisson.pmf(np.arange(k+1),l2);return np.outer(a,b)
P=[];O=[];K=[]
for a,b in zip(lh,la):
    M=mat(a,b);M/=M.sum();P.append([np.tril(M,-1).sum(),np.trace(M),np.triu(M,1).sum()])
    tot=np.add.outer(np.arange(10),np.arange(10));O.append(M[tot>2.5].sum());K.append(M[1:,1:].sum())
P=np.array(P);O=np.array(O)
y1=te.FTR.map({'H':0,'D':1,'A':2}).values
q=np.column_stack([1/te.AvgH,1/te.AvgD,1/te.AvgA]);pm=q/q.sum(1,keepdims=True)
ll=lambda p:-np.mean(np.log(p[np.arange(len(y1)),y1]))
print('test maç',len(te),'1X2 log-kayıp: model %.4f piyasa %.4f'%(ll(P),ll(pm)))
yo=((te.FTHG+te.FTAG)>2.5).values.astype(float)
qo=np.column_stack([1/te['Avg>2.5'],1/te['Avg<2.5']]);po=qo[:,0]/qo.sum(1)
lo=lambda p:-np.mean(yo*np.log(p)+(1-yo)*np.log(1-p))
print('Üst2.5 log-kayıp: model %.4f piyasa %.4f'%(lo(O),lo(po)))
# birleştir: piyasa + model, lojistik karışım
best=None
for a in (0,.1,.2,.3,.5):
    pb=(1-a)*pm+a*P;pb/=pb.sum(1,keepdims=True);print('karışım a=%.1f 1X2 %.4f'%(a,ll(pb)),end=' | ')
    ob=(1-a)*po+a*O;print('Üst %.4f'%lo(ob))
ky=((te.FTHG>0)&(te.FTAG>0)).values.astype(float);print('KG gerçek oran %.3f model ort %.3f'%(ky.mean(),np.mean(K)))
mk=np.isfinite(po)&(po>0)&(po<1)
print('Üst2.5 geçerli',mk.sum(),'model %.4f piyasa %.4f'%(lo_m:=-np.mean(yo[mk]*np.log(O[mk])+(1-yo[mk])*np.log(1-O[mk])),-np.mean(yo[mk]*np.log(po[mk])+(1-yo[mk])*np.log(1-po[mk]))))
for a in (.1,.2,.3):
    ob=(1-a)*po[mk]+a*O[mk];print(a,'%.4f'%-np.mean(yo[mk]*np.log(ob)+(1-yo[mk])*np.log(1-ob)))
