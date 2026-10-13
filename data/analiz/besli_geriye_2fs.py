"""Ön kayıtlı varyant (hipotez_defteri.md, 14 Ekim 2026 00:50): sıra 1-3 = {F1,F2,S}, sıra 4-5 açgözlü genişleme. Jason p; B=96,150. Karşılaştırma: besli_geriye.csv içindeki Jason kupon_g aynı bütçe.
Kullanım: python3 -I besli_geriye_2fs.py <scratch>"""
import sys,glob,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk import besli
R='/home/claude/tjk-sistem/';S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl')
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O=O[O.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu'])
parse=lambda k:[set(int(x) for x in s.split(',')) for s in str(k).split('/')]
rows=[];n=0
for r in O.itertuples():
    g=P[(P.tarih==r.tarih)&(P.hipodrom==r.hipodrom)&(P.kosu==r.kosu)]
    if len(g)<7: continue          # süpriz için en az 7 at (piyasa sırası>=4 aday olsun ve 5 sıra dolsun)
    g=g.sort_values('no');nos=g.no.tolist();devir=r.tur.endswith('DEVİR');win=None if devir else parse(r.kombo)
    p=g.p_Jason.values.astype(float);p=p/p.sum();pm=g.p_piyasa.values.astype(float)
    t=list(np.argsort(-p));rkm=np.argsort(np.argsort(-pm))
    F1,F2=t[0],t[1];cand=[i for i in range(len(p)) if rkm[i]>=3 and i not in (F1,F2)]
    if not cand: continue
    Sx=max(cand,key=lambda i:p[i]);rest=[i for i in t if i not in (F1,F2,Sx)]
    for B in (96,150):
        st=[[F1,F2,Sx]]*3+[[rest[0]],[rest[1]]]
        st=[list(x) for x in st]
        if besli.gecerli_say(st)>B: continue
        sets,_=besli._acgozlu_g(list(p),B,st)
        cost=besli.gecerli_say(sets)*besli.BIRIM
        hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
        rows.append((r.tarih,r.hipodrom,r.kosu,B,cost,hit,float(r.tutar) if hit else 0.0))
    n+=1
    if n%100==0: print(n,flush=True)
d=pd.DataFrame(rows,columns=['t','h','k','B','cost','hit','pay']);d.to_csv(S+'/besli_geriye_2fs.csv',index=False)
base=pd.read_csv(S+'/besli_geriye.csv');base=base[base.model=='Jason']
for B in (96,150):
    x=d[d.B==B].merge(base[base.B==B][['t','h','k','cost','hit','pay']],on=['t','h','k'],suffixes=('','_b'))
    rng=np.random.default_rng(2);bs=[];bb=[]
    for _ in range(2000):
        s=x.sample(len(x),replace=True,random_state=int(rng.integers(1e9)));bs.append(s.pay.sum()/s.cost.sum());bb.append(s.pay_b.sum()/s.cost_b.sum())
    print(f'B={B} koşu {len(x)} | 2F+S: tutan {int(x.hit.sum())} ({x.hit.mean()*100:.1f}%) maliyet {x.cost.sum():.0f} ödeme {x.pay.sum():.0f} ROI {x.pay.sum()/x.cost.sum():.2f} CI {np.percentile(bs,2.5):.2f}..{np.percentile(bs,97.5):.2f} | mevcut: tutan {int(x.hit_b.sum())} ({x.hit_b.mean()*100:.1f}%) ROI {x.pay_b.sum()/x.cost_b.sum():.2f} CI {np.percentile(bb,2.5):.2f}..{np.percentile(bb,97.5):.2f}')
