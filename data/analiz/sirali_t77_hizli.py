"""T77/T78 hızlı analiz (t77.csv'den; gün toplamlarıyla vektörel bootstrap)."""
import numpy as np,pandas as pd
from scipy.stats import poisson
d=pd.read_csv('/tmp/claude-0/t77.csv');d['alan']=pd.cut(d.n,[0,8,11,99],labels=['≤8','9–11','≥12']).astype(str);d['favg']=pd.cut(d.fav,[0,.25,.40,1],labels=['<.25','.25–.40','>.40']).astype(str);d['yari']=np.where(d.t<'2026-04','H1','H2')
rng=np.random.default_rng(77)
for B in(48,96,150):
    x=d[d.B==B];gun=np.array(sorted(set(x.t)));gi={g:i for i,g in enumerate(gun)}
    print(f'\n=== B={B}: koşu {len(x)} tutan {int(x.hit.sum())} ROI {(x.pay.sum()-x.cost.sum())/x.cost.sum():+.1%} beklenen tutan {x.pr.sum():.1f}')
    for kol in('cins','alan','favg'):
        H=sorted(set(x[kol]));nh=len(H)
        for h in H:
            m=(x[kol]==h).values;s=x[m]
            if len(s)<30:print(f'{kol:5s} {h:10s} n={len(s)} (az)');continue
            G=len(gun);pay1=np.zeros(G);c1=np.zeros(G);pay0=np.zeros(G);c0=np.zeros(G)
            for t,p,c,mm in zip(x.t,x.pay,x.cost,m):
                i=gi[t]
                if mm:pay1[i]+=p;c1[i]+=c
                else:pay0[i]+=p;c0[i]+=c
            bs=[]
            for _ in range(2000):
                w=np.bincount(rng.integers(0,G,G),minlength=G)
                a=(w@pay1-w@c1)/(w@c1) if w@c1>0 else np.nan;b=(w@pay0-w@c0)/(w@c0) if w@c0>0 else np.nan;bs.append(a-b)
            lo,hi=np.nanpercentile(bs,[100*.025/nh,100*(1-.025/nh)])
            r1=(pay1.sum()-c1.sum())/c1.sum();r0=(pay0.sum()-c0.sum())/c0.sum()
            ex=s.pr.sum();ob=int(s.hit.sum())
            yar=' '.join(f"{y}:{(s[s.yari==y].pay.sum()-s[s.yari==y].cost.sum())/s[s.yari==y].cost.sum():+.0%}" for y in('H1','H2') if len(s[s.yari==y]))
            print(f'{kol:5s} {h:10s} n={len(s):4d} tutan {ob:2d} beklenen {ex:5.1f} (Poisson {poisson.ppf(.025,ex):.0f}-{poisson.ppf(.975,ex):.0f}) ROI {r1:+.0%} fark {r1-r0:+.0%} GA[{lo:+.0%},{hi:+.0%}] {yar}')
