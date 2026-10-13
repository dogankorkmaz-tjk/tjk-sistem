"""Sıralı beşli kuponlarını (besli.kupon_g, 48/96/150 geçerli kombinasyon) 2025-01 sonrası OOS olasılıklarla geçmişe uygular; gerçek ödemelerle kazanç ölçer.
Ödeme satırı: tur 'SIRALI 5 Lİ BAHİS' (kazanan var) ya da '... DEVİR' (kazanan yok -> 0). Ödeme birimi belirsiz: A) kombinasyon başına (1,25 TL) B) 1 TL başına (x1,25).
Kullanım: python3 -I besli_geriye_test.py <scratch>"""
import sys,glob,re,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk import besli
R='/home/claude/tjk-sistem/';S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl')
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O=O[O.tur.str.startswith('SIRALI 5')]
O=O.drop_duplicates(['tarih','hipodrom','kosu'])
def parse(k):
    return [set(int(x) for x in s.split(',')) for s in str(k).split('/')]
rows=[];n=0
for r in O.itertuples():
    g=P[(P.tarih==r.tarih)&(P.hipodrom==r.hipodrom)&(P.kosu==r.kosu)]
    if len(g)<5: continue
    g=g.sort_values('no');nos=g.no.tolist();devir=r.tur.endswith('DEVİR')
    win=None if devir else parse(r.kombo)
    for model,col in (('Jason','p_Jason'),('Bolton','p_Bolton'),('Piyasa','p_piyasa')):
        p=g[col].values.astype(float);p=p/p.sum()
        for B in (48,96,150):
            k=besli.kupon_g(list(p),B)
            if not k: continue
            sets=k[0];cost=besli.gecerli_say(sets)*besli.BIRIM
            hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
            rows.append((r.tarih,r.hipodrom,r.kosu,model,B,cost,hit,float(r.tutar) if hit else 0.0,len(g)))
    n+=1
    if n%100==0: print(n,flush=True)
d=pd.DataFrame(rows,columns=['t','h','k','model','B','cost','hit','pay','n'])
d.to_csv(S+'/besli_geriye.csv',index=False)
print('koşu',n)
for (m,B),x in d.groupby(['model','B']):
    bs=[];rng=np.random.default_rng(1)
    for _ in range(2000):
        s=x.sample(len(x),replace=True,random_state=int(rng.integers(1e9)));bs.append(s.pay.sum()/s.cost.sum())
    print(f'{m:7s} B={B:3d} koşu {len(x):4d} tutan {int(x.hit.sum()):3d} ({x.hit.mean()*100:.1f}%) maliyet {x.cost.sum():9.0f} ödeme(A) {x.pay.sum():10.0f} ROI(A) {x.pay.sum()/x.cost.sum():.2f} CI {np.percentile(bs,2.5):.2f}..{np.percentile(bs,97.5):.2f} | ROI(B) {1.25*x.pay.sum()/x.cost.sum():.2f}')
