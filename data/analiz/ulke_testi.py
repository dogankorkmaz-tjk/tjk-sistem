"""Ülke ülke yabancı havuz testi (ön kayıt 15 Ekim 2026 01:05). Kullanım: python3 -I ulke_testi.py"""
import glob,numpy as np,pandas as pd
from scipy.optimize import minimize_scalar
R='/home/claude/tjk-sistem/'
d=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci/*.csv.gz')])
d=d[d.ganyan.notna()&(d.ganyan>0)&~d.kosmadi.fillna(False).astype(bool)&(d.no>0)].copy()
K=['tarih','hipodrom','kosu'];d['p']=1/d.ganyan
g=d.groupby(K).agg(top=('p','sum'),n=('p','size'),kaz=('sira',lambda s:(s==1).sum()))
ok=g[(g.kaz==1)&(g.n>=3)&g.top.between(1.2,1.7)].index
d=d.set_index(K).loc[ok].reset_index();d['pn']=d.p/d.groupby(K).p.transform('sum');d['y']=(d.sira==1).astype(int)
d['rid']=d.groupby(K).ngroup()
def nll(b,x):
    s=b*np.log(x.pn.values);e=np.exp(s-pd.Series(s).groupby(x.rid.values).transform('max').values)
    q=e/pd.Series(e).groupby(x.rid.values).transform('sum').values;return -np.log(q[x.y.values==1]).sum()
def fit(x): return minimize_scalar(lambda b:nll(b,x),bounds=(0.2,3),method='bounded').x
def adj(x,b):
    s=b*np.log(x.pn.values);e=np.exp(s-pd.Series(s).groupby(x.rid.values).transform('max').values);return e/pd.Series(e).groupby(x.rid.values).transform('sum').values
print('toplam geçerli koşu',len(ok),d.tarih.min(),'→',d.tarih.max())
rows=[]
for u,x in d.groupby('ulke'):
    nk=x.rid.nunique();gr=x.groupby('rid').p.sum()
    r={'ülke':u,'koşu':nk,'geri_ödeme':round(1/gr.median(),3)}
    if nk<80: r['not']='yetersiz';rows.append(r);continue
    b=fit(x);l0=nll(b,x);grid=np.linspace(0.3,2.5,221);ll=np.array([nll(v,x) for v in grid]);ci=grid[ll<=l0+1.92]
    r.update({'β':round(b,2),'β_GA':f'{ci.min():.2f}–{ci.max():.2f}'})
    gun=sorted(x.tarih.unique());yar=gun[len(gun)//2]
    a=x[x.tarih<yar];c=x[x.tarih>=yar].copy();b1=fit(a);c['q']=adj(c,b1)
    m=c.q*c.ganyan>1.10;z=c[m];ret=z.y*z.ganyan
    if len(z)>=5:
        s=z.assign(r=ret).groupby('tarih').agg(r=('r','sum'),n=('r','size'));rng=np.random.default_rng(2);bs=[]
        for _ in range(3000):
            t=s.iloc[rng.integers(0,len(s),len(s))].sum();bs.append(t.r/t.n)
        r.update({'β_ilk_yarı':round(b1,2),'bahis':int(m.sum()),'ROI':round(ret.mean(),3),'ROI_GA':f'{np.percentile(bs,2.5):.2f}–{np.percentile(bs,97.5):.2f}'})
    else: r.update({'β_ilk_yarı':round(b1,2),'bahis':int(m.sum())})
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))
