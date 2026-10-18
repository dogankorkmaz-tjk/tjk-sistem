"""Tempo testi (ön kayıt: hipotez_defteri.md 19 Ekim 2026 02:15). Kullanım: python3 -I tempo_testi.py <oos_p.pkl klasörü>"""
import sys,glob,json,os,re,unicodedata,numpy as np,pandas as pd
from scipy.optimize import minimize
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/';S=sys.argv[1]
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hip']=P.hipodrom.map(asc)
K=['tarih','hip','kosu']
A=[]
for f in glob.glob(R+'data/accurace/*.json'):
    m=re.match(r'(\d{4}-\d\d-\d\d)_(.+)_(\d+)$',os.path.basename(f)[:-5]);d=json.load(open(f))
    r=[(int(a['no']),float(a['hiz_ort']),float(a['hiz_bitis'])) for a in d.get('atlar',[]) if a.get('no') is not None and isinstance(a.get('hiz_ort'),(int,float)) and isinstance(a.get('hiz_bitis'),(int,float)) and 30<=a['hiz_ort']<=60 and 30<=a['hiz_bitis']<=65]
    if len(r)<4: continue
    me=np.median([x[1] for x in r]);mk=np.median([x[2] for x in r])
    A+=[{'tarih':m.group(1),'hip':m.group(2),'kosu':int(m.group(3)),'no':n,'e':he-me,'k':hb-mk} for n,he,hb in r]
A=pd.DataFrame(A);print('Accurace satırı',len(A),'koşu',A.groupby(K).ngroups)
T=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/temiz/*.csv.gz')]);T['hip']=T.hipodrom.map(asc);T['tarih']=T.tarih.astype(str)
A=A.merge(T[K+['no','at']],on=K+['no'],how='inner');A['td']=pd.to_datetime(A.tarih);A=A.sort_values('td');print('eşleşen',len(A))
P=P.merge(T[K+['no','at']],on=K+['no'],how='left');P['td']=pd.to_datetime(P.tarih);P=P[P.td>=A.td.min()].sort_values('td')
L=pd.merge_asof(P.reset_index(),A[['at','td','k']].rename(columns={'td':'tdA'}),left_on='td',right_on='tdA',by='at',direction='backward',allow_exact_matches=False).set_index('index')
L=L[(L.td-L.tdA).dt.days.fillna(9e9)<=120].reindex(P.index)
P['k']=L.k;P['var']=L.k.notna()
P=P[P.groupby(K)['var'].transform('any')&(P.groupby(K).kazandi.transform('sum')==1)].copy();P['rid']=P.groupby(K).ngroup();P['f_k']=P.k.fillna(0)
def ll(b,x,ret=False):
    s=np.log(x.p_Jason.values)+b*x.f_k.values
    s=s-pd.Series(s).groupby(x.rid.values).transform('max').values;e=np.exp(s);p=e/pd.Series(e).groupby(x.rid.values).transform('sum').values
    return p if ret else -np.log(p[x.kazandi.values==1]).sum()
yeni=P[P.td>='2026-06-01'];eski=P[P.td<'2026-06-01'].copy()
b=minimize(lambda b:ll(b[0],yeni),[0.0],method='Nelder-Mead').x[0];print('b (2026-06+, dondurulmuş)=',round(b,3),'| fit koşu',yeni.rid.nunique())
print('SINAMA koşu',eski.rid.nunique(),'| özelliği olan at oranı',round(eski['var'].mean(),3),'| tarih',eski.tarih.min(),'→',eski.tarih.max())
eski['p_t']=ll(b,eski,True);eski['pj']=eski.p_Jason/eski.groupby('rid').p_Jason.transform('sum')
w=eski[eski.kazandi==1];x=np.log(w.p_t)-np.log(w.pj);g=w.tarih.values
s=pd.DataFrame({'x':x.values,'g':g}).groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(31);o=[]
for _ in range(3000):
    t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
print(f'BAĞIMSIZ SINAV kazanç: {x.mean():+.4f} nats/koşu GA [{np.percentile(o,2.5):+.4f},{np.percentile(o,97.5):+.4f}] | gün sayısı',len(s))
