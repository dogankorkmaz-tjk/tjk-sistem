"""T40 galopta dil bağı (keşif): 2026-01-15+ koşularda DB eklenen atlar (f_db_ekle) — son 21 günde galoplu olanlar vs galopsuz vs DB değişmeyen;
ölçü: piyasaya göre bitiş artığı (res) ve kazanma−piyasa p, gün kümeli bootstrap. python3 data/analiz/galop_dilbagi.py <scratchpad>"""
import sys,glob,numpy as np,pandas as pd
S=sys.argv[1]
E=pd.read_pickle('/tmp/claude-0/ekip.pkl').drop_duplicates(['tarih','hipodrom','kosu','no']);E['tarih']=E.tarih.astype(str)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','at','p_piyasa','pct','n_at','kazandi']];J['tarih']=J.tarih.astype(str)
d=J.merge(E,on=['tarih','hipodrom','kosu','no'],how='left').sort_values(['at','tarih']).reset_index(drop=True)
db=d.ekip.fillna('').str.split().apply(lambda s:'DB' in s);prev=db.groupby(d['at']).shift(1)
d['ekle']=(db&(prev==False)).values;d['cikar']=((~db)&(prev==True)).values;d['var']=prev.notna().values
rk=d.groupby(['tarih','hipodrom','kosu']).p_piyasa.rank(ascending=False,method='first');d['res']=((rk-1)/(d.n_at-1).clip(lower=1)-d.pct).clip(-1,1)
d['pn']=d.p_piyasa/d.groupby(['tarih','hipodrom','kosu']).p_piyasa.transform('sum');d['ex']=d.kazandi-d.pn
G=pd.concat([pd.read_csv(f,low_memory=False) for f in glob.glob('data/galop/*.csv.gz')]);G['it']=pd.to_datetime(G['it'])
Gk={k:list(v) for k,v in G.groupby(G['at'].astype(str))['it']}
x=d[(d.tarih>='2026-01-15')&d['var']].copy();x['dt']=pd.to_datetime(x.tarih)
x['galop']=[any((dt-pd.Timedelta(days=21)<=g<dt) for g in Gk.get(a,[])) for a,dt in zip(x['at'].astype(str),x.dt)]
rng=np.random.default_rng(1)
def r(nm,g):
    g=g.reset_index(drop=True);gun=g.tarih.values;ug=np.unique(gun);ii={u:np.where(gun==u)[0] for u in ug}
    for k in ['res','ex']:
        v=g[k].values;m=np.nanmean(v);bs=[np.nanmean(v[np.concatenate([ii[ug[i]] for i in rng.integers(0,len(ug),len(ug))])]) for _ in range(500)]
        print(f'{nm:34s} n={len(g):5d} {k}: {m:+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]')
r('DB değişmedi',x[~x.ekle&~x.cikar]);r('DB eklendi, galop var',x[x.ekle&x.galop]);r('DB eklendi, galop yok',x[x.ekle&~x.galop]);r('DB çıkarıldı',x[x.cikar])
r('galop var (tüm)',x[x.galop]);r('galop yok (tüm)',x[~x.galop])
