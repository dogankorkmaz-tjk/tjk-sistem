import sys,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk import ortak as O, mesafe as MS
from tjk.ozellik import hazirla
from tjk.golge import _fit,_oku,EK,LPEK
from tjk.calistir import yukle_model
from tjk.walkforward import skorla
M=yukle_model()
d=MS.ekle(hazirla(_oku("temiz"),_oku("program"),M))
d["f_lp2"]=np.log(d.p_piyasa.clip(lower=1e-6))**2
# kapı yanlılığı: (hipodrom,mesafe,pist,kapı grubu) için ÖNCEKİ günlerin ortalama bitiş artığı
rk=d.groupby(["tarih","hipodrom","kosu"]).p_piyasa.rank(ascending=False,method="first")
res=(((rk-1)/(d.n_at-1).clip(lower=1))-d.pct).clip(-1,1); res[d.yeni.values]=np.nan
d["_res"]=res.values
rel=(d.st-1)/(d.n_at-1).clip(lower=1)
d["kg"]=np.where(d.st<=3,"ic",np.where(rel>0.66,"dis","orta")).astype(object)
d["anah"]=d.hipodrom.astype(str)+"|"+d.mesafe.astype(str)+"|"+d.pist.astype(str)+"|"+d.kg
d["f_kapi"]=MS._onceki_ort(d,"anah","_res",30.0)
d.loc[d.mesafe.isna()|d.st.isna(),"f_kapi"]=0.0
d=d[d.temiz&d.kazandi.notna()&d.lp.notna()].copy()
d["tarih"]=d.tarih.astype(str);d["rid"]=d.groupby(O.K).ngroup()
feats={"Jason":M["feat"]+EK+LPEK,"Jason+kapi":M["feat"]+EK+LPEK+["f_kapi"]}
d["q"]=pd.PeriodIndex(pd.to_datetime(d.tarih),freq="Q").astype(str)
rows=[]
for k in [x for x in sorted(d.q.unique()) if x>="2024Q2"]:
    te0=d[d.q==k];tr=d[d.tarih<te0.tarih.min()]
    if tr.rid.nunique()<5000: continue
    te=te0.sort_values(O.K+["no"]).reset_index(drop=True);te["rid"]=te.groupby(O.K).ngroup()
    for ad,f in feats.items():
        th,mu,sd,nk=_fit(tr,f,M.get("lam",100.0));te["p_"+ad]=skorla(te,f,th,mu,sd)
        if ad=="Jason+kapi": print(k,"w_kapi",round(th[1+f.index("f_kapi")],4),flush=True)
    rows.append(te[te.kazandi==1][["tarih","hipodrom","kosu","p_piyasa","p_Jason","p_Jason+kapi"]])
W=pd.concat(rows)
a=np.log(W["p_Jason"])-np.log(W.p_piyasa);b=np.log(W["p_Jason+kapi"])-np.log(W.p_piyasa);df=b-a
print("n",len(W),"Jason %.4f  +kapi %.4f  fark %.4f se %.4f"%(a.mean(),b.mean(),df.mean(),df.std()/len(df)**.5))
g=df.groupby(W.tarih).mean();print("gün-bazlı fark %.4f se %.4f"%(g.mean(),g.std()/len(g)**.5))
