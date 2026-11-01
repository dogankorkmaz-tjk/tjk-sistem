"""T84. python3 data/analiz/takip_t84.py"""
import unicodedata,random,numpy as np,pandas as pd
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','at']];J['tarih']=J.tarih.astype(str)
for D in(P,J):D['hipodrom']=D.hipodrom.map(asc)
P=P.merge(J.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left').dropna(subset=['at','p_piyasa','p_Jason'])
P['sr']=pd.to_numeric(P.sira,errors='coerce');P=P[P.sr>0].copy()
g=P.groupby(['tarih','hipodrom','kosu'])
P['pm']=P.p_piyasa/g.p_piyasa.transform('sum');P['pj']=P.p_Jason/g.p_Jason.transform('sum');P['n']=g.sr.transform('size')
P['mr']=g.pm.rank(ascending=False,method='first');P['kz']=(P.sr==1).astype(float)
P=P.sort_values(['at','tarih','kosu']).reset_index(drop=True)
h=P.groupby('at');P['mr0']=h.mr.shift(1);P['sr0']=h.sr.shift(1);P['n0']=h.n.shift(1);P['t0']=h.tarih.shift(1)
P['gap']=(pd.to_datetime(P.tarih)-pd.to_datetime(P.t0)).dt.days
Q=P[(P.gap<=45)&(P.n0>=7)].copy()
Q['hk']=(Q.mr0<=3)&(Q.sr0>Q.n0/2)       # hayal kırıklığı
Q['ss']=(Q.mr0>Q.n0/2)&(Q.sr0<=3)       # sürpriz iyi (kontrol)
random.seed(84);gun=sorted(set(Q.tarih));ix={t:np.where(Q.tarih.values==t)[0] for t in gun}
print('sonraki koşu satırı',len(Q),'hk',int(Q.hk.sum()),'ss',int(Q.ss.sum()),flush=True)
for ad,m in(('hayal kırıklığı',Q.hk.values),('sürpriz iyi',Q.ss.values)):
    for bn,col in(('piyasa','pm'),('model','pj')):
        a=Q.kz.values-Q[col].values;bs=[]
        for _ in range(600):
            s=np.concatenate([ix[random.choice(gun)] for _ in gun]);q=m[s]
            if q.sum():bs.append(a[s][q].mean())
        lo,hi=np.percentile(bs,[0.625,99.375])
        print(f'{ad:16s} vs {bn:6s} n={int(m.sum()):5d} kazanma {Q.kz.values[m].mean():.4f} beklenen {Q[col].values[m].mean():.4f} fark {a[m].mean():+.4f} GA98,75 [{lo:+.4f},{hi:+.4f}]',flush=True)
