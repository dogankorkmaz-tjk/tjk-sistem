"""T24 değer odaklı kupon. python3 -I butce_t24.py <oos_p.pkl>"""
import sys,glob,itertools,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/'
CEXP=[0.977,0.767,0.666];NS=(12,24,48);LAM=(0.0,0.5,1.0)
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str);P=P[P.tarih>='2025-10-19']
G=dict(list(P.groupby(['tarih','hipodrom','kosu'])))
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O=O[O.tur=='ÜÇLÜ BAHİS'].drop_duplicates(['tarih','hipodrom','kosu'])
O['tarih']=O.tarih.astype(str)
def pl(p,perms):
    W=[p**g for g in CEXP];T=[w.sum() for w in W];out=[]
    for a,b,c in perms:
        d2=T[1]-W[1][a];d3=T[2]-W[2][a]-W[2][b]
        out.append(W[0][a]/T[0]*W[1][b]/d2*W[2][c]/d3 if d2>0 and d3>0 else 0.0)
    return np.array(out)
rows=[]
for r in O.itertuples():
    g=G.get((r.tarih,r.hipodrom,r.kosu))
    if g is None or len(g)<8: continue
    g=g.sort_values('no');nos=g.no.values
    win=[set(int(x) for x in s.split(',')) for s in str(r.kombo).split('/')]
    if len(win)<3: continue
    p=np.maximum(g.p_Jason.values.astype(float),1e-9);p/=p.sum();q=np.maximum(g.p_piyasa.values.astype(float),1e-9);q/=q.sum()
    top=list(np.argsort(-(p+q)))[:8]
    perms=list(itertools.permutations(top,3))
    pp=pl(p,perms);qq=np.maximum(pl(q,perms),1e-9)
    hitv=np.array([all(nos[t] in win[j] for j,t in enumerate(c)) for c in perms])
    for n in NS:
        for lam in LAM+('mkt',):
            sc=qq if lam=='mkt' else pp/qq**lam
            idx=np.argsort(-sc)[:n];h=bool(hitv[idx].any())
            rows.append((r.tarih,n,str(lam),2.0*n,h,float(r.tutar) if h else 0.0))
d=pd.DataFrame(rows,columns=['t','n','lam','cost','hit','pay']);d.to_csv(sys.argv[2] if len(sys.argv)>2 else '/tmp/t24.csv',index=False)
rng=np.random.default_rng(7)
def daily(x):return x.groupby('t').agg(c=('cost','sum'),p=('pay','sum'))
res=[]
for n in NS:
    base=daily(d[(d.n==n)&(d.lam=='0.0')]);days=base.index.values
    for lam in ('0.0','0.5','1.0','mkt'):
        x=d[(d.n==n)&(d.lam==lam)];s=daily(x).reindex(days).fillna(0);roi=s.p.sum()/s.c.sum()
        bs=[];df=[]
        for _ in range(1500):
            ii=rng.integers(0,len(days),len(days));a=s.iloc[ii];b=base.iloc[ii];bs.append(a.p.sum()/a.c.sum());df.append(a.p.sum()/a.c.sum()-b.p.sum()/b.c.sum())
        h=x[x.hit];print(f'n={n:2d} λ={lam:>3s} koşu {len(x)} isabet {x.hit.mean()*100:5.1f}% ROI {roi:.3f} [{np.percentile(bs,2.5):.3f},{np.percentile(bs,97.5):.3f}] fark_vs_λ0 {np.mean(df):+.3f} [{np.percentile(df,2.5):+.3f},{np.percentile(df,97.5):+.3f}] tutunca medyan ödeme/maliyet {np.median(h.pay/h.cost):.2f}')
