"""T67: geç yolda ekür piyasa düzeltmesi. python3 data/analiz/ekur_piyasa_t67.py"""
import math,numpy as np,pandas as pd
GAM=np.array([1,0.80,0.67,0.59,0.52]);LP2=-0.0  # lp2 argümanla
import sys,json
lp2=json.load(open('docs/data/gun/2026-11-01.json'))['lp2_aday']
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl');E['tarih']=E.tarih.astype(str)
D=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left');D['ekur']=D.ekur.fillna(0).astype(int);D=D[D.sira.notna()&D.p_Jason.notna()&D.ganyan.notna()&(D.ganyan>0)]
def pl(p,sr):
    o=np.argsort(sr)[:5];m=np.ones(len(p),bool);t=0.0
    for k,i in enumerate(o):
        t+=GAM[k]*math.log(max(p[i]/p[m].sum(),1e-12));m[i]=False
    return t
def run(w0,l2):
    rows=[]
    for (t,hp,ks),g in D.groupby(['tarih','hipodrom','kosu']):
        if len(g)<6 or not all((g.sira==j).sum()==1 for j in range(1,6)): continue
        if not (g.ekur>0).groupby(g.ekur).sum().loc[lambda s:(s.index>0)&(s>=2)].any(): continue
        g=g.reset_index(drop=True);sr=g.sira.values.astype(float);pD=g.p_piyasa.values/g.p_piyasa.sum()
        inv=1/g.ganyan.values;ham=inv/inv.sum();e=inv.copy()
        for k_,h in g[g.ekur>0].groupby('ekur'):
            if len(h)>=2: e[h.index.values]=inv[h.index.values]/len(h)
        ek=e/e.sum();pJ=g.p_Jason.values/g.p_Jason.sum();r=dict(t=t)
        for nm,pp in (('D',pD),('H',ham),('E',ek)):
            lq=np.log(np.maximum(pp,1e-6));lD=np.log(np.maximum(pD,1e-6))
            s=np.log(pJ)+w0*(lq-lD)+l2*(lq**2-lD**2);p=np.exp(s-s.max());p/=p.sum()
            r[nm]=pl(p,sr);r[nm+'_w']=math.log(p[int(np.argmin(sr))])
        rows.append(r)
    return pd.DataFrame(rows)
rng=np.random.default_rng(1)
def ga(d,days):
    gm=d.groupby(days).agg(['sum','count']);bs=[]
    for _ in range(5000):
        s=rng.choice(len(gm),len(gm));bs.append(gm['sum'].values[s].sum()/gm['count'].values[s].sum())
    return np.percentile(bs,[2.5,97.5])
for ad,w0,l2 in (('Jason sabitleri',0.748,lp2),('G1-S ölçeği',0.25,0.0)):
    R=run(w0,l2);print(ad,'ekür koşu',len(R))
    for a,b in (('H','D'),('E','D'),('E','H')):
        for ol,suf in (('ilk5',''),('kazanan','_w')):
            d=R[a+suf]-R[b+suf];lo,hi=ga(d,R.t);print(ad,f'{a}−{b}',ol,'%.4f'%d.mean(),'GA [%.4f,%.4f]'%(lo,hi))
