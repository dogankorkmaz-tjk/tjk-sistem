"""T37 (hızlı keşif) ıslak kum pistte SOY (baba) etkisi: babanın ÖNCEKİ ıslak-gün (Nemli/Sulu/Islak) yavrularının piyasaya göre bitiş artığı ortalaması (K=10),
yalnız bugün ıslaksa; Jason olasılığına tek parametreli ek terim β. islak_pist_testi.py ile aynı yapı. python3 data/analiz/islak_soy_testi.py <scratchpad>"""
import re,glob,sys,numpy as np,pandas as pd
from math import erf,sqrt
from scipy.optimize import minimize_scalar
R='/home/claude/tjk-sistem/';S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
rows=[]
for f in sorted(glob.glob(R+'data/tjk_kron/*.html')):
    t=open(f,encoding='utf-8',errors='replace').read();m=re.search(r"Kum Pist:\s*([^<]*?)\s*Çim Pist:",t);b=f.split('/')[-1][:-5];rows.append((b[:10],b[11:],m.group(1).strip() if m else ''))
W=pd.DataFrame(rows,columns=['tarih','hipodrom','kum']);W['islak']=W.kum.isin(['Nemli','Sulu','Islak'])
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','baba','pist']];J['tarih']=J.tarih.astype(str)
d=P.merge(J,on=['tarih','hipodrom','kosu','no'],how='left').merge(W,on=['tarih','hipodrom'],how='left')
d=d[d.pist.astype(str)=='Kum'].copy()
d['n']=d.groupby(['tarih','hipodrom','kosu']).no.transform('size')
rk=d.groupby(['tarih','hipodrom','kosu']).p_piyasa.rank(ascending=False,method='first')
d['res']=(((rk-1)/(d.n-1).clip(lower=1))-(d.sira-1)/(d.n-1).clip(lower=1)).clip(-1,1)
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
bs=d.baba.astype(str).values;il=(d.islak==True).values;res=d.res.values;gun=d.tarih.values
Ssum={};Sc={};f=np.zeros(len(d));pend=[];cur=None
for i in range(len(d)):
    if gun[i]!=cur:
        for b,r in pend: Ssum[b]=Ssum.get(b,0)+r;Sc[b]=Sc.get(b,0)+1
        pend=[];cur=gun[i]
    if il[i]:
        f[i]=Ssum.get(bs[i],0)/(Sc.get(bs[i],0)+10.0)
        if np.isfinite(res[i]): pend.append((bs[i],res[i]))
d['f']=f
w=d[il&(d.tarih>='2026-02-01')].dropna(subset=['sira']).copy()
print('ıslak-gün koşu',w.groupby(['tarih','hipodrom','kosu']).ngroups,'| f≠0 at oranı %.2f'%(w.f!=0).mean(),'| f sd %.3f'%w.f[w.f!=0].std())
k=w.groupby(['tarih','hipodrom','kosu']).ngroup().values
def ll(b):
    s=np.log(w.p_Jason.clip(lower=1e-9)).values+b*w.f.values;m=pd.Series(s).groupby(k).transform('max').values;e=np.exp(s-m);Z=pd.Series(e).groupby(k).transform('sum').values
    return float((np.log(e/Z)*(w.kazandi.values==1)).sum())
b=minimize_scalar(lambda x:-ll(x),bounds=(-20,20),method='bounded').x;n=len(set(k));g=ll(b)-ll(0);lr=2*g
print('β=%.2f kazanç %.4f nats/koşu LR=%.2f p≈%.3f'%(b,g/n,lr,1-erf(sqrt(lr/2)) if lr>0 else 1))
