"""İki piyasa sağlamlık (ön kayıt 15 Ekim 2026 03:20): ABD yarış öncesi oranlarıyla. Kullanım: python3 -I iki_piyasa_erken.py"""
import glob,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/'
def dec(o):
    try:
        if str(o).upper() in('EVS','EVENS'):return 2.0
        x,y=str(o).split('/');return float(x)/float(y)+1
    except Exception:return np.nan
T=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci/*.csv.gz')])
T=T[(T.ulke=='abd')&T.ganyan.notna()&(T.ganyan>0)&~T.kosmadi.fillna(False).astype(bool)&(T.no>0)].copy()
T['at']=T['at'].astype(str).str.replace(r'\(\d+\)\s*$','',regex=True).str.strip().str.upper()
S=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci_sl/*.csv.gz')]);S=S[(S.ulke=='abd')&S.oran_son.notna()].copy()
S['at']=S['at'].astype(str).str.upper().str.strip()
h=S.oran_gecmis.fillna('').astype(str).apply(lambda s:[x for x in s.split('|') if x])
S['o_gec']=h.apply(lambda l:dec(l[-1]) if l else np.nan);S['o_erk']=h.apply(lambda l:dec(l[0]) if l else np.nan)
K=['tarih','hipodrom','kosu'];T['p']=1/T.ganyan
g=T.groupby(K).agg(top=('p','sum'),n=('p','size'),kaz=('sira',lambda s:(s==1).sum()),dup=('ganyan',lambda s:s.round(2).duplicated().any()))
T=T.set_index(K).loc[g[(g.kaz==1)&(g.n>=3)&g.top.between(1.2,1.7)&~g.dup].index].reset_index()
rows=[]
for (t,hp),tg in T.groupby(['tarih','hipodrom']):
    sg=S[(S.tarih==t)&(S.hipodrom==hp)]
    if sg.empty:continue
    for k,tk in tg.groupby('kosu'):
        a=set(tk['at']);best=None
        for sid,sk in sg.groupby('sl_id'):
            o=len(a&set(sk['at']))/len(a)
            if best is None or o>best[0]:best=(o,sid)
        if best and best[0]>=0.6:
            m=tk.merge(sg[sg.sl_id==best[1]][['at','oran_son','o_gec','o_erk']],on='at',how='inner')
            if len(m)==len(tk):rows.append(m)
D=pd.concat(rows,ignore_index=True)
tam=D.groupby(K).o_gec.transform(lambda s:s.notna().all())&D.groupby(K).o_erk.transform(lambda s:s.notna().all())
print('eşleşen ABD koşusu',D.groupby(K).ngroups,'| geçmişi tam olan',D[tam].groupby(K).ngroups)
D=D[tam].copy();D['y']=(D.sira==1).astype(int);D['gun']=D.tarih+D.hipodrom;D['pn']=D.p/D.groupby(K).p.transform('sum')
def boot(v,g,B=3000):
    s=pd.DataFrame({'v':v.values,'g':g.values}).groupby('g').v.agg(['sum','size']);rng=np.random.default_rng(21);o=[]
    for _ in range(B):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
gunler=sorted(D.tarih.unique());yar=gunler[len(gunler)//2]
for ad,col in (('SON','oran_son'),('GEÇ (birincil)','o_gec'),('ERKEN','o_erk')):
    q=(1/D[col])/D.groupby(K)[col].transform(lambda s:(1/s).sum());D['q']=q
    w=D[D.y==1];l=np.log(w.q)-np.log(w.pn);lo,hi=boot(l,w.gun)
    m=D.q*D.ganyan>1.25;z=D[m];r=z.y*z.ganyan;a,b=boot(r,z.gun)
    h1=z[z.tarih<yar];h2=z[z.tarih>=yar];top=r.nlargest(3).sum()
    print(f'{ad:15s} tahmin q−TJK {l.mean():+.4f} [{lo:+.3f},{hi:+.3f}] | k=1,25: bahis {len(z)} isabet {int(z.y.sum())} ROI {r.mean():.3f} GA [{a:.2f},{b:.2f}] | yarılar {(h1.y*h1.ganyan).mean():.2f}/{(h2.y*h2.ganyan).mean():.2f} | büyük 3 hariç {(r.sum()-top)/len(z):.2f}')
# oran hareketi: ABD'de seçilen atların oranı son dakikada ne yöne gitti?
D['q_gec']=(1/D.o_gec)/D.groupby(K).o_gec.transform(lambda s:(1/s).sum());D['q_son']=(1/D.oran_son)/D.groupby(K).oran_son.transform(lambda s:(1/s).sum())
m=D.q_gec*D.ganyan>1.25;print('GEÇ kuralının seçtiği atlarda ABD olasılığı son dakikada: ort. son/geç oranı',round((D[m].q_son/D[m].q_gec).mean(),3),'| tüm atlar',round((D.q_son/D.q_gec).mean(),3))
