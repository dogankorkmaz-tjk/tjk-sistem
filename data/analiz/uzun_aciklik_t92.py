import pandas as pd,numpy as np,glob
d=pd.read_pickle(glob.glob('/tmp/claude-0/**/oos_p.pkl',recursive=True)[0])
d=d[(d.p_piyasa>0)&(d.ganyan>0)].copy()
d['kid']=d.tarih.astype(str)+d.hipodrom.astype(str)+d.kosu.astype(str);d['gun']=d.tarih.astype(str).str[:10];d['yil']=d.gun.str[:4]
for c in('p_piyasa','p_Jason'): d[c]=d[c]/d.groupby('kid')[c].transform('sum')
mx=d.groupby('kid').p_piyasa.max();d['mx']=d.kid.map(mx)
d['g']=np.where(d.mx<.277,'acik',np.where(d.mx<.373,'orta','kapali'))
S=d[(d.ganyan>=10)&(d.p_Jason/d.p_piyasa>1.2)].copy();S['get']=S.kazandi*S.ganyan
rng=np.random.default_rng(5)
def roi(x):
    if len(x)<20: return 'n<20'
    ug=x.gun.unique();ix=x.groupby('gun').indices;v=x['get'].values;r=[]
    for _ in range(2000): r.append(v[np.concatenate([ix[g] for g in rng.choice(ug,len(ug))])].mean())
    return f"n={len(x)} kazanan={int(x.kazandi.sum())} oran={x.kazandi.mean():.4f} ROI={v.mean():.3f} GA95{np.percentile(r,[2.5,97.5]).round(3)} GA99.2{np.percentile(r,[.4,99.6]).round(3)}"
out=['TÜM: '+roi(S)]
for g in['acik','orta','kapali']: out.append(f"{g}: "+roi(S[S.g==g]))
for y in sorted(S.yil.unique()): out.append(f"yıl {y}: "+roi(S[S.yil==y]))
for y in sorted(S.yil.unique()): out.append(f"açık {y}: "+roi(S[(S.g=='acik')&(S.yil==y)]))
open('data/analiz/uzun_aciklik_t92_sonuc.txt','w').write('\n'.join(out));print('\n'.join(out))
