import pandas as pd,numpy as np,glob,json
def dk(s):
    p=[int(x) for x in str(s).split(':')];return p[0]*60+p[1]+(p[2]/60 if len(p)>2 else 0)
rows=[]
for f in sorted(glob.glob('data/piyasa/2026-*.csv.gz')):
    gun=f[-17:-7];d=pd.read_csv(f);d=d[(d.tip==1001)&(d.oran>1.0)]
    if d.empty: continue
    try:G=json.load(open(f'docs/data/gun/{gun}.json'))
    except Exception: continue
    for h in G['hipodromlar']:
        for k in h['kosular']:
            S=k.get('sonuc') or {}
            if not S or not k.get('saat'): continue
            x=d[(d.hipodrom==h['id'])&(d.kosu==k['kosu'])]
            if x.empty: continue
            st=dk(k['saat']);x=x.assign(t=x.saat.map(dk))
            for no,v in S.items():
                y=x[x.no==int(no)].sort_values('t')
                if y.empty: continue
                rec=dict(gun=gun,h=h['id'],k=k['kosu'],no=int(no),g=v['g'],pj=v['pm2'],sira=v['sira'],son=y.oran.iloc[-1],tson=st-y.t.iloc[-1])
                for m in(30,15,10,5,3):
                    z=y[y.t<=st-m];rec[f'o{m}']=z.oran.iloc[-1] if len(z) else np.nan
                rows.append(rec)
D=pd.DataFrame(rows);print(len(D),'at',D.groupby(['gun','h','k']).ngroups,'koşu; son oranın yarıştan kaç dk önce yayınlandığı (medyan) %.1f'%D.tson.median())
for m in(30,15,10,5,3):
    r=(D[f'o{m}']/D.son).dropna();print(f' T-{m}: oran/son medyan {r.median():.3f}  n={len(r)}')
for m in(15,10,5,3):
    c=f'o{m}';x=D[(D.pj*D[c])>=1.2].dropna(subset=[c]);print(f'kural p×oran(T-{m})≥1.2: n={len(x)} kazanan={int((x.sira==1).sum())} ROI={((x.sira==1)*x[c]).mean():.3f}')
x=D[(D.pj*D.son)>=1.2];print(f'kural p×son≥1.2: n={len(x)} ROI={((x.sira==1)*x.son).mean():.3f}')
D.to_csv('/tmp/claude-0/sabit_zaman.csv',index=False)
