"""Jason-S kupon geriye testi (ön kayıt 14 Ekim 2026 01:45). Kullanım: python3 -I besli_geriye_s.py <scratch>"""
import sys,glob,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk import besli
R='/home/claude/tjk-sistem/';S=sys.argv[1]
PJ=pd.read_pickle(S+'/oos_p.pkl');PS=pd.read_pickle(S+'/p_S.pkl')
PS['tarih']=PS.tarih.astype(str);PJ['tarih']=PJ.tarih.astype(str)
P=PJ.merge(PS,on=['tarih','hipodrom','kosu','no'],how='inner')
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O=O[O.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu'])
parse=lambda k:[set(int(x) for x in s.split(',')) for s in str(k).split('/')]
GM0=list(besli.G_M)
rows=[];n=0
for r in O.itertuples():
    g=P[(P.tarih==r.tarih)&(P.hipodrom==r.hipodrom)&(P.kosu==r.kosu)]
    if len(g)<5: continue
    g=g.sort_values('no');nos=g.no.tolist();devir=r.tur.endswith('DEVİR');win=None if devir else parse(r.kombo)
    a=[1.0,g.a2.iloc[0],g.a3.iloc[0],g.a4.iloc[0],g.a5.iloc[0]]
    for model,col,G in (('Jason','p_Jason',GM0),('Jason-S','p_S',a)):
        besli.G_M=G
        p=g[col].values.astype(float);p=list(p/p.sum())
        for B in (48,96,150):
            k=besli.kupon_g(p,B)
            if not k: continue
            sets,pr=k;cost=besli.gecerli_say(sets)*besli.BIRIM
            hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
            rows.append((r.tarih,r.hipodrom,r.kosu,model,B,cost,hit,float(r.tutar) if hit else 0.0,pr))
    n+=1
    if n%100==0: print(n,flush=True)
besli.G_M=GM0
d=pd.DataFrame(rows,columns=['t','h','k','model','B','cost','hit','pay','pr']);d.to_csv(S+'/besli_geriye_s.csv',index=False);print('koşu',n)
for B in (48,96,150):
    a=d[(d.model=='Jason')&(d.B==B)];b=d[(d.model=='Jason-S')&(d.B==B)]
    m=a.merge(b,on=['t','h','k'],suffixes=('_J','_S'))
    rng=np.random.default_rng(5);bs=[]
    for _ in range(2000):
        s=m.sample(len(m),replace=True,random_state=int(rng.integers(1e9)));bs.append(s.pay_S.sum()/s.cost_S.sum()-s.pay_J.sum()/s.cost_J.sum())
    print(f'B={B} koşu {len(m)} | Jason: tutan {int(m.hit_J.sum())} ({m.hit_J.mean()*100:.1f}%) model-beklenen %{m.pr_J.mean()*100:.1f} maliyet {m.cost_J.sum():.0f} ROI {m.pay_J.sum()/m.cost_J.sum():.2f} | Jason-S: tutan {int(m.hit_S.sum())} ({m.hit_S.mean()*100:.1f}%) model-beklenen %{m.pr_S.mean()*100:.1f} maliyet {m.cost_S.sum():.0f} ROI {m.pay_S.sum()/m.cost_S.sum():.2f} | ROI farkı {np.mean(bs):+.2f} CI {np.percentile(bs,2.5):+.2f}..{np.percentile(bs,97.5):+.2f}')
