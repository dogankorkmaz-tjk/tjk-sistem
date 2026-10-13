"""Islak pist özelliği testi (13 Ekim 2026). Kron sayfalarından kum pist durumu (Normal/Nemli/Sulu/Islak); özellik: atın ÖNCEKİ günlerdeki
ıslak-gün koşularında piyasa beklentisine göre bitiş artığının ortalaması (K=2 ağırlık önsel), yalnız bugün ıslaksa. Sınama: Jason olasılığına
tek parametreli ek terim (β), ıslak günlerde log-olabilirlik kazancı ve LR testi. Kum pistli koşular."""
import re,glob,sys,numpy as np,pandas as pd
from math import erf,sqrt
R='/home/claude/tjk-sistem/'; S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl')
rows=[]
for f in sorted(glob.glob(R+'data/tjk_kron/*.html')):
    t=open(f,encoding='utf-8',errors='replace').read()
    m=re.search(r"Kum Pist:\s*([^<]*?)\s*Çim Pist:",t)
    b=f.split('/')[-1][:-5]; rows.append((b[:10],b[11:],m.group(1).strip() if m else ''))
W=pd.DataFrame(rows,columns=['tarih','hipodrom','kum']);W['islak']=W.kum.isin(['Nemli','Sulu','Islak'])
T=pd.concat([pd.read_csv(f,low_memory=False) for f in sorted(glob.glob(R+'data/temiz/*.csv.gz'))])[['tarih','hipodrom','kosu','no','at','sira']]
d=P.merge(T,on=['tarih','hipodrom','kosu','no'],how='left').merge(W,on=['tarih','hipodrom'],how='left')
d['n']=d.groupby(['tarih','hipodrom','kosu']).no.transform('size')
rk=d.groupby(['tarih','hipodrom','kosu']).p_piyasa.rank(ascending=False,method='first')
d['res']=(((rk-1)/(d.n-1).clip(lower=1))-(d.sira-1)/(d.n-1).clip(lower=1)).clip(-1,1)
# özellik: at bazında önceki ıslak-gün koşuları
d=d.sort_values(['at','tarih']).reset_index(drop=True)
f=np.zeros(len(d))
for at,ix in d.groupby('at').indices.items():
    if len(ix)<2: continue
    s=0.0;c=0;last=None
    for j in ix:
        if d.islak[j] is True or d.islak[j]==True: f[j]=s/(c+2.0)
        if d.islak[j]==True and not np.isnan(d.res[j]) : pass
    # günlük sızıntı olmasın: aynı günün koşusu sonradan eklenir (ardışık satırlar aynı tarihte at yok)
    s=0.0;c=0
    for j in ix:
        if d.islak[j]==True: f[j]=s/(c+2.0)
        if d.islak[j]==True and not np.isnan(d.res[j]): s+=d.res[j];c+=1
d['f']=f
w=d[(d.islak==True)&(d.tarih>='2026-02-01')].copy()
w=w.dropna(subset=['sira'])
print('ıslak-gün koşu',w.groupby(['tarih','hipodrom','kosu']).ngroups,'| f≠0 at oranı %.2f'%(w.f!=0).mean())
from scipy.optimize import minimize_scalar
def ll(b):
    s=np.log(w.p_Jason.clip(lower=1e-9))+b*w.f
    k=w.groupby(['tarih','hipodrom','kosu']).ngroup().values
    m=pd.Series(s).groupby(k).transform('max').values;e=np.exp(s-m);Z=pd.Series(e).groupby(k).transform('sum').values
    return float((np.log(e/Z)*(w.kazandi.values==1)).sum())
r=minimize_scalar(lambda b:-ll(b),bounds=(-20,20),method='bounded');b=r.x
n=w.groupby(['tarih','hipodrom','kosu']).ngroup().nunique()
g=ll(b)-ll(0);lr=2*g
print('β=%.2f  kazanç %.4f nats/koşu  LR=%.2f  p≈%.3f'%(b,g/n,lr,1-erf(sqrt(lr/2)) if lr>0 else 1))
