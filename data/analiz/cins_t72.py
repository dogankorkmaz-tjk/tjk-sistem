"""T72 koşu cinsi analizi. python3 data/analiz/cins_t72.py"""
import gzip,json,glob,re,math,unicodedata,numpy as np,pandas as pd
GAM=np.array([1,0.80,0.67,0.59,0.52])
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
rows=[]
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=f.split('/')[-1][:10]
    if t<'2024-04-01': continue
    try: d=json.load(gzip.open(f))
    except Exception: continue
    for hip,rs in (d.get('program') or {}).items():
        for r in rs:
            td=(r.get('typeDescription') or '').strip();b=re.sub(r'\s+',' ',td.split('/')[0].strip().upper())
            m=re.match(r'ŞARTLI (\d)',b)
            if b.startswith('MAIDEN'): c='Maiden'
            elif m: c='ŞARTLI '+m.group(1)
            elif b.startswith('HANDIKAP') or b.startswith('KISA VADE HANDIKAP'): c='Handikap'
            elif b.startswith('KV'): c='KV'
            elif b.startswith('SATIŞ'): c='SATIŞ'
            elif re.match(r'(G|GRUP) ?\d',b): c='Grup'
            else: c='Diğer'
            rows.append((t,asc(hip),int(r['number']),c,r.get('groupName') or ''))
C=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','cins','grup']);print('program koşu',len(C),C.cins.value_counts().to_dict())
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','hnd']];J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc)
P=P.merge(J.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left').merge(C.drop_duplicates(['tarih','hipodrom','kosu']),on=['tarih','hipodrom','kosu'],how='left')
P=P.dropna(subset=['sira','p_piyasa','ganyan']);print('eşleşen at',len(P),'cins eşleşmeyen',int(P.cins.isna().sum()))
def pl(p,sr):
    o=np.argsort(sr)[:5];m=np.ones(len(p),bool);t=0.0
    for k,i in enumerate(o):
        t+=GAM[k]*math.log(max(p[i]/p[m].sum(),1e-12));m[i]=False
    return t
rec=[]
for (t,h,k),g in P.groupby(['tarih','hipodrom','kosu']):
    if g.cins.isna().all() or len(g)<5 or (g.sira==1).sum()!=1: continue
    c=g.cins.iloc[0];pm=g.p_piyasa.values/g.p_piyasa.sum();w=int(np.argmin(g.sira.values));fav=int(np.argmax(pm))
    r=dict(t=t,c=c,n=len(g),favw=float(fav==w),wg=float(g.ganyan.values[w]),sur10=float(g.ganyan.values[w]>=10))
    if g.sira.notna().all() and len(g)>=6 and all((g.sira==j).sum()==1 for j in range(1,6)) and g.p_Jason.notna().all():
        pj=g.p_Jason.values/g.p_Jason.sum();sr=g.sira.values.astype(float);r['ust']=pl(pj,sr)-pl(pm,sr)
    hn=g.hnd.values.astype(float)
    if np.isfinite(hn).sum()>=5:
        mx=np.nanmax(hn);top=np.where(hn==mx)[0];r['hnd_win']=float(w in top)/len(top)*0+ (1.0/len(top) if w in top else 0.0)*1.0;r['hnd_exp']=float(pm[top].sum()/len(top)) if len(top) else np.nan
        r['hnd_pay']=1.0
    rec.append(r)
R=pd.DataFrame(rec);rng=np.random.default_rng(72)
def boot(f,S,n=4000):
    days=S.t.values;u=np.unique(days);ix={d:np.where(days==d)[0] for d in u};o=[]
    for _ in range(n):
        s=rng.integers(0,len(u),len(u));o.append(f(S.iloc[np.concatenate([ix[u[i]] for i in s])]))
    return np.percentile(o,[1.7,98.3])
print('\nSINIF TABLOSU (koşu, favori kazanma, kazanan ganyan≥10, model üstünlüğü nats)')
for c,S in sorted(R.groupby('c'),key=lambda x:-len(x[1])):
    u=S.ust.dropna();print(f'{c:10s} n={len(S):5d} fav {S.favw.mean():.3f} sur10 {S.sur10.mean():.3f} ort_ganyan {S.wg.mean():.1f} üstünlük {u.mean() if len(u) else float("nan"):+.4f} (n={len(u)})')
sart=R[R.c.isin(['ŞARTLI 1','ŞARTLI 3','ŞARTLI 4','ŞARTLI 5'])];s2=R[R.c=='ŞARTLI 2']
f=lambda S:S[S.c=='ŞARTLI 2'].sur10.mean()-S[S.c.isin(['ŞARTLI 1','ŞARTLI 3','ŞARTLI 4','ŞARTLI 5'])].sur10.mean()
S_=R[R.c.str.startswith('ŞARTLI')];print('\nC1 Şartlı2 sür10 − diğer şartlı: %.4f'%f(S_),'GA98,3',boot(f,S_))
h=R[R.c.isin(['ŞARTLI 4','ŞARTLI 5'])].dropna(subset=['hnd_win']);g=lambda S:S.hnd_win.mean()-S.hnd_exp.mean()
print('C2 Şartlı4+5 hnd en yüksek at: kazanma %.3f beklenen(piyasa) %.3f fark %.4f'%(h.hnd_win.mean(),h.hnd_exp.mean(),g(h)),'GA98,3',boot(g,h),'n',len(h))
m=lambda S:S[S.c.isin(['Maiden','ŞARTLI 1'])].favw.mean()-S[~S.c.isin(['Maiden','ŞARTLI 1'])].favw.mean()
print('C3 Maiden+Şartlı1 favori kazanma − diğer: %.4f'%m(R),'GA98,3',boot(m,R))
