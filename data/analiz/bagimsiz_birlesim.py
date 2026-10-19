"""Birleşim testi (ön kayıt 19 Ekim 2026 12:20). Kullanım: python3 -I bagimsiz_jason.py"""
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
P={}
for ad,(son_tr,bas_,bit) in {"2025":("2024-12-31","2025-01-01","2025-12-31"),"2026":("2025-12-31","2026-01-01","2026-12-31")}.items():
    tr=d[d.tarih<=son_tr].copy();te=d[(d.tarih>=bas_)&(d.tarih<=bit)].copy();trF=tr.copy();trF["lp"]=0.0
    thF,muF,sdF,_=_fit(trF,feat);thC,muC,sdC,_=_fit(tr,feat+["f_lp2"])
    te["pF"]=skor(te,thF,muF,sdF,feat,False);te["pC"]=skor(te,thC,muC,sdC,feat+["f_lp2"],True)
    G=HistGradientBoostingClassifier(max_iter=200,random_state=0).fit(tr[feat].fillna(0),(pd.to_numeric(tr.sira,errors='coerce').fillna(99)<=5).astype(int));te["pG"]=G.predict_proba(te[feat].fillna(0))[:,1]
    te["prk"]=te.groupby("rid").p_piyasa.rank(ascending=False,method="first");te["ilk5"]=(pd.to_numeric(te.sira,errors="coerce").fillna(99)<=5).astype(int)
    P[ad]=te[te.prk>=6].copy();print(ad,"piyasa-dışı satır",len(P[ad]),flush=True)
def auc_tablo(od,col_fn):
    rows=[]
    for _,g in od.groupby("rid"):
        sc=col_fn(g);y=g.ilk5.values;pos=sc[y==1];neg=sc[y==0]
        if len(pos)==0 or len(neg)==0: continue
        rows.append((g.tarih.iloc[0],((pos[:,None]>neg[None,:]).sum()+0.5*(pos[:,None]==neg[None,:]).sum()),len(pos)*len(neg)))
    return pd.DataFrame(rows,columns=["t","a","n"])
BET=[0,0.1,0.2,0.3,0.5,0.75,1.0]
for X in ("pF","pG"):
    f=lambda b:(lambda g:np.log(g.pC.values.clip(1e-9))+b*np.log(g[X].values.clip(1e-9)))
    cur={b:auc_tablo(P["2025"],f(b)) for b in BET};ac={b:cur[b].a.sum()/cur[b].n.sum() for b in BET}
    print(X,"2025 AUC(β):",{b:round(v,4) for b,v in ac.items()})
    bs=max(ac,key=ac.get);print(X,"seçilen β (2025):",bs)
    A0=auc_tablo(P["2026"],f(0));A1=auc_tablo(P["2026"],f(bs));m=A0.merge(A1,on="t",suffixes=("0","1"))
    sg=m.groupby("t")[["a0","a1","n0"]].sum();tot=sg.n0.sum();rng=np.random.default_rng(5);o=[]
    for _ in range(3000):
        t=sg.iloc[rng.integers(0,len(sg),len(sg))];o.append((t.a1.sum()-t.a0.sum())/t.n0.sum())
    print(f"{X} 2026: AUC Jason {sg.a0.sum()/tot:.4f} | birleşik (β={bs}) {sg.a1.sum()/tot:.4f} | fark {(sg.a1.sum()-sg.a0.sum())/tot:+.4f} GA97,5 {np.percentile(o,[1.25,98.75]).round(4)}",flush=True)
