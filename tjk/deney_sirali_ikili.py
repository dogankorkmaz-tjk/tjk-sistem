import sys,glob as gl,os; sys.path.insert(0,'/home/claude/tjk-sistem')
import numpy as np,pandas as pd
from tjk import deney_uzman as U
G=U.G;O=U.O
d,M=U.veri()
feat1=list(M["feat"])+G.EK+G.LPEK
od0=pd.concat([pd.read_csv(f) for f in sorted(gl.glob(os.path.join(U.KOK,"data","odeme","*.csv.gz")))],ignore_index=True)
od0=od0[od0.tur=="SIRALI İKİLİ"]
def ordered(E):
    a=E[0]/E[0].sum();b=E[1];B=b.sum()
    P=a[:,None]*b[None,:]/(B-b)[:,None];np.fill_diagonal(P,0);return P
def w(S):return np.exp(S-S.max(axis=1,keepdims=True))
def calis(egit_son,bas,bit):
    egit=d[d.tarih<=egit_son];sinav=d[(d.tarih>bas)&(d.tarih<=bit)&d.sira.notna()&d.lp.notna()].copy()
    th,mu,sd,_=G._fit(U.asama_verisi(egit,1),feat1,M.get("lam",100.0))
    sinav["sj"]=U.skorla(sinav,feat1,th,mu,sd)
    od=od0[(od0.tarih>bas)&(od0.tarih<=bit)]
    ok={(r.tarih,r.hipodrom,r.kosu):r.kombo.split("/") for r in od.itertuples() if all(v.strip().isdigit() for v in r.kombo.split("/"))}
    ok2={}
    for r in od.itertuples():
        ok2.setdefault((r.tarih,r.hipodrom,r.kosu),[]).append((r.kombo.split("/"),float(r.tutar)))
    rows=[]
    for (t,h,ks),g in sinav.groupby(O.K):
        if (t,h,ks) not in ok2 or len(g)<6 or len(g)>16:continue
        no=g.no.astype(int).astype(str).tolist();n=len(g)
        SJ=np.array([U.G_M[k]*g.sj.values for k in range(5)]);SP=np.array([U.G_P[k]*g.lp.values for k in range(5)])
        Pj=ordered(w(SJ));Pm=ordered(w(SP))
        win={}
        for kb,tut in ok2[(t,h,ks)]:
            if all(x in no for x in kb): win[(no.index(kb[0]),no.index(kb[1]))]=win.get((no.index(kb[0]),no.index(kb[1])),0)+tut
        for i in range(n):
            for j in range(n):
                if i==j:continue
                rows.append((t,(t,h,ks),Pj[i,j]/Pm[i,j],Pj[i,j],Pm[i,j],win.get((i,j),0.0)))
    return pd.DataFrame(rows,columns="t kosu oran pj pm win".split())
rng=np.random.default_rng(2)
def boot(y):
    g=y.groupby('kosu').agg(w=('win','sum'),c=('win','size'));w_=g.w.values;c=g.c.values;i=np.arange(len(g));b=[w_[s].sum()/c[s].sum() for s in (rng.choice(i,len(i)) for _ in range(300))];return np.percentile(b,[5,95])
for ad,args in (("2026 (Jason ≤2025)",("2025-12-31","2025-12-31","2026-12-31")),("2025 (Jason ≤2024)",("2024-12-31","2024-12-31","2025-12-31"))):
    R=calis(*args);nk=R.kosu.nunique();print("==",ad,"koşu",nk,"tarih",R.t.min(),R.t.max())
    top=R[R.groupby('kosu').pj.transform('max')==R.pj];print(" Jason'ın en yüksek ihtimalli sıralı çifti: isabet",int((top.win>0).sum()),"ROI %.3f"%(top.win.sum()/len(top)))
    print(" hepsi ROI %.3f"%(R.win.sum()/len(R)))
    for pm in (0,.005,.01,.02):
        for r in (1.0,1.1,1.25,1.5):
            y=R[(R.oran>=r)&(R.pm>=pm)]
            if y.kosu.nunique()<100 or (y.win>0).sum()<40:continue
            lo,hi=boot(y);print(f"  piyasa≥{pm} oran≥{r}: bilet/koşu {len(y)/nk:.1f} isabet {(y.win>0).sum()} ROI {y.win.sum()/len(y):.3f} ({lo:.2f}-{hi:.2f}) Jason bek {y.pj.sum():.0f} piyasa bek {y.pm.sum():.0f}")
