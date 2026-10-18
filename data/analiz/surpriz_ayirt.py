"""Sürpriz ayırt etme testi (ön kayıt 19 Ekim 2026 03:20). Kullanım: python3 -I surpriz_ayirt.py <oos_p.pkl klasörü>"""
import sys,numpy as np,pandas as pd
P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str);K=['tarih','hipodrom','kosu']
P=P[P.sira.notna()&(pd.to_numeric(P.sira,errors='coerce')>0)&P.p_Jason.notna()&P.p_piyasa.notna()].copy();P['sira']=pd.to_numeric(P.sira)
P['prk']=P.groupby(K).p_piyasa.rank(ascending=False,method='first');P['ilk5']=(P.sira<=5).astype(int)
O=P[P.prk>=6]
def auc(g,col):
    pos=g[g.ilk5==1][col].values;neg=g[g.ilk5==0][col].values
    if len(pos)==0 or len(neg)==0: return None
    return ((pos[:,None]>neg[None,:]).sum()+0.5*(pos[:,None]==neg[None,:]).sum()),len(pos)*len(neg)
rows=[]
for k,g in O.groupby(K):
    a=auc(g,'p_Jason');b=auc(g,'p_piyasa')
    if a is None: continue
    rows.append((k[0],a[0],b[0],a[1]))
R=pd.DataFrame(rows,columns=['t','aj','ap','n']);print('koşu',len(R),'çift',int(R.n.sum()))
AJ=R.aj.sum()/R.n.sum();AP=R.ap.sum()/R.n.sum();print('AUC Jason',round(AJ,4),'piyasa',round(AP,4),'fark',round(AJ-AP,4))
s=R.groupby('t')[['aj','ap','n']].sum();rng=np.random.default_rng(5);o=[]
for _ in range(3000):
    t=s.iloc[rng.integers(0,len(s),len(s))];o.append((t.aj.sum()-t.ap.sum())/t.n.sum())
print('fark GA',np.percentile(o,[2.5,97.5]).round(4))
