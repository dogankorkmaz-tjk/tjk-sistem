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
for ad,(son,b,e) in {"2025":("2024-12-31","2025-01-01","2025-12-31"),"2026":("2025-12-31","2026-01-01","2026-12-31")}.items():
    tr=d[d.tarih<=son];te=d[(d.tarih>=b)&(d.tarih<=e)].copy()
    a=_fit(tr,f2);c=_fit(tr,f3)
    te["p0"]=skor(te,a[0],a[1],a[2],f2);te["p1"]=skor(te,c[0],c[1],c[2],f3)
    w=te[te.kazandi==1].copy();w["dl"]=np.log(w.p1.clip(1e-9))-np.log(w.p0.clip(1e-9))
    print(ad,"katsayı kfz,kfz_pos (std):",np.round(c[0][-2:],3))
    for ad2,g in (("tüm",w),("handikap",w[w.hv])):
        t=g.groupby("tarih").dl.agg(['sum','size']);rng=np.random.default_rng(3);o=[]
        for _ in range(3000):
            i=rng.integers(0,len(t),len(t));o.append(t['sum'].values[i].sum()/t['size'].values[i].sum())
        print(f"{ad} {ad2}: koşu {len(g)} | Δ loglik {g.dl.mean():+.5f} nats/koşu GA95 {np.percentile(o,[2.5,97.5]).round(5)}",flush=True)
