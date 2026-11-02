import pandas as pd,numpy as np,glob,json
rows=[]
for f in sorted(glob.glob('data/piyasa/2026-*.csv.gz')):
    gun=f[-17:-7];d=pd.read_csv(f);d=d[(d.tip==1001)&(d.oran>1.0)]
    if d.empty: continue
    try:G=json.load(open(f'docs/data/gun/{gun}.json'))
    except Exception: continue
    S={}
    for h in G['hipodromlar']:
        for k in h['kosular']:
            for no,v in (k.get('sonuc') or {}).items(): S[(h['id'],k['kosu'],int(no))]=v
    for (h,k),x in d.groupby(['hipodrom','kosu']):
        ts=sorted(x.saat.unique())
        fi=x[x.saat==ts[0]].set_index('no').oran;la=x.sort_values('saat').groupby('no').oran.last()
        n=la.index
        if len(n)<4: continue
        ov_f=(1/fi).sum() if len(fi)==len(la) else np.nan;ov_l=(1/la).sum()
        for i in n:
            v=S.get((h,k,int(i)))
            if not v: continue
            rows.append(dict(gun=gun,h=h,k=k,no=i,ilk=fi.get(i,np.nan),son=la[i],g=v['g'],pj=v['pm2'],pm=v['pp'],sira=v['sira'],ovf=ov_f,ovl=ov_l,nts=len(ts)))
D=pd.DataFrame(rows);print(len(D),'at',D.groupby(['gun','h','k']).ngroups,'koşu;',D.groupby('h').gun.nunique().to_dict())
r=D.drop_duplicates(['gun','h','k'])
print('overround (Σ1/oran) ilk %.3f son %.3f'%(r.ovf.mean(),r.ovl.mean()),' | güncelleme sayısı medyan',r.nts.median())
print('sabit son oran / kapanış ganyan (medyan): %.3f'%(D.son/D.g).median(), ' ilk/son: %.3f'%(D.ilk/D.son).median())
D['pm_n']=D.pm
for lo,hi in((0,5),(5,10),(10,20),(20,999)):
    x=D[(D.g>=lo)&(D.g<hi)];print(f'kapanış ganyan {lo}-{hi}: n={len(x)} sabit son/ganyan {np.median(x.son/x.g):.2f} ilk/son {np.nanmedian(x.ilk/x.son):.2f}')
D['ev']=D.pj*D.son;D['get']=(D.sira==1)*D.son
for e in(1.0,1.1,1.2):
    x=D[D.ev>=e];print(f'p_Jason×sabit son oran ≥{e}: n={len(x)} kazanan {int((x.sira==1).sum())} ROI {x["get"].mean():.3f}')
D.to_csv('/tmp/claude-0/sabit_t95.csv',index=False)
