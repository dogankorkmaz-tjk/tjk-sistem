"""İki piyasa testi (ön kayıt 15 Ekim 2026 01:45). Kullanım: python3 -I iki_piyasa.py"""
import glob,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/'
T=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci/*.csv.gz')])
T=T[T.ganyan.notna()&(T.ganyan>0)&~T.kosmadi.fillna(False).astype(bool)&(T.no>0)].copy()
T['at']=T['at'].astype(str).str.replace(r'\(\d+\)\s*$','',regex=True).str.strip().str.upper()
S=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci_sl/*.csv.gz')])
S=S[S.oran_son.notna()].copy();S['at']=S['at'].astype(str).str.upper().str.strip()
K=['tarih','hipodrom','kosu']
T['p']=1/T.ganyan;g=T.groupby(K).agg(top=('p','sum'),n=('p','size'),kaz=('sira',lambda s:(s==1).sum()),dup=('ganyan',lambda s:s.round(2).duplicated().any()))
ok=g[(g.kaz==1)&(g.n>=3)&g.top.between(1.2,1.7)&~g.dup].index
T=T.set_index(K).loc[ok].reset_index()
# koşu eşleştirme: aynı gün+hipodrom, at adı örtüşmesi
rows=[]
for (t,h),tg in T.groupby(['tarih','hipodrom']):
    sg=S[(S.tarih==t)&(S.hipodrom==h)]
    if sg.empty: continue
    for k,tk in tg.groupby('kosu'):
        a=set(tk['at']);best=None
        for sid,sk in sg.groupby('sl_id'):
            o=len(a&set(sk['at']))/len(a)
            if best is None or o>best[0]: best=(o,sid)
        if best and best[0]>=0.6:
            m=tk.merge(sg[sg.sl_id==best[1]][['at','oran_son']],on='at',how='inner')
            if len(m)==len(tk): rows.append(m)
D=pd.concat(rows,ignore_index=True)
D['pn']=D.p/D.groupby(K).p.transform('sum');D['q']=(1/D.oran_son)/D.groupby(K).oran_son.transform(lambda s:(1/s).sum())
D['y']=(D.sira==1).astype(int);D['gun']=D.tarih+D.hipodrom
print('eşleşen koşu',D.groupby(K).ngroups,D.groupby('ulke').apply(lambda x:x[K].drop_duplicates().shape[0]).to_dict())
def boot(v,g,B=3000):
    s=pd.DataFrame({'v':v.values,'g':g.values}).groupby('g').v.agg(['sum','size']);rng=np.random.default_rng(12);o=[]
    for _ in range(B):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
for u,x in list(D.groupby('ulke'))+[('tümü',D)]:
    w=x[x.y==1];l=np.log(w.q)-np.log(w.pn);lo,hi=boot(l,w.gun)
    print(f'\n[{u}] koşu {w.shape[0]} | tahmin q−TJK: {l.mean():+.4f} nats/koşu [{lo:+.4f},{hi:+.4f}]')
    gunler=sorted(x.tarih.unique());yar=gunler[len(gunler)//2]
    for k in (1.25,1.10):
        m=x.q*x.ganyan>k;z=x[m];ret=z.y*z.ganyan
        if len(z)<5: print(f'  k={k}: bahis {len(z)}');continue
        lo,hi=boot(ret,z.gun);h1=z[z.tarih<yar];h2=z[z.tarih>=yar]
        print(f'  k={k}: bahis {len(z)} isabet {int(z.y.sum())} ROI {ret.mean():.3f} GA [{lo:.2f},{hi:.2f}] | ilk yarı {((h1.y*h1.ganyan).mean() if len(h1) else float("nan")):.2f} (n {len(h1)}) ikinci yarı {((h2.y*h2.ganyan).mean() if len(h2) else float("nan")):.2f} (n {len(h2)})')
D.to_csv('/tmp/claude-0/-home-claude-tjk-sistem/0584d01c-865c-5e93-a1ba-b5b1dcefa381/scratchpad/iki_piyasa.csv',index=False)
