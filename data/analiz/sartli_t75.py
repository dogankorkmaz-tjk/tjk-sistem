"""T75. python3 data/analiz/sartli_t75.py"""
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
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','at','sira','antrenor','p_piyasa','ganyan','n_at']];J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc)
J=J.merge(C,on=['tarih','hipodrom','kosu'],how='left');J=J[J.cins.notna()&J.p_piyasa.notna()&J.sira.notna()].reset_index(drop=True)
J['pp']=J.p_piyasa/J.groupby(['tarih','hipodrom','kosu']).p_piyasa.transform('sum');J['w']=(J.sira==1).astype(float);J['dt']=pd.to_datetime(J.tarih)
rng=np.random.default_rng(75)
def boot(S,f,n=2000,q=(1.25,98.75)):
    days=S.tarih.values;u=np.unique(days);ix={d:np.where(days==d)[0] for d in u};o=[]
    for _ in range(n):
        s=rng.integers(0,len(u),len(u));o.append(f(S.iloc[np.concatenate([ix[u[i]] for i in s])]))
    return np.percentile(o,q)
# (a)
W=J[(J.w==1)&(J.tarih>='2024-04-01')].copy()
gs={'3 Yaşlı Araplar':'A3','4 ve Yukarı Araplar':'A4','3 Yaşlı İngilizler':'I3','4 ve Yukarı İngilizler':'I4','2 Yaşlı İngilizler':'I2'}
def gk(x):
    for k,v in gs.items():
        if x.startswith(k.split()[0]) and (('Arap' in x)==('Arap' in k)): return v
W['g']=W.grup.map(gk);W['band']=pd.cut(W.n_at,[0,8,11,99],labels=['<=8','9-11','>=12']);W['s10']=(W.ganyan>=10).astype(float)
print('(a) alan bandı × grup: sürpriz oranı (koşu sayısı)')
tab=W.pivot_table(index='g',columns='band',values='s10',aggfunc=['mean','size'],observed=True);print(tab.round(3).to_string())
def fw(S):
    out=0;tot=0
    for b,x in S.groupby('band',observed=True):
        m=x.groupby('g').s10.agg(['mean','size']);m=m[m['size']>=30]
        if len(m)>=2: out+=(m['mean'].max()-m['mean'].min())*len(x);tot+=len(x)
    return out/tot
print('ağırlıklı bant-içi (max−min) fark %.4f'%fw(W),'GA97,5',boot(W.dropna(subset=['g']),fw,1000,(1.25,98.75)))
fa=lambda S:S[S.g=='A4'].s10.mean()-S[S.g=='I3'].s10.mean()
for b,x in W.groupby('band',observed=True):print(f'  bant {b}: A4−I3 {fa(x):+.4f}')
print('  genel A4−I3 %.4f'%fa(W),boot(W.dropna(subset=['g']),fa,1000,(1.25,98.75)))
# (b)
J['res']=J.w-J.pp;J=J.sort_values(['antrenor','dt']).reset_index(drop=True);q=np.full(len(J),np.nan)
for a,g in J.groupby('antrenor'):
    dts=g.dt.values.astype('datetime64[D]').astype(np.int64);r=g.res.values;cs=np.r_[0,np.cumsum(r)];ix=g.index.values
    lo=np.searchsorted(dts,dts-180,side='left');hi=np.searchsorted(dts,dts,side='left');n=hi-lo;s=cs[hi]-cs[lo];q[ix]=np.where(n>=30,s/np.maximum(n,1),np.nan)
J['aq']=q;J=J[J.tarih>='2024-04-01']
J['dilim']=J.groupby('tarih').aq.transform(lambda x:x.rank(pct=True))
M=J[J.cins.isin(['Maiden','ŞARTLI 1'])&J.aq.notna()].copy();thr=J[J.aq.notna()].aq.quantile(0.9);S=M[M.aq>=thr]
fe=lambda S:S.w.mean()-S.pp.mean()
print('\n(b) Maiden+Şartlı1 en iyi %%10 antrenör (eşik aq≥%.4f): at %d kazanma %.4f beklenen %.4f fark %.4f'%(thr,len(S),S.w.mean(),S.pp.mean(),fe(S)),'GA97,5',boot(S,fe,2000,(1.25,98.75)))
S_=M[M.aq<thr];print('   diğer antrenörler: fark %.4f'%fe(S_))
