"""Eşikli kapsama kuponu (ön kayıt 15 Ekim 2026 00:25). Kullanım: python3 -I esikli_kupon.py <scratch>"""
import sys,glob,numpy as np,pandas as pd
from statistics import NormalDist
R='/home/claude/tjk-sistem/';S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str);K=['tarih','hipodrom','kosu']
G={k:(g.no.values,g.p_Jason.values/g.p_Jason.sum()) for k,g in P.groupby(K)}
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')])
TUR={"5'Lİ GANYAN":5,"6'LI GANYAN":6,"7'Lİ GANYAN":7}
rows=[]
for ad,L in TUR.items():
    o=O[O.tur.str.startswith(ad)].drop_duplicates(['tarih','hipodrom','kosu'])
    for r in o.itertuples():
        legs=[G.get((r.tarih,r.hipodrom,k)) for k in range(r.kosu-L+1,r.kosu+1)]
        if any(x is None for x in legs): continue
        devir='DEVİR' in r.tur
        win=None if devir else [set(int(x) for x in s.split(',') if x.strip().isdigit()) for s in str(r.kombo).split('/')]
        if not devir and len(win)!=L: continue
        for T in (0.60,0.75,0.90):
            sets=[];ph=1.0
            for nos,p in legs:
                o_=np.argsort(-p);c=0;s=[]
                for i in o_:
                    s.append(i);c+=p[i]
                    if c>=T or len(s)>=8: break
                sets.append(s);ph*=c
            cost=float(np.prod([len(s) for s in sets]))
            hit=(not devir) and all(any(legs[j][0][i] in win[j] for i in sets[j]) for j in range(L))
            rows.append((ad,T,r.tarih,r.hipodrom,r.kosu,cost,hit,float(r.tutar) if hit else 0.0,ph))
D=pd.DataFrame(rows,columns=['tur','T','t','h','k','cost','hit','pay','ph']);D.to_csv(S+'/esikli.csv',index=False)
z=NormalDist().inv_cdf(1-0.05/(2*9));q=100*NormalDist().cdf(-z)
for (ad,T),x in D.groupby(['tur','T']):
    x=x.assign(g=x.t+x.h);s=x.groupby('g')[['pay','cost']].sum();rng=np.random.default_rng(4);bs=[]
    for _ in range(3000):
        u=s.iloc[rng.integers(0,len(s),len(s))].sum();bs.append(u.pay/u.cost)
    top=x.pay.nlargest(3).sum()
    print(f"{ad} T={T:.2f}: kupon {len(x)} tutan {int(x.hit.sum())} (%{x.hit.mean()*100:.1f}, model %{x.ph.mean()*100:.1f}) ort.maliyet {x.cost.mean():.0f} medyan {x.cost.median():.0f} ROI {x.pay.sum()/x.cost.sum():.2f} GA95 [{np.percentile(bs,2.5):.2f},{np.percentile(bs,97.5):.2f}] Bonf [{np.percentile(bs,q):.2f},{np.percentile(bs,100-q):.2f}] büyük3 hariç {(x.pay.sum()-top)/x.cost.sum():.2f}")
