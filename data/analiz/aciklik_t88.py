import pandas as pd,numpy as np,glob
d=pd.read_pickle(glob.glob('/tmp/claude-0/**/oos_p.pkl',recursive=True)[0])
d['gun']=d.tarih.astype(str).str[:10]
d['kid']=d.tarih.astype(str)+d.hipodrom.astype(str)+d.kosu.astype(str)
d=d[d.p_piyasa>0].copy()
for c in('p_piyasa','p_Jason'): d[c]=d[c]/d.groupby('kid')[c].transform('sum')
W=d[d.kazandi==1].drop_duplicates('kid')
mx=d.groupby('kid').p_piyasa.max().rename('mx')
W=W.merge(mx,on='kid')
W=W[W.kid.isin(d.groupby('kid').kazandi.sum().loc[lambda s:s==1].index)]
W['dn']=-np.log(W.p_Jason)+np.log(W.p_piyasa)  # negatif = Jason iyi
q=W.mx.quantile([1/3,2/3]).values
W['g']=np.where(W.mx<q[0],'acik',np.where(W.mx<q[1],'orta','kapali'))
W['yil']=W.gun.str[:4]
rng=np.random.default_rng(1);gun=W.gun.values;ug=np.unique(gun)
idx={g:np.where(gun==g)[0] for g in ug}
def boot(f,B=2000):
    r=[]
    for _ in range(B):
        s=rng.choice(ug,len(ug));i=np.concatenate([idx[g] for g in s]);r.append(f(W.iloc[i]))
    return np.percentile(r,[2.5,97.5])
out=[f"kesimler {q.round(3)}, koşu {len(W)}"]
for g in['acik','orta','kapali']:
    s=W[W.g==g];out.append(f"{g}: n={len(s)} dNLL={s.dn.mean():+.4f} GA{boot(lambda x:x[x.g==g].dn.mean()).round(4)}")
f=lambda x:x[x.g=='acik'].dn.mean()-x[x.g=='kapali'].dn.mean()
out.append(f"fark(acik-kapali)={f(W):+.4f} GA{boot(f).round(4)}")
for y in sorted(W.yil.unique()):
    s=W[W.yil==y];out.append(f"  {y}: acik {s[s.g=='acik'].dn.mean():+.4f} kapali {s[s.g=='kapali'].dn.mean():+.4f} fark {s[s.g=='acik'].dn.mean()-s[s.g=='kapali'].dn.mean():+.4f}")
L=d[d.ganyan>=10].copy()
out.append(f"uzun at (ganyan>=10) n={len(L)} gozlenen {L.kazandi.mean():.4f} p_piyasa {L.p_piyasa.mean():.4f} p_Jason {L.p_Jason.mean():.4f}")
S=L[L.p_Jason/L.p_piyasa>1.2].copy();S['get']=S.kazandi*S.ganyan
out.append(f"p_J/p_m>1.2 uzun: n={len(S)} gozlenen {S.kazandi.mean():.4f} ROI {S['get'].mean():.3f}")
sg=S.gun.values;ug2=np.unique(sg);i2={g:np.where(sg==g)[0] for g in ug2}
r=[S['get'].values[np.concatenate([i2[g] for g in rng.choice(ug2,len(ug2))])].mean() for _ in range(2000)]
out.append(f"  ROI GA {np.percentile(r,[2.5,97.5]).round(3)}")
open('data/analiz/aciklik_t88_sonuc.txt','w').write('\n'.join(out));print('\n'.join(out))
