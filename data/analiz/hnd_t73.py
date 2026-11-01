"""T73 handikap sırası stratejisi. python3 data/analiz/hnd_t73.py"""
import gzip,json,glob,re,unicodedata,numpy as np,pandas as pd
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
rows=[]
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=f.split('/')[-1][:10]
    if t<'2024-04-01': continue
    try: d=json.load(gzip.open(f))
    except Exception: continue
    for hip,rs in (d.get('program') or {}).items():
        for r in rs:
            b=re.sub(r'\s+',' ',(r.get('typeDescription') or '').split('/')[0].strip().upper());m=re.match(r'ŞARTLI (\d)',b)
            c='Maiden' if b.startswith('MAIDEN') else ('ŞARTLI '+m.group(1) if m else ('Handikap' if b.startswith('HANDIKAP') or b.startswith('KISA VADE') else ('KV' if b.startswith('KV') else 'Diğer')))
            rows.append((t,asc(hip),int(r['number']),c))
C=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','cins']).drop_duplicates(['tarih','hipodrom','kosu'])
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','hnd']];J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc)
P=P.merge(J.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left').merge(C,on=['tarih','hipodrom','kosu'],how='left')
P=P.dropna(subset=['sira','p_piyasa','hnd','cins'])
def top3(p):
    n=len(p);q=np.zeros(n)
    for i in range(n):
        s=p[i]
        for j in range(n):
            if j==i: continue
            s+=p[j]*p[i]/(1-p[j])
            for k in range(n):
                if k in (i,j): continue
                s+=p[j]*p[k]/(1-p[j])*p[i]/max(1-p[j]-p[k],1e-9)
        q[i]=s
    return q
rec=[]
for (t,h,k),g in P.groupby(['tarih','hipodrom','kosu']):
    if len(g)<6 or len(g)>14 or (g.sira==1).sum()!=1: continue
    pm=(g.p_piyasa/g.p_piyasa.sum()).values;e3=top3(pm);hn=g.hnd.values.astype(float);sr=g.sira.values;n=len(g)
    rk=pd.Series(hn).rank(ascending=False,method='average').values
    for i in range(n): rec.append((t,g.cins.iloc[0],rk[i],n,float(sr[i]==1),pm[i],float(sr[i]<=3),e3[i]))
R=pd.DataFrame(rec,columns=['t','c','rk','n','w','pw','t3','p3']);print('at',len(R),'koşu',R.groupby(['t']).ngroups)
rng=np.random.default_rng(73)
def boot(S,f,n=3000):
    days=S.t.values;u=np.unique(days);ix={d:np.where(days==d)[0] for d in u};o=[]
    for _ in range(n):
        s=rng.integers(0,len(u),len(u));o.append(f(S.iloc[np.concatenate([ix[u[i]] for i in s])]))
    return np.percentile(o,[1.25,98.75])
print('\nBETİMLEYİCİ: hnd sırası (tüm cinsler) gerçek/beklenen kazanma ve ilk-3')
for lab,m in (('1',R.rk<=1.5),('2-3',(R.rk>1.5)&(R.rk<=3.5)),('4-6',(R.rk>3.5)&(R.rk<=6.5)),('7+',R.rk>6.5)):
    S=R[m];print(f'hnd sıra {lab:4s} at {len(S):6d} kazanma {S.w.mean():.4f} bek {S.pw.mean():.4f} | ilk3 {S.t3.mean():.4f} bek {S.p3.mean():.4f}')
f1=lambda S:S.t3.mean()-S.p3.mean();S1=R[R.c.isin(['ŞARTLI 3','ŞARTLI 4','ŞARTLI 5'])&(R.rk<=3.5)]
print('\nİDDİA1 Şartlı3-5 hnd sırası 1-3 ilk-3: gerçek %.4f beklenen %.4f fark %.4f'%(S1.t3.mean(),S1.p3.mean(),f1(S1)),'GA97,5',boot(S1,f1),'at',len(S1))
f2=lambda S:S.w.mean()-S.pw.mean();R['alt']=R.rk>(R.n+1)/2;S2=R[R.alt]
print('İDDİA2 hnd alt yarı kazanma: gerçek %.4f beklenen %.4f fark %.4f'%(S2.w.mean(),S2.pw.mean(),f2(S2)),'GA97,5',boot(S2,f2),'at',len(S2))
for c in ('ŞARTLI 3','ŞARTLI 4','ŞARTLI 5','Handikap','Maiden'):
    S=R[(R.c==c)&(R.rk<=3.5)];S_=R[(R.c==c)&R.alt];print(f'  {c}: hnd1-3 ilk3 fark {f1(S):+.4f} (n={len(S)}) | alt yarı kazanma fark {f2(S_):+.4f} (n={len(S_)})')
