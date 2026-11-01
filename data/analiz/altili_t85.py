"""T85. python3 data/analiz/altili_t85.py"""
import unicodedata,random,collections,numpy as np,pandas as pd
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','at','jokey']];J['tarih']=J.tarih.astype(str)
for D in(P,J):D['hipodrom']=D.hipodrom.map(asc)
P=P.merge(J.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left').dropna(subset=['at','p_piyasa','p_Jason'])
P['sr']=pd.to_numeric(P.sira,errors='coerce');P=P[P.sr>0].copy()
g=P.groupby(['tarih','hipodrom','kosu'])
P['pm']=P.p_piyasa/g.p_piyasa.transform('sum');P['pj']=P.p_Jason/g.p_Jason.transform('sum')
def h3(p):
    n=len(p);q=np.zeros(n)
    for i in range(n):
        o=np.delete(p,i);s=1-p
        # P(i 3.) = Σ_{j≠k} p_j p_k/(1-p_j) * p_i/(1-p_j-p_k)
        for a in range(n-1):
            for b in range(n-1):
                if a!=b:q[i]+=o[a]*o[b]/(1-o[a])*p[i]/(1-o[a]-o[b])
    return q
P=P.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
P['h3m']=0.0;P['h3j']=0.0
for k,ix in P.groupby(['tarih','hipodrom','kosu']).indices.items():
    if len(ix)>16:continue
    P.loc[ix,'h3m']=h3(P.pm.values[ix]);P.loc[ix,'h3j']=h3(P.pj.values[ix])
P['kz']=(P.sr==1).astype(float);P['u3']=(P.sr==3).astype(float)
P=P.sort_values(['at','tarih','kosu']).reset_index(drop=True);h=P.groupby('at')
P['s1']=h.sr.shift(1);P['s2']=h.sr.shift(2);P['s3']=h.sr.shift(3)
P['onc_kz']=h.kz.cumsum()-P.kz   # önceki toplam galibiyet
P['n_once']=h.cumcount()
A=((P.s1==3).astype(int)+(P.s2==3).astype(int)+(P.s3==3).astype(int)>=2)&(P.n_once>=3)
Bm=(P.s1==1)&(P.onc_kz==1)
# c: jokey
P=P.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
nr=P.groupby(['tarih','hipodrom','jokey']).kosu.transform('size')
jt=collections.defaultdict(list)  # jokey -> [(tarih, hipodrom, kz)]
C=np.zeros(len(P),bool)
P['dt']=pd.to_datetime(P.tarih)
R=P.groupby('jokey')
for jk,gj in R:
    gj=gj.sort_values('dt');dts=gj.dt.values;hp=gj.hipodrom.values;kz=gj.kz.values;idx=gj.index.values
    for r in range(len(gj)):
        if nr.values[idx[r]]!=1:continue
        m30=(dts<dts[r])&(dts>=dts[r]-np.timedelta64(30,'D'))
        if m30.sum()<5:continue
        top=collections.Counter(hp[m30]).most_common(1)[0][0]
        m365=(dts<dts[r])&(dts>=dts[r]-np.timedelta64(365,'D'))
        if top!=hp[r] and m365.sum()>=100:C[idx[r]]=True;P.loc[idx[r],'jw']=kz[m365].mean()
if 'jw' in P:
    thr=P.loc[C,'jw'].quantile(0.0) if False else None
    ranks=P.loc[C].groupby('tarih').jw.transform(lambda s:s)
    # jokey sıralaması: tüm jokeylerin 365-gün kazanma oranının ilk 10'u -> yaklaşık: jw ≥ 0,17
    C=C&(P.jw.fillna(0)>=0.17).values
random.seed(85);gun=sorted(set(P.tarih));ix={t:np.where(P.tarih.values==t)[0] for t in gun}
def rapor(ad,m,y,e):
    a=y-e;bs=[]
    for _ in range(600):
        s=np.concatenate([ix[random.choice(gun)] for _ in gun]);q=m[s]
        if q.sum():bs.append(a[s][q].mean())
    lo,hi=np.percentile(bs,[0.625,99.375]);print(f'{ad:30s} n={int(m.sum()):5d} gerçek {y[m].mean():.4f} beklenen {e[m].mean():.4f} fark {a[m].mean():+.4f} GA98,75 [{lo:+.4f},{hi:+.4f}] ({"SAĞLANDI" if lo>0 else "sağlanmadı"})',flush=True)
a_=A.values;b_=Bm.values
rapor('a 3.lük kalıcı / piyasa P3',a_,P.u3.values,P.h3m.values);rapor('a 3.lük kalıcı / model P3',a_,P.u3.values,P.h3j.values)
rapor('a kazanma / model',a_,P.kz.values,P.pj.values)
rapor('b ilk galibiyetten sonra / model',b_,P.kz.values,P.pj.values);rapor('b ... / piyasa',b_,P.kz.values,P.pm.values)
rapor('c uzaktan tek ata üst jokey / model',C,P.kz.values,P.pj.values);rapor('c ... / piyasa',C,P.kz.values,P.pm.values)
