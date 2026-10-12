import pandas as pd,numpy as np,json,glob
R='/home/claude/tjk-sistem/'
A=json.load(open(R+'data/model_aday.json'));w0=A['w'][0];lp2=A['lp2_a']
rows=[]
for f in sorted(glob.glob(R+'data/agf_zaman/*.csv.gz')):
    d=pd.read_csv(f);t=f[-17:-7]
    g=json.load(open(R+f'docs/data/gun/{t}.json')) if glob.glob(R+f'docs/data/gun/{t}.json') else None
    if not g: continue
    z={}
    for h in g['hipodromlar']:
        for k in h['kosular']:
            for a in k['atlar']:
                if a.get('z2') is not None: z[(h['id'],k['kosu'],a['no'])]=a['z2']
    for (h,k),x in d.groupby(['hipodrom','kosu']):
        ts=sorted(x.saat.unique())
        if len(ts)<3: continue
        a0=x[x.saat==ts[0]].set_index('no').agf; a1=x[x.saat==ts[-1]].set_index('no').agf
        n=a0.index.intersection(a1.index)
        if len(n)<4: continue
        p0=a0[n]/a0[n].sum(); n=n[(a0[n]>0)&(a1[n]>0)]; p0=a0[n]/a0[n].sum(); p1=a1[n]/a1[n].sum()
        zz=pd.Series({i:z.get((h,k,i),np.nan) for i in n})
        if zz.isna().any(): continue
        lk=np.log(p0.clip(lower=1e-4)); s=w0*lk+lp2*lk**2+zz; pm=np.exp(s-s.max()); pm/=pm.sum()
        for i in n: rows.append((t,h,k,i,ts[0],ts[-1],np.log(pm[i]/p0[i]),np.log(p1[i]/p0[i]),p0[i]))
D=pd.DataFrame(rows,columns=['t','h','k','no','s0','s1','edge','drift','p0'])
print(len(D),'at',D.groupby(['t','h','k']).ngroups,'koşu')
D['r']=D.groupby(['t','h','k']).ngroup()
c=D.groupby('r').apply(lambda x:np.corrcoef(x.edge,x.drift)[0,1]).dropna()
print('koşu-içi korelasyon ort %.3f se %.3f'%(c.mean(),c.std()/len(c)**.5))
b=np.polyfit(D.edge,D.drift,1);print('eğim',b)
top=D[D.edge>=np.log(1.25)];print('edge>=1.25 atlar',len(top),'ort drift %.4f'%top.drift.mean(),' tümü %.4f'%D.drift.mean())
bs=[D[D.r.isin(np.random.choice(D.r.unique(),D.r.nunique()))].pipe(lambda x:x[x.edge>=np.log(1.25)].drift.mean()) for _ in range(300)];print('boot',np.percentile(bs,[2.5,97.5]).round(4))
neg=D[D.edge<=-np.log(1.25)];print('edge<=-1.25 ort drift %.4f n %d'%(neg.drift.mean(),len(neg)))
print('ort ilk-son süre', D.s0.iloc[0],D.s1.iloc[0])
