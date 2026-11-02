import pandas as pd,numpy as np
d=pd.read_pickle('/tmp/claude-0/agf_d.pkl')
d['kid']=d.tarih.astype(str)+d.hipodrom.astype(str)+d.kosu.astype(str);d['gun']=d.tarih.astype(str).str[:10]
d=d[(d.ganyan>0)&(d.a>0)].copy()
for c in('p_piyasa','p_Jason','a'): d[c]=d[c]/d.groupby('kid')[c].transform('sum')
mx=d.groupby('kid').p_piyasa.max();d['g']=np.where(d.kid.map(mx)<.277,'acik',np.where(d.kid.map(mx)<.373,'orta','kapali'))
rng=np.random.default_rng(2);ug=d.gun.unique();ix=d.groupby('gun').indices
def ci(S,fn,B=2000):
    r=[]
    for _ in range(B):
        s=rng.choice(ug,len(ug));i=np.concatenate([ix[g] for g in s]);r.append(fn(d.iloc[i],S))
    return np.percentile(r,[2.5,97.5]).round(3)
def oran(x,S,col='a'):
    y=x[S(x)];return y.kazandi.sum()/y[col].sum() if y[col].sum()>0 else np.nan
out=[f"ayak {d.kid.nunique()}, at {len(d)}"]
S={'>=7':lambda x:x.ganyan>=7,'7-10':lambda x:(x.ganyan>=7)&(x.ganyan<10),'10-15':lambda x:(x.ganyan>=10)&(x.ganyan<15),'>=15':lambda x:x.ganyan>=15}
for g in['acik','orta','kapali']: S['>=7 '+g]=(lambda g:lambda x:(x.ganyan>=7)&(x.g==g))(g)
for k,f in S.items():
    y=d[f(d)]
    out.append(f"{k}: n={len(y)} kazanan={int(y.kazandi.sum())} gözlenen/AGF={oran(d,f):.3f} GA{ci(f,lambda x,f:oran(x,f))} | /p_piyasa={oran(d,f,'p_piyasa'):.3f} | /p_Jason={oran(d,f,'p_Jason'):.3f}")
open('data/analiz/altili_uzun_t89_sonuc.txt','w').write('\n'.join(out));print('\n'.join(out))
