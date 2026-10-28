"""T34b: sıralı havuzlar ekür çift-içi bölüşümü fiyatlıyor mu? python3 data/analiz/ekur_havuz.py
Her sıralı havuzun kazanan kombinasyonu için L=log(ödeme*H_piyasa(kombo)); ekür atının Jason-bölüşüm payı s
için eğim: L ~ a + b*log(2s). b=-1 tam fiyatlanmış, 0 hiç fiyatlanmamış (ganyan-eşit bölüşümle aynı)."""
import numpy as np,pandas as pd,glob
R='/home/claude/tjk-sistem/'
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl')
D=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left');D['ekur']=D.ekur.fillna(0).astype(int)
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')])
TH=3.7;POOL={'SIRALI İKİLİ':2,'ÜÇLÜ BAHİS':3,'TABELA BAHİS':4,'SIRALI 5 Lİ BAHİS':5}
O=O[O.tur.isin(POOL)];cnt=O.groupby(['tarih','hipodrom','kosu','tur']).size();O=O.join(cnt.rename('n'),on=['tarih','hipodrom','kosu','tur']);O=O[O.n==1]
G={k:g for k,g in D.groupby(['tarih','hipodrom','kosu'])}
rows=[]
for r in O.itertuples():
    g=G.get((r.tarih,r.hipodrom,r.kosu))
    if g is None or g.p_piyasa.isna().any() or g.p_Jason.isna().any(): continue
    try: c=[int(x) for x in str(r.kombo).split('/')]
    except: continue
    k=POOL[r.tur]
    if len(c)!=k or len(set(c))!=k or not set(c)<=set(g.no): continue
    g=g.set_index('no');pm=g.p_piyasa/g.p_piyasa.sum();pj=g.p_Jason/g.p_Jason.sum()
    h=1.0;rem=1.0
    for x in c: h*=pm[x]/rem;rem-=pm[x]
    ls=0.0;ctrl=0.0;ne=0;bad=False
    for x in c:
        e=g.ekur[x]
        if e>0:
            m=g.index[g.ekur==e]
            if len(m)!=2 or (set(m)<=set(c)): bad=True;break
            y=[z for z in m if z!=x][0];s0=pj[x]/(pj[x]+pj[y]);l=np.log(s0/(1-s0));s=1/(1+np.exp(-TH*l));ls+=np.log(2*s);ne+=1
        else: ctrl+=np.log(pj[x]/pm[x])
    if bad or ne==0: continue
    rows.append((r.tarih,r.tur,np.log(r.tutar*h),ls,ctrl))
F=pd.DataFrame(rows,columns=['t','tur','L','ls','ctrl']);print('ekürlü kazanan kombo',len(F),F.groupby('tur').size().to_dict())
rng=np.random.default_rng(1)
def fit(f):
    X=np.c_[np.ones(len(f)),f.ls,f.ctrl];return np.linalg.lstsq(X,f.L.values,rcond=None)[0]
for tur,f in list(F.groupby('tur'))+[('HEPSİ',F)]:
    f=f.reset_index(drop=True);ug=f.t.unique();ix={u:np.where(f.t==u)[0] for u in ug};b=fit(f)[1]
    bs=[fit(f.iloc[np.concatenate([ix[ug[i]] for i in rng.integers(0,len(ug),len(ug))])])[1] for _ in range(1000)]
    print(f'{tur:20s} n={len(f):4d} eğim b={b:+.3f} [{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}]  (0=fiyatlanmamış, -1=tam fiyatlanmış)')
