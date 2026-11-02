import numpy as np,pandas as pd
rng=np.random.default_rng(97)
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl');E['tarih']=E.tarih.astype(str)
D=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left');D['ekur']=D.ekur.fillna(0).astype(int);D=D[D.sira.notna()&D.p_Jason.notna()]
R=[]
for (t,h,k),g in D.groupby(['tarih','hipodrom','kosu']):
    pj=g.p_Jason/g.p_Jason.sum()
    for e,x in g[g.ekur>0].groupby('ekur'):
        if len(x)!=2: continue
        a,b=x.index[0],x.index[1]
        if x.sira.iloc[0]==x.sira.iloc[1]: continue
        sa=pj[a]/(pj[a]+pj[b]); ya=int(x.sira.iloc[0]<x.sira.iloc[1])   # a önde mi
        top=int(x.sira.min()<=5); win=int((x.sira==1).any())
        R.append(dict(t=t,dogru=int((sa>0.5)==bool(ya)),ll=-np.log(sa if ya else 1-sa),ll0=np.log(2),win=win,top5=top,pjc=pj[a]+pj[b]))
R=pd.DataFrame(R)
def ga(v,days,n=3000):
    gl=days.unique();grp={k:v[days==k] for k in gl};s=[]
    for _ in range(n): s.append(np.concatenate([grp[k] for k in rng.choice(gl,len(gl))]).mean())
    return np.percentile(s,[2.5,97.5]).round(3)
o=[f"çift n={len(R)} (günler {R.t.nunique()})"]
o.append(f"(a) doğru partner seçimi {R.dogru.mean():.3f} GA {ga(R.dogru,R.t)} (taban 0.5)")
o.append(f"(b) log-loss Jason {R.ll.mean():.4f} vs 0.5 payı {R.ll0.mean():.4f} fark {(R.ll0-R.ll).mean():+.4f} GA {ga(R.ll0-R.ll,R.t)} (>0 = Jason iyi)")
w=R[R.win==1]; o.append(f"(c) çiftten biri kazandığında n={len(w)} doğru {w.dogru.mean():.3f} GA {ga(w.dogru,w.t)}")
t5=R[R.top5==1]; o.append(f"top5 içinde n={len(t5)} doğru {t5.dogru.mean():.3f} GA {ga(t5.dogru,t5.t)}")
for lo,hi in((0,.1),(.1,.25),(.25,1)):
    s=R[(R.pjc>=lo)&(R.pjc<hi)]
    if len(s)>20: o.append(f"çift Jason toplamı [{lo},{hi}) n={len(s)} doğru {s.dogru.mean():.3f} GA {ga(s.dogru,s.t)}")
open('data/analiz/ekur_cift_t97_sonuc.txt','w').write('\n'.join(o));print('\n'.join(o))
