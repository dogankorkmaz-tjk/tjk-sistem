import pandas as pd,numpy as np,glob
d=pd.read_pickle('/tmp/claude-0/agf_d.pkl')
O=pd.concat([pd.read_csv(f) for f in glob.glob('data/odeme/*.csv.gz')])
O=O[O.tur.str.startswith("6'LI GANYAN")].drop_duplicates(['tarih','hipodrom','kosu','seq'])
G={k:g for k,g in d.groupby(['tarih','hipodrom','kosu'])}
rows=[]
for r in O.itertuples():
    for pos,k in enumerate(range(r.kosu-5,r.kosu+1),1):
        g=G.get((r.tarih,r.hipodrom,k))
        if g is None or g.kazandi.sum()!=1: continue
        g=g.copy();g['ar']=g.a.rank(ascending=False,method='first');b=(g.ar>4)|(g.ganyan>=7)
        pj=g.p_Jason/g.p_Jason.sum();pm=g.p_piyasa/g.p_piyasa.sum()
        rows.append(dict(seq=r.seq,pos=pos,obs=int(b[g.kazandi==1].iloc[0]),ej=pj[b].sum(),em=pm[b].sum()))
D=pd.DataFrame(rows);D['konum']=D.seq.astype(str)+'/'+D.pos.astype(str)
out=['konum n gözlenen Jason-beklenen piyasa-beklenen']
for k in['1/5','2/1','2/2']:
    g=D[D.konum==k];out.append(f"{k} n={len(g)} gözlenen {g.obs.mean():.3f} Jason {g.ej.mean():.3f} piyasa {g.em.mean():.3f}")
g=D[~D.konum.isin(['1/5','2/1','2/2'])];out.append(f"diğer n={len(g)} gözlenen {g.obs.mean():.3f} Jason {g.ej.mean():.3f} piyasa {g.em.mean():.3f}")
open('data/analiz/altili_ayak_t90b_sonuc.txt','w').write('\n'.join(out));print('\n'.join(out))
