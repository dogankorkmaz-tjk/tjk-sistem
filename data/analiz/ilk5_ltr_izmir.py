"""İlk-5 sıralama ön bakışı, İzmir, walk-forward (zaman bölmesi). KEŞİF. Kullanım: python3 -I ilk5_ltr_izmir.py <oos_p.pkl>"""
import sys,glob,json,os,re,numpy as np,pandas as pd
from scipy.optimize import minimize
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
P=pd.read_pickle(sys.argv[1]);P=P[P.hipodrom=='izmir'].copy();P['tarih']=P.tarih.astype(str)
K=['tarih','kosu']
# Accurace f_k (önceki ≤120 gün, bitiş hızı - koşu medyanı)
A=[]
for f in glob.glob(R+'data/accurace/*_izmir_*.json'):
    m=re.match(r'(\d{4}-\d\d-\d\d)_izmir_(\d+)$',os.path.basename(f)[:-5]);d=json.load(open(f))
    r=[(int(a['no']),float(a['hiz_bitis'])) for a in d.get('atlar',[]) if a.get('no') is not None and isinstance(a.get('hiz_bitis'),(int,float)) and 30<=a['hiz_bitis']<=65]
    if len(r)<4: continue
    mk=np.median([x[1] for x in r]);A+=[{'tarih':m.group(1),'kosu':int(m.group(2)),'no':n,'k':hb-mk} for n,hb in r]
A=pd.DataFrame(A)
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','at']) for f in glob.glob(R+'data/temiz/*.csv.gz')]);T=T[T.hipodrom=='izmir'];T['tarih']=T.tarih.astype(str)
A=A.merge(T[K+['no','at']],on=K+['no']);A['td']=pd.to_datetime(A.tarih);A=A.sort_values('td')
P=P.merge(T[K+['no','at']],on=K+['no'],how='left');P['td']=pd.to_datetime(P.tarih);P=P.sort_values('td')
L=pd.merge_asof(P.reset_index(),A[['at','td','k']].rename(columns={'td':'tdA'}),left_on='td',right_on='tdA',by='at',direction='backward',allow_exact_matches=False).set_index('index')
L=L[(L.td-L.tdA).dt.days.fillna(9e9)<=120].reindex(P.index);P['fk']=L.k.fillna(0.0)
P=P.dropna(subset=['sira','p_Jason','p_piyasa']);P=P[P.p_Jason>0][P.p_piyasa>0]
races=[]
for (t,k),g in P.groupby(K):
    g=g.sort_values('sira')
    if len(g)<6 or g.sira.iloc[:6].nunique()<6 or g.sira.iloc[0]!=1: continue
    x1=np.log(g.p_Jason/g.p_Jason.sum()).values;x2=np.log(g.p_piyasa/g.p_piyasa.sum()).values
    races.append((t,np.vstack([x1,x2,g.fk.values])))   # at sırası = bitiş sırası
races.sort(key=lambda r:r[0]);days=sorted({r[0] for r in races});cut=days[int(len(days)*0.6)]
fit=[r for r in races if r[0]<cut];test=[r for r in races if r[0]>=cut]
print('İzmir koşu',len(races),'| fit',len(fit),'(<',cut,') | test',len(test))
def stage_nll(R_,th,mask):   # th: (5,3) katsayı; mask hangi özellikler; döner (koşu,5) NLL
    out=np.zeros((len(R_),5))
    for i,(t,X) in enumerate(R_):
        for s in range(5):
            sc=(th[s][:,None]*X).sum(0)[s:];sc=sc-sc.max();out[i,s]=-(sc[0]-np.log(np.exp(sc).sum()))
    return out
def fitmodel(free,shared=False):
    # free: boolean (3,) hangi özellikler öğrenilir; başlangıç: x1 katsayısı 1
    nf=free.sum()
    def th_of(v):
        th=np.zeros((5,3))
        for s in range(5):
            row=v[0:nf] if shared else v[s*nf:(s+1)*nf]
            th[s,free]=row
        return th
    v0=np.tile(np.array([1.0 if j==0 else 0.0 for j in range(3) if free[j]]),1 if shared else 5)
    f=lambda v:stage_nll(fit,th_of(v),None).sum()+0.5*np.sum((v-v0)**2)   # hafif L2
    v=minimize(f,v0,method='L-BFGS-B').x
    return th_of(v)
U=np.zeros((5,3));U[:,0]=1                                   # A: Harville p_Jason
M=np.zeros((5,3));M[:,1]=1                                   # piyasa
models={'A Harville(Jason)':U,'M Harville(piyasa)':M,
 'B tek üs':fitmodel(np.array([1,0,0],bool),True),
 'C sıraya özel üs':fitmodel(np.array([1,0,0],bool)),
 'D +piyasa (sıraya özel)':fitmodel(np.array([1,1,0],bool)),
 'E +piyasa+f_k (sıraya özel)':fitmodel(np.array([1,1,1],bool))}
base=stage_nll(test,U,None);days_t=np.array([r[0] for r in test]);ud=np.unique(days_t);rng=np.random.default_rng(7)
def ci(d):
    s=pd.DataFrame({'d':days_t,'x':d}).groupby('d').x.agg(['sum','size']);o=[]
    for _ in range(2000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
print('\nTest: A\'ya göre kazanç (nats/koşu, + iyi); 2.–5. sıra toplamı | tüm 1.–5. | GA(2.–5.)')
for n,th in models.items():
    nl=stage_nll(test,th,None);d25=(base-nl)[:,1:].sum(1);d15=(base-nl).sum(1);lo,hi=ci(d25)
    print(f'{n:30s} {d25.mean():+.4f} | {d15.mean():+.4f} | [{lo:+.4f},{hi:+.4f}]')
print('\nKatsayılar (satır=sıra 1..5; x1=logJason, x2=logPiyasa, x3=f_k)')
for n in ['C sıraya özel üs','D +piyasa (sıraya özel)','E +piyasa+f_k (sıraya özel)']:print(n);print(np.round(models[n],3))
print('\nC (sıraya özel üs) ZEMİNİNE göre ek kazanç, 2.–5. sıra (üretimde gam üsleri zaten var):')
nC=stage_nll(test,models['C sıraya özel üs'],None)
for n in ['B tek üs','D +piyasa (sıraya özel)','E +piyasa+f_k (sıraya özel)']:
    d=(nC-stage_nll(test,models[n],None))[:,1:].sum(1);lo,hi=ci(d);print(f'{n:30s} {d.mean():+.4f} [{lo:+.4f},{hi:+.4f}]')
