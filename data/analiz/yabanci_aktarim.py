"""Türk modelleri piyasa bileşeni yabancı koşularda (ön kayıt 19 Ekim 2026 11:05). Kullanım: python3 -I yabanci_aktarim.py"""
import glob,os,numpy as np,pandas as pd
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
d=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci/*.csv.gz')])
d=d[d.ganyan.notna()&(d.ganyan>0)&~d.kosmadi.fillna(False).astype(bool)&(d.no>0)].copy();K=['tarih','hipodrom','kosu']
d['p']=1/d.ganyan;g=d.groupby(K).agg(top=('p','sum'),n=('p','size'),kaz=('sira',lambda s:(s==1).sum()))
ok=g[(g.kaz==1)&(g.n>=3)&g.top.between(1.2,1.7)].index;d=d.set_index(K).loc[ok].reset_index();d['rid']=d.groupby(K).ngroup()
d['pm']=d.p/d.groupby('rid').p.transform('sum');d['kaz']=(d.sira==1).astype(int);d['l']=np.log(d.pm.clip(lower=1e-6))
MOD={'Bolton':(0.9506785,0.0),'Jason':(0.7482937,-0.0484677),'Jason-S':(0.4118009,-0.0986594)}
for ad,(w0,l2) in MOD.items():
    s=w0*d.l+l2*d.l**2;s=s-s.groupby(d.rid).transform('max');e=np.exp(s);d['p_'+ad]=e/e.groupby(d.rid).transform('sum')
def boot(gun,v,n,B=3000,seed=3):
    rng=np.random.default_rng(seed);t=pd.DataFrame({'g':gun,'v':v,'n':n}).groupby('g').agg(['sum']);s=t['v']['sum'].values;c=t['n']['sum'].values;o=[]
    for _ in range(B):
        i=rng.integers(0,len(s),len(s));o.append(s[i].sum()/c[i].sum())
    return np.percentile(o,[2.5,97.5])
W=d[d.kaz==1].copy();print('koşu',len(W),d.groupby('ulke').rid.nunique().to_dict())
for ad in MOD:
    W['x']=np.log(W['p_'+ad])-np.log(W.pm)
    for u,g in [('TOPLAM',W)]+list(W.groupby('ulke')):
        if len(g)<100: continue
        lo,hi=boot(g.tarih.values,g.x.values,np.ones(len(g)))
        print(f'{ad:8s} {u:18s} koşu {len(g):5d} kazanç {g.x.mean():+.4f} GA [{lo:+.4f},{hi:+.4f}]')
print('--- EV kuralı (betimleyici): model p x TJK ganyan > k')
for ad in MOD:
    for k in (1.10,1.25):
        B=d[d['p_'+ad]*d.ganyan>k].copy();B['net']=np.where(B.kaz==1,B.ganyan,0.0)
        if len(B)<20: continue
        lo,hi=boot(B.tarih.values,B.net.values,np.ones(len(B)));print(f'{ad:8s} k={k:.2f} bahis {len(B):5d} isabet {int(B.kaz.sum()):4d} ROI {B.net.mean():.3f} GA [{lo:.3f},{hi:.3f}]')
