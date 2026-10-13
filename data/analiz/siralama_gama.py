"""Pozisyona özgü üslü Plackett-Luce (Harville'in γ=1 hali). Kullanım: python3 -I siralama_gama.py <scratch>"""
import sys,glob,numpy as np,pandas as pd
from scipy.optimize import minimize_scalar
R='/home/claude/tjk-sistem/';S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl')
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','sira']) for f in sorted(glob.glob(R+'data/temiz/*.csv.gz'))])
d=P.merge(T,on=['tarih','hipodrom','kosu','no'],how='inner').dropna(subset=['sira'])
races=[]
for key,g in d.groupby(['tarih','hipodrom','kosu']):
    g=g[g.sira>0]
    if len(g)<6 or g.sira.duplicated().any(): continue
    g=g.sort_values('sira')
    if list(g.sira.iloc[:5])!=[1,2,3,4,5]: continue
    races.append((key[0],g))
print('koşu',len(races))
def pos_ll(rs,col,k,gam):
    ll=0
    for _,g in rs:
        p=g[col].values.clip(1e-6)**gam  # k. pozisyon: kalanlar arasından sıra k-1 olan seçilir
        rem=p[k-1:]; ll+=np.log(rem[0]/rem.sum())
    return ll
for col in ['p_Jason','p_piyasa']:
    tr=[r for r in races if r[0]<'2026-01-01'];te=[r for r in races if r[0]>='2026-01-01']
    print('==',col,'eğitim',len(tr),'sınama',len(te))
    tot0=tot1=0
    for k in (2,3,4,5):
        f=lambda g:-pos_ll(tr,col,k,g)
        gm=minimize_scalar(f,bounds=(0.3,2.0),method='bounded').x
        a0=pos_ll(te,col,k,1.0);a1=pos_ll(te,col,k,gm)
        # bootstrap: koşu başına fark
        dif=np.array([pos_ll([r],col,k,gm)-pos_ll([r],col,k,1.0) for r in te])
        bs=np.random.default_rng(0).choice(dif,(2000,len(dif))).mean(1)
        print(f'  sıra {k}: γ={gm:.3f} | sınama kazancı {dif.mean():+.4f} nats/koşu (CI {np.percentile(bs,2.5):+.4f}..{np.percentile(bs,97.5):+.4f})')
        tot0+=a0;tot1+=a1
    print('  toplam sıra2-5 kazanç/koşu %.4f'%((tot1-tot0)/len(te)))
print('\n=== Mevcut canlı üsler (besli.py G_M/G_P) ve eğitimde bulunanlarla karşılaştırma (sınama 2026) ===')
GM=[1,0.80,0.69,0.69,0.69];GP=[1,0.87,0.74,0.74,0.74]
for col,G in (('p_Jason',GM),('p_piyasa',GP)):
    tr=[r for r in races if r[0]<'2026-01-01'];te=[r for r in races if r[0]>='2026-01-01']
    gs=[1.0]+[minimize_scalar(lambda g:-pos_ll(tr,col,k,g),bounds=(0.3,2.0),method='bounded').x for k in (2,3,4,5)]
    for k in (2,3,4,5):
        dif=np.array([pos_ll([r],col,k,gs[k-1])-pos_ll([r],col,k,G[k-1]) for r in te]);bs=np.random.default_rng(0).choice(dif,(2000,len(dif))).mean(1)
        print(f'{col} sıra {k}: canlı γ={G[k-1]:.2f} -> yeni γ={gs[k-1]:.3f} | kazanç {dif.mean():+.4f} nats/koşu (CI {np.percentile(bs,2.5):+.4f}..{np.percentile(bs,97.5):+.4f})')
    tot=sum(np.mean([pos_ll([r],col,k,gs[k-1])-pos_ll([r],col,k,G[k-1]) for r in te]) for k in (2,3,4,5));print(f'  toplam {tot:+.4f} nats/koşu')
