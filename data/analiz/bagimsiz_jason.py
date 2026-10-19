"""Piyasadan bağımsız Jason (ön kayıt 19 Ekim 2026 11:35). Kullanım: python3 -I bagimsiz_jason.py"""
import sys,os,numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'));sys.path.insert(0,R)
from tjk import ortak as O, mesafe as MS
from tjk.ozellik import hazirla
from tjk.golge import _fit,_oku,EK
from tjk.calistir import yukle_model
M=yukle_model()
d=MS.ekle(hazirla(_oku("temiz"),_oku("program"),M));d["f_lp2"]=np.log(d.p_piyasa.clip(lower=1e-6))**2
d=d[d.temiz&d.kazandi.notna()&d.lp.notna()].copy();d["tarih"]=d.tarih.astype(str)
feat=M["feat"]+EK
d=d.sort_values(O.K+["no"]).reset_index(drop=True);d["rid"]=d.groupby(O.K).ngroup()
print("koşu",d.rid.nunique(),"| tarih",d.tarih.min(),d.tarih.max(),flush=True)
def skor(df,th,mu,sd,cols,use_lp):
    X=((df[cols]-mu)/sd).values;s=(th[0]*df.lp.values if use_lp else 0)+X@th[1:]
    s=pd.Series(s,index=df.index);s=s-s.groupby(df.rid.values).transform('max');e=np.exp(s);return (e/e.groupby(df.rid.values).transform('sum')).values
def boot(g,x,B=3000,seed=9):
    t=pd.DataFrame({'g':g,'x':x}).groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(seed);o=[];s=t['sum'].values;c=t['size'].values
    for _ in range(B):
        i=rng.integers(0,len(s),len(s));o.append(s[i].sum()/c[i].sum())
    return np.percentile(o,[2.5,97.5])
for ad,(son_tr,bas,bit) in {"2025":("2024-12-31","2025-01-01","2025-12-31"),"2026":("2025-12-31","2026-01-01","2026-12-31")}.items():
    tr=d[d.tarih<=son_tr].copy();te=d[(d.tarih>=bas)&(d.tarih<=bit)].copy()
    trF=tr.copy();trF["lp"]=0.0
    thF,muF,sdF,_=_fit(trF,feat);thC,muC,sdC,_=_fit(tr,feat+["f_lp2"])
    te["pF"]=skor(te,thF,muF,sdF,feat,False);te["pC"]=skor(te,thC,muC,sdC,feat+["f_lp2"],True);te["pM"]=te.p_piyasa/te.groupby("rid").p_piyasa.transform("sum")
    W=te[te.kazandi==1]
    # --- BİRİNCİL: piyasa-dışı (piyasa sırası >=6) atlar arasında ilk-5 ayırma AUC'si
    G=HistGradientBoostingClassifier(max_iter=200,random_state=0).fit(tr[feat].fillna(0),(pd.to_numeric(tr.sira,errors='coerce').fillna(99)<=5).astype(int));te["pG"]=G.predict_proba(te[feat].fillna(0))[:,1]
    te["prk"]=te.groupby("rid").p_piyasa.rank(ascending=False,method="first");te["ilk5"]=(pd.to_numeric(te.sira,errors="coerce").fillna(99)<=5).astype(int);OD=te[te.prk>=6]
    def cift(g,col):
        pos=g[g.ilk5==1][col].values;neg=g[g.ilk5==0][col].values
        if len(pos)==0 or len(neg)==0: return None
        return ((pos[:,None]>neg[None,:]).sum()+0.5*(pos[:,None]==neg[None,:]).sum(),len(pos)*len(neg))
    rows=[]
    for _,g in OD.groupby("rid"):
        a={c:cift(g,c) for c in ("pM","pC","pF","pG")}
        if a["pM"] is None: continue
        rows.append((g.tarih.iloc[0],a["pM"][1],*[a[c][0] for c in ("pM","pC","pF","pG")]))
    Rw=pd.DataFrame(rows,columns=["t","n","M","C","F","G"]);tot=Rw.n.sum()
    print(f"== {ad}: SÜRPRİZ AUC (piyasa-dışı atlar, {len(Rw)} koşu, {int(tot)} çift): "+" | ".join(f"{c} {Rw[c].sum()/tot:.4f}" for c in "MCFG"))
    sg=Rw.groupby("t")[list("MCFG")+["n"]].sum();rng=np.random.default_rng(5)
    for c in ("F","G"):
        o=[]
        for _ in range(3000):
            t=sg.iloc[rng.integers(0,len(sg),len(sg))];o.append((t[c].sum()-t["C"].sum())/t.n.sum())
        print(f"   {c} − Jason(C): {(Rw[c].sum()-Rw.C.sum())/tot:+.4f} GA97,5 {np.percentile(o,[1.25,98.75]).round(4)}  | {c} − piyasa: {(Rw[c].sum()-Rw.M.sum())/tot:+.4f}",flush=True)
    print(f"== {ad}: eğitim koşu {tr.rid.nunique()} sınama koşu {te.rid.nunique()}")
    for ad2,col in (("F (bağımsız)","pF"),("C (Jason)","pC")):
        x=(np.log(W[col])-np.log(W.pM)).values;lo,hi=boot(W.tarih.values,x);print(f"  {ad2:14s} − piyasa: {x.mean():+.4f} nats/koşu GA [{lo:+.4f},{hi:+.4f}]")
    # favori isabeti
    top=lambda col:te.loc[te.groupby("rid")[col].idxmax()].kazandi.mean()
    print(f"  en yüksek puanlı atın kazanma oranı: piyasa {top('pM'):.3f} | F {top('pF'):.3f} | Jason {top('pC'):.3f}")
    for k in (1.25,1.50):
        B=te[te.pF*te.ganyan>k].copy()
        if len(B)<30: print(f"  F ROI k={k}: bahis {len(B)} (az)");continue
        net=np.where(B.kazandi==1,B.ganyan,0.0);lo,hi=boot(B.tarih.values,net);print(f"  F ROI k={k:.2f}: bahis {len(B)} isabet {int(B.kazandi.sum())} ROI {net.mean():.3f} GA [{lo:.3f},{hi:.3f}]")
