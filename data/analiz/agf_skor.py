"""Faz 1 (ön kayıt 15 Ekim 2026 00:00): AGF'nin olasılık olarak skoru. Kullanım: python3 -I agf_skor.py <scratch_with_oos_p.pkl>"""
import sys,glob,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/';S=sys.argv[1]
P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
Z=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(R+'data/zengin/*.csv.gz'))])[['tarih','hipodrom','kosu','no','agf_son']]
d=P.merge(Z,on=['tarih','hipodrom','kosu','no'],how='left')
K=['tarih','hipodrom','kosu']
ok=d.groupby(K).agf_son.transform(lambda s:s.notna().all()&(s.sum()>50))
d=d[ok].copy()
d['a']=d.agf_son.clip(lower=0.01);d['a']=d.a/d.groupby(K).a.transform('sum')
for c in ['p_piyasa','p_Jason','p_Bolton']: d[c]=d[c]/d.groupby(K)[c].transform('sum')
w=d[d.kazandi==1].copy()
w=w[w.groupby(K).no.transform('size')==1]
for c,n in [('a','AGF'),('p_piyasa','piyasa'),('p_Jason','Jason'),('p_Bolton','Bolton')]: w['l_'+n]=np.log(w[c])
w['yil']=w.tarih.str[:4]
def boot(x,g,B=2000,seed=1):
    df=pd.DataFrame({'x':x.values,'g':g.values});s=df.groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(seed);gs=s.index.values;out=[]
    for _ in range(B):
        i=rng.integers(0,len(gs),len(gs));t=s.iloc[i];out.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(out,[2.5,97.5])
w['gun']=w.tarih+w.hipodrom
print('koşu',len(w),'dönemler',w.tarih.min(),w.tarih.max())
for a,b in [('Jason','AGF'),('piyasa','AGF'),('Jason','piyasa'),('Bolton','AGF')]:
    x=w['l_'+a]-w['l_'+b];lo,hi=boot(x,w.gun)
    per={y:round(x[w.yil==y].mean(),4) for y in sorted(w.yil.unique())}
    print(f'{a}-{b}: {x.mean():+.4f} nats/koşu GA [{lo:+.4f},{hi:+.4f}]  yıl:{per}')
# karışım: halkın AGF'si ile piyasa farkı nerede? oran dilimi
d['r']=d.p_piyasa/d.a
d['dilim']=pd.cut(d.p_piyasa,[0,.03,.07,.15,.3,1])
t=d.groupby('dilim',observed=True).agg(n=('kazandi','size'),kaz=('kazandi','mean'),piy=('p_piyasa','mean'),agf=('a','mean'),jas=('p_Jason','mean'))
print(t.round(4).to_string())
w.to_pickle(S+'/agf_w.pkl');d.to_pickle(S+'/agf_d.pkl')
