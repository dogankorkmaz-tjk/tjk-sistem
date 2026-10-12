import sys,json; sys.path.insert(0,'/home/claude/tjk-sistem')
import numpy as np,pandas as pd
from scipy.optimize import minimize
from tjk import deney_uzman as U
G=U.G;O=U.O
d,M=U.veri()
feat1=list(M["feat"])+G.EK+G.LPEK
egit=d[d.tarih<='2025-12-31']
th,mu,sd,_=G._fit(U.asama_verisi(egit,1),feat1,M.get("lam",100.0))
S=d[(d.tarih>='2026-08-15')&d.sira.notna()&d.lp.notna()&(d.kosmadi==False)].copy()
S["sj"]=U.skorla(S,feat1,th,mu,sd)
I=pd.read_csv('/home/claude/tjk-sistem/data/idman.csv.gz')
I["at"]=I["at"].astype(str).str.strip().str.upper(); S["atn"]=S["at"].astype(str).str.strip().str.upper()
I["itd"]=pd.to_datetime(I.it)
# gün bazında m400 medyanı (göreli hız)
I["m400_rel"]=I.m400-I.groupby(["it","hip"]).m400.transform("median")
I["hizli"]=I.durum.isin(["Ç","HÇ","ÇR"]).astype(float)
gr={a:x.sort_values("itd") for a,x in I.groupby("at")}
print("idman at sayısı",len(gr),"eşleşen yarış atı oranı %.3f"%S.atn.isin(gr).mean())
rows=[]
for r in S.itertuples():
    x=gr.get(r.atn);t=pd.Timestamp(r.tarih)
    f=dict(say30=0,gun=30.0,rel_son=0.0,rel_en=0.0,hizli_oran=0.0,yok=1.0)
    if x is not None:
        y=x[(x.itd<t)&(x.itd>=t-pd.Timedelta(days=30))]
        if len(y):
            f["say30"]=len(y);f["gun"]=float((t-y.itd.max()).days);f["yok"]=0.0
            rm=y.m400_rel.dropna()
            if len(rm):f["rel_son"]=float(rm.iloc[-1]);f["rel_en"]=float(rm.min())
            f["hizli_oran"]=float(y.hizli.mean())
    rows.append(f)
F=pd.DataFrame(rows,index=S.index);S=pd.concat([S,F],axis=1)
S["rel_son"]=S.rel_son.clip(-4,4);S["rel_en"]=S.rel_en.clip(-4,4)
cols=["say30","gun","rel_son","rel_en","hizli_oran","yok"]
print(S.groupby("yok").size())
S["tr"]=S.tarih<='2026-09-20'
K=["tarih","hipodrom","kosu"]
grp=[(k,g) for k,g in S.groupby(K) if len(g)>=6 and (g.sira==1).sum()==1]
def mk(sel):
    L=[]
    for k,g in grp:
        if g.tr.iloc[0]==sel:
            # ganyan sütunu yoksa bile iç kontrol
            L.append((g.sj.values-np.log(np.exp(g.sj.values).sum()),g[cols].values,int(np.where(g.sira.values==1)[0][0]),g.sj.values))
    return L
TR,TE=mk(True),mk(False);print("eğitim koşu",len(TR),"sınama koşu",len(TE))
mu_=np.vstack([x[1] for x in TR]).mean(0);sd_=np.vstack([x[1] for x in TR]).std(0)+1e-9
def nll(b,L,lam):
    t=0
    for s,X,w,_ in L:
        z=s+((X-mu_)/sd_)@b; z=z-z.max(); t-=z[w]-np.log(np.exp(z).sum())
    return t/len(L)+lam*(b@b)
def fit(L,lam):
    return minimize(nll,np.zeros(len(cols)),args=(L,lam),method="L-BFGS-B").x
def kay(b,L):
    out=[]
    for s,X,w,sj in L:
        z0=sj-sj.max();z0=z0-np.log(np.exp(z0).sum())
        z=sj+((X-mu_)/sd_)@b;z=z-z.max();z=z-np.log(np.exp(z).sum())
        out.append(z[w]-z0[w])
    return np.array(out)
for lam in (0.0,0.01,0.05):
    b=fit(TR,lam);g=kay(b,TE)
    print("lam",lam,"β",dict(zip(cols,np.round(b,3))),"sınama kazancı/koşu %.4f ± %.4f (z=%.2f)"%(g.mean(),g.std()/np.sqrt(len(g)),g.mean()/(g.std()/np.sqrt(len(g)))))
# tek özellik
for j,c in enumerate(cols):
    TRj=[(s,X[:,[j]],w,sj) for s,X,w,sj in TR];TEj=[(s,X[:,[j]],w,sj) for s,X,w,sj in TE]
    m0,s0=mu_[j],sd_[j]
    def n1(b):
        t=0
        for s,X,w,_ in TRj:
            z=s+((X[:,0]-m0)/s0)*b[0];z=z-z.max();t-=z[w]-np.log(np.exp(z).sum())
        return t/len(TRj)
    b=minimize(n1,[0.0],method="L-BFGS-B").x
    gg=[]
    for s,X,w,sj in TEj:
        z0=sj-sj.max();z0=z0-np.log(np.exp(z0).sum());z=sj+((X[:,0]-m0)/s0)*b[0];z=z-z.max();z=z-np.log(np.exp(z).sum());gg.append(z[w]-z0[w])
    gg=np.array(gg);print(c,"β=%.3f"%b[0],"kazanç %.4f ± %.4f"%(gg.mean(),gg.std()/np.sqrt(len(gg))))
