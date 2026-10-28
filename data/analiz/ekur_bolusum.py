"""T34 ekür içi bölüşüm. python3 data/analiz/ekur_bolusum.py"""
import numpy as np,pandas as pd
from scipy.optimize import minimize_scalar
GAM=np.array([1,0.80,0.67,0.59,0.52])
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl')
D=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left');D['ekur']=D.ekur.fillna(0).astype(int);D=D[D.sira.notna()&D.p_Jason.notna()]
races=[]
for k,g in D.groupby(['tarih','hipodrom','kosu']):
    if len(g)<6 or not all((g.sira==j).sum()==1 for j in range(1,6)): continue
    g=g.reset_index(drop=True);pairs=[]
    for e,h in g[g.ekur>0].groupby('ekur'):
        if len(h)==2:
            i,j=h.index.values
            if g.p_Jason[i]<g.p_Jason[j]: i,j=j,i
            pairs.append((i,j))
    if not pairs: continue
    races.append(dict(t=k[0],p=g.p_Jason.values/g.p_Jason.sum(),sr=g.sira.values.astype(int),pairs=pairs))
print('ekür çiftli çözülmüş koşu',len(races),races[0]['t'],races[-1]['t'])
def ll(r,th):
    p=r['p'].copy()
    for i,j in r['pairs']:
        Pp=p[i]+p[j];s=p[i]/Pp;l=np.log(s/(1-s));a=Pp/(1+np.exp(-th*l));p[i]=a;p[j]=Pp-a
    order=np.argsort(r['sr'])[:5];m=np.ones(len(p),bool);out=np.zeros(5)
    for k in range(5):
        z=GAM[k]*np.log(np.clip(p,1e-12,None));z=np.where(m,z,-1e9);z-=z.max();out[k]=z[order[k]]-np.log(np.exp(z[m]).sum());m[order[k]]=False
    return out
Y=lambda t:t[:4]+'Q'+str((int(t[5:7])-1)//3+1)
q=sorted({Y(r['t']) for r in races});rows=[];ths=[]
for qq in [x for x in q if x>='2025Q1']:
    tr=[r for r in races if Y(r['t'])<qq];te=[r for r in races if Y(r['t'])==qq]
    if len(tr)<200 or not te: continue
    th=minimize_scalar(lambda th:-sum(ll(r,th).sum() for r in tr),bounds=(0.5,4),method='bounded').x
    d=np.array([ll(r,th)-ll(r,1.0) for r in te]);rows+= [(r['t'],x) for r,x in zip(te,d)];ths.append((qq,round(th,2),len(te),round(float(d[:,0].mean()),4),round(float(d.sum(1).mean()),4)))
    print(qq,'θ=%.2f'%th,'test koşu',len(te),'kazanan %+.4f ilk5 %+.4f'%(d[:,0].mean(),d.sum(1).mean()),flush=True)
gun=np.array([r[0] for r in rows]);D5=np.array([r[1] for r in rows]);ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};rng=np.random.default_rng(2)
print('TOPLAM ekür koşu',len(D5))
for nm,ix in [('kazanan',[0]),('ikili',[0,1]),('üçlü',[0,1,2]),('ilk4',[0,1,2,3]),('ilk5',[0,1,2,3,4])]:
    x=D5[:,ix].sum(1);bs=[x[np.concatenate([gi[ug[i]] for i in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(2000)]
    print(f'  {nm:8s} {x.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]')
th_all=minimize_scalar(lambda th:-sum(ll(r,th).sum() for r in races),bounds=(0.5,4),method='bounded').x;print('tüm veri θ (betimleyici) %.2f'%th_all)
