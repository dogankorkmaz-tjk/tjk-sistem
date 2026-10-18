import sys,glob,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from tjk.golge import _oku
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
t=_oku("temiz"); t=t[t.tarih.astype(str)>="2025-01-01"].copy(); t["tarih"]=t.tarih.astype(str)
O=pd.concat([pd.read_csv(f) for f in glob.glob('data/odeme/*.csv.gz')]); O=O[O.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu'])
K=['tarih','hipodrom','kosu']
t=t.merge(O[K+['tutar','tur']],on=K,how='inner')
t["sira"]=pd.to_numeric(t.sira,errors='coerce')
rows=[]
for k,g in t.groupby(K):
    g=g[(~g.kosmadi.fillna(False).astype(bool))&g.p_piyasa.notna()]
    if len(g)<6: continue
    p=g.p_piyasa.values/g.p_piyasa.sum(); o=np.argsort(-p); top5=set(g.no.values[o[:5]])
    fin=g[(g.sira>=1)&(g.sira<=5)]
    if len(fin)<5: continue
    n_out=sum(n not in top5 for n in fin.no)
    ps=np.sort(p)[::-1]
    rows.append(dict(tarih=k[0],hip=k[1],kosu=k[2],n_at=len(g),p1=ps[0],p12=ps[0]/ps[1],m5=ps[:5].sum(),ent=-(p*np.log(p)).sum(),n_out=n_out,tutar=g.tutar.iloc[0],devir=str(g.tur.iloc[0]).endswith('DEVİR')))
D=pd.DataFrame(rows); print("koşu",len(D))
print("n_out dağılımı:",D.n_out.value_counts(normalize=True).sort_index().round(3).to_dict())
D["acik"]=(D.n_out>=1).astype(int)
print("n_out>=1 oranı",D.acik.mean().round(3))
D["nb"]=pd.cut(D.n_at,[0,8,10,12,14,30]); print(D.groupby("nb",observed=True).agg(n=("acik","size"),acik=("acik","mean"),out_ort=("n_out","mean")).round(3))
D["mb"]=pd.qcut(D.m5,5,duplicates='drop'); print(D.groupby("mb",observed=True).agg(n=("acik","size"),acik=("acik","mean"),out_ort=("n_out","mean")).round(3))
print("medyan ödeme (tutar) n_out'a göre:",D[~D.devir].groupby("n_out").tutar.median().round(0).to_dict(), D[~D.devir].groupby("n_out").size().to_dict())
F=["n_at","p1","p12","m5","ent"]
tr=D[D.tarih<"2026-01-01"]; te=D[D.tarih>="2026-01-01"].copy()
mu,sd=tr[F].mean(),tr[F].std()
m=LogisticRegression(C=1.0).fit((tr[F]-mu)/sd,tr.acik); te["s"]=m.predict_proba((te[F]-mu)/sd)[:,1]
auc=roc_auc_score(te.acik,te.s); rng=np.random.default_rng(1); gunler=te.tarih.unique(); aucs=[]
for _ in range(1000):
    gs=rng.choice(gunler,len(gunler)); x=pd.concat([te[te.tarih==g] for g in gs])
    if x.acik.nunique()==2: aucs.append(roc_auc_score(x.acik,x.s))
print("2026 sına: koşu",len(te),"AUC",round(auc,3),"GA",np.percentile(aucs,[2.5,97.5]).round(3), "taban",te.acik.mean().round(3))
te["q"]=pd.qcut(te.s,4,duplicates='drop'); print(te.groupby("q",observed=True).agg(n=("acik","size"),acik=("acik","mean"),out=("n_out","mean")).round(3))
print(dict(zip(F,m.coef_[0].round(2))))
