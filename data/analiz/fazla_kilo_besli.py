"""Ön kayıt 20 Ekim 2026 02:40. Kullanım: python3 -I data/analiz/fazla_kilo.py"""
import sys,os,numpy as np,pandas as pd
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'));sys.path.insert(0,R)
from tjk import ortak as O, mesafe as MS
from tjk.ozellik import hazirla
from tjk.golge import _fit,_oku,EK
from tjk.calistir import yukle_model
M=yukle_model()
d=MS.ekle(hazirla(_oku("temiz"),_oku("program"),M));d["f_lp2"]=np.log(d.p_piyasa.clip(lower=1e-6))**2
d=d[d.temiz&d.kazandi.notna()&d.lp.notna()].copy();d["tarih"]=d.tarih.astype(str)
d["hv"]=d.hnd_rel.notna()&(d.groupby(O.K).hnd_rel.transform(lambda x:x.notna().all()))
d["kfz"]=(d.f_kilo-0.5*d.hnd_rel).where(d.hv,0.0).fillna(0.0);d["kfz_pos"]=d.kfz.clip(lower=0)
feat=M["feat"]+EK;f2=feat+["f_lp2"];f3=f2+["kfz","kfz_pos"]
d=d.sort_values(O.K+["no"]).reset_index(drop=True);d["rid"]=d.groupby(O.K).ngroup()
print("koşu",d.rid.nunique(),"handikap koşu",d[d.hv].rid.nunique(),flush=True)
def skor(df,th,mu,sd,cols):
    X=((df[cols]-mu)/sd).values;s=th[0]*df.lp.values+X@th[1:];s=pd.Series(s,index=df.index);s=s-s.groupby(df.rid.values).transform('max');e=np.exp(s);return (e/e.groupby(df.rid.values).transform('sum')).values
G=np.array([1,0.80,0.69,0.69,0.69])
def pl(g,sc,K):
    # g: koşu df sıralı; sc: skor (ln p); ilk-K sıra log-olabilirliği
    o=g.assign(_s=sc).sort_values("sr");r=o[o.sr.between(1,K)]
    if len(r)<K: return np.nan
    s=g._s.values if "_s" in g else sc;ll=0;rest=list(range(len(o)));v=o._s.values;ix=[o.index.get_loc(i) for i in r.index]
    used=np.zeros(len(o),bool)
    for k in range(K):
        z=G[k]*v;m=np.where(used,-1e18,z).max();ll+=z[ix[k]]-(m+np.log(np.exp(np.where(used,-1e18,z)-m).sum()));used[ix[k]]=True
    return ll
d["sr"]=pd.to_numeric(d.sira,errors="coerce").fillna(0)
for ad,(son,b,e) in {"2025":("2024-12-31","2025-01-01","2025-12-31"),"2026":("2025-12-31","2026-01-01","2026-12-31")}.items():
    tr=d[d.tarih<=son];te=d[(d.tarih>=b)&(d.tarih<=e)].copy()
    a=_fit(tr,f2);c=_fit(tr,f3)
    te["s0"]=np.log(skor(te,a[0],a[1],a[2],f2).clip(1e-12));te["s1"]=np.log(skor(te,c[0],c[1],c[2],f3).clip(1e-12))
    rows=[]
    for _,g in te.groupby("rid"):
        if not all((g.sr==k).sum()==1 for k in range(1,6)): continue
        r={"t":g.tarih.iloc[0],"hv":g.hv.iloc[0]}
        for K in (3,5):
            r[f"d{K}"]=pl(g,g.s1.values,K)-pl(g,g.s0.values,K)
        rows.append(r)
    R=pd.DataFrame(rows)
    for ad2,x in (("tüm",R),("handikap",R[R.hv])):
        for K in (3,5):
            t=x.groupby("t")[f"d{K}"].agg(['sum','size']);rng=np.random.default_rng(3);o=[]
            for _ in range(3000):
                i=rng.integers(0,len(t),len(t));o.append(t['sum'].values[i].sum()/t['size'].values[i].sum())
            print(f"{ad} {ad2} ilk-{K}: koşu {len(x)} | Δ PL {x[f'd{K}'].mean():+.5f} GA95 {np.percentile(o,[2.5,97.5]).round(5)}",flush=True)
