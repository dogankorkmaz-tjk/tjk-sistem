import numpy as np,pandas as pd
D=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_sinif.pkl')
D=D[D.sinif.notna()&D.p_Jason.notna()&D.p_piyasa.notna()&D.sira.notna()]
rows=[]
for (t,h,k),g in D.groupby(['tarih','hipodrom','kosu']):
    if len(g)<5 or g.kazandi.sum()!=1: continue
    pj=g.p_Jason.values/g.p_Jason.sum(); pq=g.p_piyasa.values/g.p_piyasa.sum(); w=np.where(g.kazandi.values==1)[0][0]
    s=g.sira.values.astype(float)
    def t3(p): 
        a=set(np.argsort(-p)[:3]); b=set(np.argsort(s)[:3]); return len(a&b)
    def top1(p): return float(np.argmax(p)==w)
    def sp(p):
        from scipy.stats import spearmanr
        return spearmanr(-p,s)[0]
    rows.append(dict(t=t,sinif=g.sinif.iloc[0],n=len(g),llJ=-np.log(pj[w]),llQ=-np.log(pq[w]),hJ=top1(pj),hQ=top1(pq),t3J=t3(pj),t3Q=t3(pq),spJ=sp(pj),spQ=sp(pq),pmaxQ=pq.max()))
R=pd.DataFrame(rows);R['grup']=R.sinif.isin(['G1','G2','G3'])
rng=np.random.default_rng(1)
def ci(x,col):
    days=x.groupby('t')[col].agg(['sum','count']);v=[]
    for _ in range(2000):
        i=rng.integers(0,len(days),len(days));v.append(days['sum'].values[i].sum()/days['count'].values[i].sum())
    return np.percentile(v,[2.5,97.5])
def tab(G,name):
    d=R[G]; x=d.assign(dll=d.llJ-d.llQ)
    lo,hi=ci(x,'dll')
    print(f"{name:10s} n={len(d):5d} alan={d.n.mean():4.1f} piyasaMaxP={d.pmaxQ.mean():.2f} | ll J={d.llJ.mean():.3f} Q={d.llQ.mean():.3f} fark(J-Q)={x.dll.mean():+.3f} [{lo:+.3f},{hi:+.3f}] | ilk1 J={d.hJ.mean():.3f} Q={d.hQ.mean():.3f} | ilk3∩ J={d.t3J.mean():.2f} Q={d.t3Q.mean():.2f} | spearman J={d.spJ.mean():.3f} Q={d.spQ.mean():.3f}")
for s in ['G1','G2','G3','KV','Handikap','Şartlı','Maiden','Diğer']: tab(R.sinif==s,s)
tab(R.grup,'G1-G3'); tab(~R.grup,'diğer hepsi')
R.to_csv('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/sinif_sonuc.csv',index=False)
