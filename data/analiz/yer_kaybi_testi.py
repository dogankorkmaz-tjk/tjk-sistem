"""Yer kaybı ilk bakış (ön kayıt 15 Ekim 2026 03:50). Kullanım: python3 -I yer_kaybi_testi.py <oos_p.pkl klasörü>"""
import sys,glob,json,os,re,unicodedata,numpy as np,pandas as pd
from scipy.optimize import minimize
R='/home/claude/tjk-sistem/';S=sys.argv[1]
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hip']=P.hipodrom.map(asc)
K=['tarih','hip','kosu']
# Accurace: koşu başına fm; o koşudaki piyasa sırasına göre "kötü bitiş"
A=[]
for f in glob.glob(R+'data/accurace/*.json'):
    m=re.match(r'(\d{4}-\d\d-\d\d)_(.+)_(\d+)$',os.path.basename(f)[:-5]);d=json.load(open(f))
    r=[(int(a['no']),a.get('kosulan_mesafe')) for a in d.get('atlar',[]) if a.get('no') is not None and a.get('kosulan_mesafe')]
    if len(r)<4: continue
    med=float(np.median([x[1] for x in r]))
    A+=[{'tarih':m.group(1),'hip':m.group(2),'kosu':int(m.group(3)),'no':n,'fm':km-med} for n,km in r]
A=pd.DataFrame(A);A=A[A.fm.abs()<80]  # açık OCR hatalarını at
T=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/temiz/*.csv.gz')]);T['hip']=T.hipodrom.map(asc);T['tarih']=T.tarih.astype(str)
T=T[T.sira.notna()&(T.sira>0)].copy();T['prk']=T.groupby(K).p_piyasa.rank(ascending=False,method='first')
A=A.merge(T[K+['no','at','sira','prk']],on=K+['no'],how='inner');A['kotu']=(A.sira>A.prk).astype(float)
A['td']=pd.to_datetime(A.tarih);A=A.sort_values('td')
print('Accurace satırı (eşleşen)',len(A),'koşu',A.groupby(K).ngroups)
# hedef koşular: P + at adı; her at için en son ÖNCEKİ Accurace kaydı (<=120 gün)
P=P.merge(T[K+['no','at']],on=K+['no'],how='left');P['td']=pd.to_datetime(P.tarih)
P=P[P.td>=A.td.min()].sort_values('td')
L=pd.merge_asof(P.reset_index(),A[['at','td','fm','kotu']].rename(columns={'td':'tdA'}),left_on='td',right_on='tdA',by='at',direction='backward',allow_exact_matches=False).set_index('index')
L=L[(L.td-L.tdA).dt.days.fillna(9e9)<=120].reindex(P.index)
P['f_yk']=(L.fm/10).fillna(0);P['f_maz']=(L.fm*L.kotu/10).fillna(0);P['var']=L.fm.notna()
P=P[P.groupby(K)['var'].transform('any')&(P.groupby(K).kazandi.transform('sum')==1)].copy()
P['rid']=P.groupby(K).ngroup();print('sınama koşusu',P.rid.nunique(),'| özelliği olan at oranı',round(P['var'].mean(),3),'| tarih',P.tarih.min(),'→',P.tarih.max())
def ll(b,x,ret=False):
    s=np.log(x.p_Jason.values)+b[0]*x.f_yk.values+b[1]*x.f_maz.values
    s=s-pd.Series(s).groupby(x.rid.values).transform('max').values;e=np.exp(s);p=e/pd.Series(e).groupby(x.rid.values).transform('sum').values
    return p if ret else -np.log(p[x.kazandi.values==1]).sum()
gun=sorted(P.tarih.unique());yar=gun[len(gun)//2];tr=P[P.tarih<yar];te=P[P.tarih>=yar].copy()
b=minimize(lambda b:ll(b,tr),[0,0],method='Nelder-Mead').x;print('ilk yarı fit b1,b2 =',np.round(b,3),'| ilk yarı koşu',tr.rid.nunique(),'ikinci yarı',te.rid.nunique())
te['p_yk']=ll(b,te,True);te['pj']=te.p_Jason/te.groupby('rid').p_Jason.transform('sum')
w=te[te.kazandi==1];x=np.log(w.p_yk)-np.log(w.pj);g=(w.tarih+w.hip).values
s=pd.DataFrame({'x':x.values,'g':g}).groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(31);o=[]
for _ in range(3000):
    t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
print(f'BİRİNCİL ikinci yarı kazanç: {x.mean():+.4f} nats/koşu GA [{np.percentile(o,2.5):+.4f},{np.percentile(o,97.5):+.4f}]')
bt=minimize(lambda b:ll(b,P),[0,0],method='Nelder-Mead').x;l0=ll([0,0],P);l1=ll(bt,P)
print('bilgi (tüm örnek, iç-örnek): b =',np.round(bt,3),'LR =',round(2*(l0-l1),2),'(2 sd, %5 eşik 5,99)')
