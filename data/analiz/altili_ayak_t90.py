import pandas as pd,numpy as np,glob
d=pd.read_pickle('/tmp/claude-0/agf_d.pkl');d['gun']=d.tarih.astype(str).str[:10]
O=pd.concat([pd.read_csv(f) for f in glob.glob('data/odeme/*.csv.gz')])
O=O[O.tur.str.startswith("6'LI GANYAN")].drop_duplicates(['tarih','hipodrom','kosu','seq'])
G={k:g for k,g in d.groupby(['tarih','hipodrom','kosu'])}
rows=[]
for r in O.itertuples():
    for pos,k in enumerate(range(r.kosu-5,r.kosu+1),1):
        g=G.get((r.tarih,r.hipodrom,k))
        if g is None or g.kazandi.sum()!=1: continue
        g=g.copy();g['ar']=g.a.rank(ascending=False,method='first');w=g[g.kazandi==1].iloc[0]
        rows.append(dict(gun=str(r.tarih)[:10],seq=r.seq,pos=pos,bust=int(w.ar>4 or w.ganyan>=7),fav=int(w.ar==1),gan=w.ganyan,n=len(g)))
D=pd.DataFrame(rows);D['konum']=D.seq.astype(str)+'/'+D.pos.astype(str)
rng=np.random.default_rng(3);ug=D.gun.unique();ix=D.groupby('gun').indices
def fark(x,m): return x[m(x)].bust.mean()-x[~m(x)].bust.mean()
out=[f"ayak {len(D)}, altılı≈{len(D)//6}, genel bust {D.bust.mean():.3f}"]
H={'H1 seq1/ayak5':lambda x:(x.seq==1)&(x.pos==5),'H2 seq2/ayak1':lambda x:(x.seq==2)&(x.pos==1),'H3 seq2/ayak2':lambda x:(x.seq==2)&(x.pos==2)}
for k,m in H.items():
    r=[]
    for _ in range(2000):
        s=rng.choice(ug,len(ug));x=D.iloc[np.concatenate([ix[g] for g in s])];r.append(fark(x,m))
    y=D[m(D)];out.append(f"{k}: n={len(y)} bust {y.bust.mean():.3f} diğer {D[~m(D)].bust.mean():.3f} fark {fark(D,m):+.3f} GA%98.3 {np.percentile(r,[0.85,99.15]).round(3)}")
out.append('keşifsel (konum: n, bust, favori kazanma, medyan kazanan ganyanı)')
for k,g in D.groupby('konum'): out.append(f"  {k}: n={len(g)} bust {g.bust.mean():.3f} fav {g.fav.mean():.3f} medyan gan {g.gan.median():.2f}")
open('data/analiz/altili_ayak_t90_sonuc.txt','w').write('\n'.join(out));print('\n'.join(out))
