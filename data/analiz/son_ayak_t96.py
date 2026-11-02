import pandas as pd,numpy as np,glob
rng=np.random.default_rng(96)
d=pd.read_pickle('/tmp/claude-0/agf_d.pkl')
O=pd.concat([pd.read_csv(f) for f in glob.glob('data/odeme/*.csv.gz')])
O=O[O.tur.str.startswith("6'LI GANYAN")].drop_duplicates(['tarih','hipodrom','kosu','seq'])
G={k:g for k,g in d.groupby(['tarih','hipodrom','kosu'])}
rows=[];bets=[]
for r in O.itertuples():
    for pos,k in enumerate(range(r.kosu-5,r.kosu+1),1):
        g=G.get((r.tarih,r.hipodrom,k))
        if g is None or g.kazandi.sum()!=1: continue
        g=g.copy();g['ar']=g.a.rank(ascending=False,method='first');b=(g.ar>4)|(g.ganyan>=7)
        pj=g.p_Jason/g.p_Jason.sum()
        son=(r.seq==0 and pos==6) or (r.seq==2 and pos==6)
        konum='SON' if son else 'diger'
        rows.append(dict(gun=r.tarih,konum=konum,obs=int(b[g.kazandi==1].iloc[0]),ej=pj[b].sum()))
        v=g[(g.ar>4)&(pj/g.a>=1.0)]
        for x in v.itertuples(): bets.append(dict(gun=r.tarih,konum=konum,ret=(x.ganyan if x.kazandi==1 else 0.0)))
D=pd.DataFrame(rows);B=pd.DataFrame(bets)
def boot(df,f,n=2000):
    gl=df.gun.unique();grp={k:v for k,v in df.groupby('gun')};s=[]
    for _ in range(n):
        x=pd.concat([grp[k] for k in rng.choice(gl,len(gl))]);s.append(f(x))
    return np.percentile(s,[2.5,97.5])
out=[]
for k in['SON','diger']:
    g=D[D.konum==k];f=lambda x:(x.obs-x.ej).mean()
    out.append(f"(a) {k} n={len(g)} gözlenen {g.obs.mean():.3f} Jason {g.ej.mean():.3f} fark {f(g):+.3f} GA95 {boot(g,f).round(3)}")
for k in['SON','diger']:
    g=B[B.konum==k];f=lambda x:x.ret.mean()
    out.append(f"(b) {k} V-uzun at bahis={len(g)} kazanan={(g.ret>0).sum()} ROI {f(g):.3f} GA95 {boot(g,f).round(3)} (en büyük ödeme çıkarılınca {(g.ret.sum()-g.ret.max())/(len(g)-1):.3f}, yalnız bilgi)")
open('data/analiz/son_ayak_t96_sonuc.txt','w').write('\n'.join(out));print('\n'.join(out))
