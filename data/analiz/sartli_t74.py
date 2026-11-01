"""T74 şartlı püf noktaları. python3 data/analiz/sartli_t74.py"""
import gzip,json,glob,re,unicodedata,numpy as np,pandas as pd
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
rows=[]
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=f.split('/')[-1][:10]
    if t<'2023-06-01': continue
    try: d=json.load(gzip.open(f))
    except Exception: continue
    for hip,rs in (d.get('program') or {}).items():
        for r in rs:
            b=re.sub(r'\s+',' ',(r.get('typeDescription') or '').split('/')[0].strip().upper());m=re.match(r'ŞARTLI (\d)',b)
            c='Maiden' if b.startswith('MAIDEN') else ('ŞARTLI '+m.group(1) if m else ('Handikap' if b.startswith('HANDIKAP') or b.startswith('KISA VADE') else 'Diğer'))
            rows.append((t,asc(hip),int(r['number']),c,(r.get('groupName') or '').strip()))
C=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','cins','grup']).drop_duplicates(['tarih','hipodrom','kosu'])
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','at','sira','sahip','p_piyasa','ganyan']];J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc)
J=J.merge(C,on=['tarih','hipodrom','kosu'],how='left').sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
J=J.sort_values(['at','tarih','hipodrom','kosu']);J['pcins']=J.groupby('at').cins.shift();J['psira']=J.groupby('at').sira.shift()
J=J.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
J=J[(J.tarih>='2024-04-01')&J.cins.notna()&J.p_piyasa.notna()&J.sira.notna()].copy()
J=J.reset_index(drop=True)
J['pp']=J.p_piyasa/J.groupby(['tarih','hipodrom','kosu']).p_piyasa.transform('sum');J['w']=(J.sira==1).astype(float)
# ahır büyüklüğü: sahibin önceki 180 günde başlatma sayısı
ow=J[['tarih','sahip']].copy();ow['dt']=pd.to_datetime(ow.tarih);cnt=np.zeros(len(J))
for s,g in ow.groupby('sahip'):
    dts=g.dt.values.astype('datetime64[D]').astype(np.int64);ix=g.index.values;srt=np.sort(dts)
    cnt[ix]=np.searchsorted(srt,dts,side='left')-np.searchsorted(srt,dts-180,side='left')
J['big']=cnt>=100
rng=np.random.default_rng(74)
def boot(S,f,n=3000,q=(0.625,99.375)):
    days=S.tarih.values;u=np.unique(days);ix={d:np.where(days==d)[0] for d in u};o=[]
    for _ in range(n):
        s=rng.integers(0,len(u),len(u));o.append(f(S.iloc[np.concatenate([ix[u[i]] for i in s])]))
    return np.percentile(o,q)
fe=lambda S:S.w.mean()-S.pp.mean()
S1=J[(J.cins=='ŞARTLI 3')&(J.pcins=='Maiden')&(J.psira==1)];print('D1 Maiden kazananı -> Şartlı 3: n',len(S1),'kazanma %.4f beklenen %.4f fark %.4f'%(S1.w.mean(),S1.pp.mean(),fe(S1)),'GA98,75',boot(S1,fe))
S1b=S1[S1.grup.str.contains('3 Yaşlı Arap')];print('   yalnız 3 yaşlı Arap: n',len(S1b),'fark %.4f'%fe(S1b),boot(S1b,fe) if len(S1b)>30 else '')
# D2
R=J[J.w==1].copy();R['iki']=((R.ganyan<3)|(R.ganyan>=10)).astype(float)
Sx=R[R.cins.str.startswith('ŞARTLI')]
f2=lambda S:S[S.cins=='ŞARTLI 2'].iki.mean()-S[S.cins!='ŞARTLI 2'].iki.mean()
print('D2 Şartlı2 uç oranı %.3f diğer şartlı %.3f fark %.4f'%(Sx[Sx.cins=='ŞARTLI 2'].iki.mean(),Sx[Sx.cins!='ŞARTLI 2'].iki.mean(),f2(Sx)),'GA98,75',boot(Sx,f2))
# D3
S3=J[J.cins.isin(['Maiden','ŞARTLI 1'])&J.big];print('D3 Maiden+Şartlı1 büyük ahır: at',len(S3),'kazanma %.4f beklenen %.4f fark %.4f'%(S3.w.mean(),S3.pp.mean(),fe(S3)),'GA98,75',boot(S3,fe))
S3k=J[J.cins.isin(['Maiden','ŞARTLI 1'])&~J.big];print('   küçük ahır: fark %.4f'%fe(S3k))
# D4
gs=['3 Yaşlı Araplar','4 ve Yukarı Araplar','3 Yaşlı İngilizler','4 ve Yukarı İngilizler','2 Yaşlı İngilizler']
Rk=R.copy();Rk['g']=Rk.grup.map(lambda x:next((k for k in gs if x.replace('Yukarı','Yukarı').startswith(k[:6]) and ('Arap' in x)==('Arap' in k) and x.split()[0]==k.split()[0]),None))
print('D4 grup (kazanan ganyan ≥10 oranı, favori=ganyan en düşük ~ kazanan ganyan<3 oranı):')
for k,S in Rk.groupby('g'):print(f'  {k:26s} koşu {len(S):5d} sür10 {(S.ganyan>=10).mean():.3f} kazanan<3 {(S.ganyan<3).mean():.3f}')
tab=Rk.groupby('g').apply(lambda S:(S.ganyan>=10).mean());print('en yüksek−en düşük sür10: %.3f'%(tab.max()-tab.min()))
fd=lambda S:(lambda t:t.max()-t.min())(S.groupby('g').apply(lambda x:(x.ganyan>=10).mean()));print('   bootstrap alt sınır (≥0,03?):',boot(Rk.dropna(subset=['g']),fd,500,(1.25,98.75)))
