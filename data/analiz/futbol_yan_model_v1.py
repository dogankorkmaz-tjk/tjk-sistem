import pandas as pd,numpy as np,warnings;warnings.filterwarnings('ignore')
from collections import defaultdict
from sklearn.linear_model import PoissonRegressor
d=pd.read_pickle('fd.pkl').sort_values('Date').reset_index(drop=True)
d=d.dropna(subset=['HC','AC','HY','AY','HF','AF','HS','AS','HST','AST']).reset_index(drop=True)
if 'Referee' not in d: d['Referee']=None
STATS=['C','Y','F','S','ST']  # korner, sarı, faul, şut, isabetli şut: H/A önekli sütunlar
dec=0.97
ti=defaultdict(lambda: defaultdict(float)); ref=defaultdict(lambda:[0.,0.,0.]) ;lg=defaultdict(lambda:defaultdict(float))
rows=[]
def team_feat(t,L,s):
    k=(L,t);c=ti[k]['n']
    if c<3: return None
    return ti[k][s+'_f']/c,ti[k][s+'_a']/c,c
for i,r in d.iterrows():
    L=r.lig;h,a=r.HomeTeam,r.AwayTeam
    lm=lg[L]
    if lm['n']>150:
        f={}
        ok=True
        for s in STATS:
            fh=team_feat(h,L,s);fa=team_feat(a,L,s)
            if not fh or not fa: ok=False;break
            lavg=lm[s]/lm['n']  # ev+dep toplam / maç
            f['h_'+s+'_f']=fh[0]/(lavg/2);f['h_'+s+'_a']=fh[1]/(lavg/2)
            f['a_'+s+'_f']=fa[0]/(lavg/2);f['a_'+s+'_a']=fa[1]/(lavg/2)
        if ok:
            rf=ref[r.Referee] if isinstance(r.Referee,str) else None
            f['ref_y']=(rf[0]/rf[2]/ (lm['Y']/lm['n']) if rf and rf[2]>=8 else 1.0)
            f['ref_f']=(rf[1]/rf[2]/ (lm['F']/lm['n']) if rf and rf[2]>=8 else 1.0)
            f['lig_C']=lm['C']/lm['n'];f['lig_Y']=lm['Y']/lm['n'];f['lig_F']=lm['F']/lm['n']
            f.update(dict(Date=r.Date,lig=L,kor=r.HC+r.AC,kart=r.HY+r.AY,faul=r.HF+r.AF,idx=i,ref=r.Referee));rows.append(f)
    # güncelle
    vals={'C':(r.HC,r.AC),'Y':(r.HY,r.AY),'F':(r.HF,r.AF),'S':(r.HS,r.AS),'ST':(r.HST,r.AST)}
    for (t,side) in ((h,0),(a,1)):
        k=(L,t)
        for kk in list(ti[k]): ti[k][kk]*=dec
        ti[k]['n']+=1
        for s,v in vals.items():
            ti[k][s+'_f']+=v[side];ti[k][s+'_a']+=v[1-side]
    for s,v in vals.items(): lm[s]+=v[0]+v[1]
    lm['n']+=1
    if isinstance(r.Referee,str):
        rr=ref[r.Referee];rr[0]+=r.HY+r.AY;rr[1]+=r.HF+r.AF;rr[2]+=1
X=pd.DataFrame(rows);print(len(X))
X.to_pickle('X.pkl')
fe=[c for c in X.columns if c.startswith(('h_','a_','ref_','lig_'))]
def dev(y,mu): 
    y=np.asarray(y,float);mu=np.maximum(mu,1e-6);return np.mean(2*(np.where(y>0,y*np.log(y/mu),0)-(y-mu)))
cut=pd.Timestamp('2025-07-01')
tr=X[X.Date<cut];te=X[X.Date>=cut]
print('train',len(tr),'test',len(te))
for tgt in ('kor','kart','faul'):
    m=PoissonRegressor(alpha=3e-3,max_iter=500).fit(tr[fe],tr[tgt]);mu=m.predict(te[fe])
    base=te['lig_'+{'kor':'C','kart':'Y','faul':'F'}[tgt]].values
    print(tgt,'MAE model %.3f taban %.3f'%(np.abs(mu-te[tgt]).mean(),np.abs(base-te[tgt]).mean()),'deviance model %.4f taban %.4f'%(dev(te[tgt],mu),dev(te[tgt],base)),'korelasyon %.3f'%np.corrcoef(mu,te[tgt])[0,1])
    if tgt=='kart':
        imp=pd.Series(m.coef_,fe).sort_values();print(imp.tail(6).round(3).to_dict())
