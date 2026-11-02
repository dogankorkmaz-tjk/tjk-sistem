import pandas as pd,numpy as np,glob,json
def h3(p,i):
    n=len(p);t=p[i]
    for j in range(n):
        if j==i: continue
        t+=p[j]*p[i]/(1-p[j])
        for k in range(n):
            if k in(i,j): continue
            t+=p[j]*p[k]/(1-p[j])*p[i]/(1-p[j]-p[k])
    return t
def ozet(R,ad):
    R=pd.DataFrame(R);print(f"{ad}: n={len(R)} ilk3 gözlenen {R.i3.mean():.3f} beklenen(piyasa) {R.e3.mean():.3f} fark {R.i3.mean()-R.e3.mean():+.3f} SE≈{np.sqrt((R.e3*(1-R.e3)).sum())/len(R):.3f} | ort. sıra yüzdesi {R.pct.mean():.3f} (beklenen {R.epct.mean():.3f}) | kazanma {R.w.mean():.3f} beklenen {R.ew.mean():.3f}")
# geçmiş
d=pd.read_pickle(glob.glob('/tmp/claude-0/**/oos_p.pkl',recursive=True)[0]);d=d[(d.p_piyasa>0)&(d.sira>0)].copy()
d['kid']=d.tarih.astype(str)+d.hipodrom.astype(str)+d.kosu.astype(str)
R=[]
for kid,g in d.groupby('kid'):
    if g.kazandi.sum()!=1 or len(g)<5: continue
    pm=(g.p_piyasa/g.p_piyasa.sum()).values;pj=(g.p_Jason/g.p_Jason.sum()).values
    for i in np.where((pj>=.06)&(pj/pm>=1.3))[0]:
        n=len(g);s=g.sira.values[i];R.append(dict(i3=int(s<=3),e3=h3(pm,i),pct=(s-1)/(n-1),epct=0,w=int(s==1),ew=pm[i]))
for r in R: r['epct']=np.nan
ozet(R,'geçmiş tüyo kuralı');
