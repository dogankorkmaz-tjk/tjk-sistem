"""Faz 1b (ön kayıt 15 Ekim 2026 00:25): Jason^(1-w) * AGF^w. Kullanım: python3 -I agf_karisim.py <scratch>"""
import sys,numpy as np,pandas as pd
from scipy.optimize import minimize_scalar
S=sys.argv[1];d=pd.read_pickle(S+'/agf_d.pkl');K=['tarih','hipodrom','kosu']
d=d[d.groupby(K).kazandi.transform('sum')==1].copy()
# DÜZELTME 15 Eki 00:10: ekürlü koşular çıkarılır (p_ham ekürde bölünür, 1/p_ham ödemeyi şişirir); ödeme = gerçek ganyan
d['ekur']=(abs(d.p_ham*d.ganyan-1)>1e-6);d=d[~d.groupby(K).ekur.transform('any')].copy()
d['rid']=d.groupby(K).ngroup();d['yil']=d.tarih.str[:4]
def karis(g,w):
    s=(1-w)*np.log(g.p_Jason.values)+w*np.log(g.a.values);e=np.exp(s-pd.Series(s).groupby(g.rid.values).transform('max').values)
    return e/pd.Series(e).groupby(g.rid.values).transform('sum').values
def nll(w,g): p=karis(g,w);return -np.log(p[g.kazandi.values==1]).sum()
tr=d[d.yil=='2025'];te=d[d.yil=='2026'].copy()
w=minimize_scalar(lambda x:nll(x,tr),bounds=(0,1),method='bounded').x;print('w (2025 fit) =',round(w,3))
te['p_M']=karis(te,w)
k=te[te.kazandi==1].copy();k['x']=np.log(k.p_M)-np.log(k.p_Jason);k['y']=np.log(k.p_M)-np.log(k.p_piyasa);k['gun']=k.tarih+k.hipodrom
def boot(x,g,B=2000):
    s=pd.DataFrame({'x':x.values,'g':g.values}).groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(3);o=[]
    for _ in range(B):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
print('2026 koşu',len(k));print('Karışım−Jason %+.4f GA %s'%(k.x.mean(),np.round(boot(k.x,k.gun),4)));print('Karışım−piyasa %+.4f GA %s'%(k.y.mean(),np.round(boot(k.y,k.gun),4)))
te['gan']=te.ganyan
for e in (1.1,1.3):
    for c in ('p_Jason','p_M'):
        m=te[c]*te.gan>e;r=te[m].kazandi*te[m].gan
        print(f'EV>{e} {c}: bahis {m.sum()} ROI {r.mean():.3f} ± {r.std()/np.sqrt(m.sum()):.3f}')
