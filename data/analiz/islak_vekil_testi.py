"""Islak pist vekili testi (13 Ekim 2026; ön kayıt: hipotez_defteri.md). Vekil: hipodrom/gün 3 günlük yağış toplamı >= eşik (eşik 2026 etiketli günlerde Youden ile seçilir).
Özellik: atın ÖNCEKİ vekil-ıslak-gün kum koşularındaki piyasa-artığı ortalaması (K=2). Sınama: Jason log-olasılığına tek β, vekil-ıslak kum günlerinde LR, OOS 2025-01 sonrası."""
import sys,glob,re,numpy as np,pandas as pd
from math import erf,sqrt
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk import mesafe
R='/home/claude/tjk-sistem/';S=sys.argv[1]
H=pd.read_csv(R+'data/hava/gunluk.csv');H['tarih']=H.tarih.astype(str);H=H.sort_values(['hipodrom','tarih'])
H['p3']=H.groupby('hipodrom').yagis_mm.transform(lambda s:s.rolling(3,min_periods=1).sum())
rows=[]
for f in glob.glob(R+'data/tjk_kron/*.html'):
    t=open(f,encoding='utf-8',errors='replace').read();m=re.search(r"Kum Pist:\s*([^<]*?)\s*Çim Pist:",t);b=f.split('/')[-1][:-5]
    if m and m.group(1).strip(): rows.append((b[:10],b[11:],m.group(1).strip() in('Nemli','Sulu','Islak')))
W=pd.DataFrame(rows,columns=['tarih','hipodrom','y']).merge(H,on=['tarih','hipodrom'])
best=max(((W[(W.p3>=e)].y.sum()/W.y.sum())-(W[(W.p3>=e)&(~W.y)].shape[0]/(~W.y).sum()),e) for e in np.arange(0.5,20,0.5))
thr=best[1];print('eşik',thr,'Youden %.2f'%best[0],'| 2026 etiketli gün',len(W))
H['islak']=H.p3>=thr
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','at','sira','p_piyasa']) for f in sorted(glob.glob(R+'data/temiz/*.csv.gz'))])
M=mesafe.tablo()[['tarih','hipodrom','kosu','pist']]
T=T.merge(M,on=['tarih','hipodrom','kosu'],how='left').merge(H[['tarih','hipodrom','islak']],on=['tarih','hipodrom'],how='left')
T=T[(T.pist=='Kum')&(T.islak==True)].copy()
T['n']=T.groupby(['tarih','hipodrom','kosu']).no.transform('size')
rk=T.groupby(['tarih','hipodrom','kosu']).p_piyasa.rank(ascending=False,method='first')
T['res']=(((rk-1)/(T.n-1).clip(lower=1))-(T.sira-1)/(T.n-1).clip(lower=1)).clip(-1,1)
T=T.sort_values(['at','tarih']).reset_index(drop=True)
f=np.zeros(len(T))
for at,ix in T.groupby('at').indices.items():
    s=0.0;c=0;i=0;tt=T.tarih.values
    while i<len(ix):
        j=i
        while j<len(ix) and tt[ix[j]]==tt[ix[i]]: j+=1
        for q in ix[i:j]: f[q]=s/(c+2.0)
        for q in ix[i:j]:
            if not np.isnan(T.res.values[q]): s+=T.res.values[q];c+=1
        i=j
T['f']=f
P=pd.read_pickle(S+'/oos_p.pkl')
w=P.merge(T[['tarih','hipodrom','kosu','no','f']],on=['tarih','hipodrom','kosu','no'],how='inner').dropna(subset=['p_Jason'])
k=w.groupby(['tarih','hipodrom','kosu']).ngroup().values;nr=len(set(k))
print('vekil-ıslak kum koşu (OOS)',nr,'| f≠0 at oranı %.2f'%(w.f!=0).mean())
from scipy.optimize import minimize_scalar
def ll(b):
    s=np.log(w.p_Jason.clip(lower=1e-9)).values+b*w.f.values
    m=pd.Series(s).groupby(k).transform('max').values;e=np.exp(s-m);Z=pd.Series(e).groupby(k).transform('sum').values
    return float((np.log(e/Z)*(w.kazandi.values==1)).sum())
b=minimize_scalar(lambda x:-ll(x),bounds=(-20,20),method='bounded').x;g=ll(b)-ll(0);lr=2*g
print('β=%.2f kazanç %.4f nats/koşu LR=%.2f p≈%.3f'%(b,g/nr,lr,1-erf(sqrt(lr/2)) if lr>0 else 1))
