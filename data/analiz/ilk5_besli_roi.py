"""Sıralı 5'li: mevcut (G_M) vs C (sıraya özel üs) vs D (üs + piyasa) ile kurulan kuponların gerçek ödemelerle karşılaştırması.
Yalnız D'nin fit kesiminden SONRA (>=2025-10-19). Kullanım: python3 -I ilk5_besli_roi.py <oos_p.pkl> <cikti.csv>"""
import sys,glob,json,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk import besli
R='/home/claude/tjk-sistem/'
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str)
D=np.array(json.load(open(R+'data/analiz/ilk5_katsayilar.json'))['D']);Cexp=[0.977,0.767,0.666,0.575,0.513]
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O=O[O.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu'])
O=O[O.tarih.astype(str)>='2025-10-19']
ctx={'lm':None};orig=besli._W
def W_D(p,G):
    lp=np.log(np.maximum(np.array(p),1e-9));lm=ctx['lm']
    W=[list(np.exp(D[k,0]*lp+D[k,1]*lm)) for k in range(5)];return W,[sum(w) for w in W]
def parse(k):return [set(int(x) for x in s.split(',')) for s in str(k).split('/')]
rows=[];n=0
for r in O.itertuples():
    g=P[(P.tarih==str(r.tarih))&(P.hipodrom==r.hipodrom)&(P.kosu==r.kosu)]
    if len(g)<5: continue
    g=g.sort_values('no');nos=g.no.tolist();devir=r.tur.endswith('DEVİR');win=None if devir else parse(r.kombo)
    p=g.p_Jason.values.astype(float);p=p/p.sum();pm=g.p_piyasa.values.astype(float);pm=pm/pm.sum();ctx['lm']=np.log(np.maximum(pm,1e-9))
    for model in ('Mevcut','C','D'):
        for B in (48,96,150):
            if model=='D': besli._W=W_D;k=besli.kupon_g(list(p),B)
            else:
                besli._W=orig;k=besli.kupon_g(list(p),B,None if model=='Mevcut' else Cexp)
            besli._W=orig
            if not k: continue
            sets=k[0];cost=besli.gecerli_say(sets)*besli.BIRIM
            hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
            rows.append((r.tarih,r.hipodrom,r.kosu,model,B,cost,hit,float(r.tutar) if hit else 0.0))
    n+=1
    if n%50==0:print(n,flush=True)
d=pd.DataFrame(rows,columns=['t','h','k','model','B','cost','hit','pay']);d.to_csv(sys.argv[2],index=False);print('koşu',n)
rng=np.random.default_rng(5)
def boot(x):
    s=x.groupby('t').agg(c=('cost','sum'),p=('pay','sum'));o=[]
    for _ in range(2000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t.p.sum()/t.c.sum())
    return np.percentile(o,[2.5,97.5])
for (m,B),x in d.groupby(['model','B']):
    lo,hi=boot(x);print(f'{m:7s} B={B:3d} koşu {len(x)} tutan {int(x.hit.sum()):3d} ({x.hit.mean()*100:.1f}%) maliyet {x.cost.sum():8.0f} ROI(A) {x.pay.sum()/x.cost.sum():.2f} [{lo:.2f},{hi:.2f}]')
