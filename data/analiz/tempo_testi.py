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
P=P.merge(T[K+['no','at']],on=K+['no'],how='left');P['td']=pd.to_datetime(P.tarih);P=P[P.td>='2026-06-01'].sort_values('td')
L=pd.merge_asof(P.reset_index(),A[['at','td','e','k']].rename(columns={'td':'tdA'}),left_on='td',right_on='tdA',by='at',direction='backward',allow_exact_matches=False).set_index('index')
L=L[(L.td-L.tdA).dt.days.fillna(9e9)<=120].reindex(P.index)
P['e']=L.e;P['k']=L.k;P['var']=L.e.notna()
P=P[P.groupby(K)['var'].transform('any')&(P.groupby(K).kazandi.transform('sum')==1)].copy()
P['rid']=P.groupby(K).ngroup()
def Z(g):
    e=g.e.dropna().sort_values(ascending=False)
    return pd.Series(e.iloc[:3].mean() if len(e)>=4 else 0.0,index=g.index)   # rakip sayısı >=3 (kendisi dahil >=4 veri)
P['Z']=P.groupby('rid',group_keys=False).apply(Z)
P['f_e']=P.e.fillna(0);P['f_k']=P.k.fillna(0);P['f_int']=(P.k*P.Z).fillna(0)
print('sınama koşusu',P.rid.nunique(),'| özelliği olan at oranı',round(P['var'].mean(),3),'| tarih',P.tarih.min(),'→',P.tarih.max(),'| Z>0 koşu oranı',round((P.groupby('rid').Z.first()>0).mean(),3))
F=['f_e','f_k','f_int']
def ll(b,x,ret=False):
    s=np.log(x.p_Jason.values)+x[F].values@np.asarray(b)
    s=s-pd.Series(s).groupby(x.rid.values).transform('max').values;e=np.exp(s);p=e/pd.Series(e).groupby(x.rid.values).transform('sum').values
    return p if ret else -np.log(p[x.kazandi.values==1]).sum()
gun=sorted(P.tarih.unique());yar=gun[len(gun)//2];tr=P[P.tarih<yar];te=P[P.tarih>=yar].copy()
b=minimize(lambda b:ll(b,tr),[0,0,0],method='Nelder-Mead').x;print('ilk yarı fit b =',np.round(b,3),'| ilk yarı koşu',tr.rid.nunique(),'ikinci yarı',te.rid.nunique())
te['p_t']=ll(b,te,True);te['pj']=te.p_Jason/te.groupby('rid').p_Jason.transform('sum')
w=te[te.kazandi==1];x=np.log(w.p_t)-np.log(w.pj);g=(w.tarih).values
s=pd.DataFrame({'x':x.values,'g':g}).groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(31);o=[]
for _ in range(3000):
    t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
print(f'BİRİNCİL ikinci yarı kazanç: {x.mean():+.4f} nats/koşu GA [{np.percentile(o,2.5):+.4f},{np.percentile(o,97.5):+.4f}]')
bt=minimize(lambda b:ll(b,P),[0,0,0],method='Nelder-Mead').x;l0=ll([0,0,0],P);l1=ll(bt,P)
print('bilgi (tüm örnek, iç-örnek): b =',np.round(bt,3),'LR =',round(2*(l0-l1),2),'(3 sd, %5 eşik 7,81)')
# KEŞİF (sonuç görüldükten sonra eklendi, kanıt sayılmaz): tempo etkileşimi gerçekten bir şey ekliyor mu, yoksa kazanç atın kendi bitiş hızından mı?
F=['f_e','f_k'];b2=minimize(lambda b:ll(b,P),[0,0],method='Nelder-Mead').x;l2=ll(b2,P)
print('f_int olmadan: b =',np.round(b2,3),'LR(f_e,f_k) =',round(2*(l0-l2),2),'| f_int katkısı LR =',round(2*(l2-l1),2),'(1 sd, %5 eşik 3,84)')
