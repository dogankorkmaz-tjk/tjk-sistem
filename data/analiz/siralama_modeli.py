"""Jason-S testi (ön kayıt: hipotez_defteri.md 14 Ekim 2026 01:20). Çalıştır: cd /home/claude/tjk-sistem && python3 -m data.analiz... yerine: python3 data/analiz/siralama_modeli.py"""
import sys,os,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
from scipy.optimize import minimize
from tjk import ortak as O, mesafe as MS
from tjk.ozellik import hazirla
from tjk.golge import _fit,_oku,EK,LPEK
from tjk.calistir import yukle_model
GM=np.array([1,0.80,0.69,0.69,0.69])
M=yukle_model()
d=MS.ekle(hazirla(_oku("temiz"),_oku("program"),M));d["f_lp2"]=np.log(d.p_piyasa.clip(lower=1e-6))**2
d=d[d.temiz&d.kazandi.notna()&d.lp.notna()].copy();d["tarih"]=d.tarih.astype(str)
feat=M["feat"]+EK+LPEK
d=d.sort_values(O.K+["no"]).reset_index(drop=True);d["rid"]=d.groupby(O.K).ngroup()
# ilk 5 çözülmüş koşular
s=pd.to_numeric(d.sira,errors='coerce').fillna(0)
d["sr"]=s
ok=d.groupby("rid").sr.apply(lambda x:all((x==k).sum()==1 for k in range(1,6)))
d=d[d.rid.map(ok)].copy().reset_index(drop=True);d["rid"]=d.groupby(O.K).ngroup()
print("çözülmüş koşu",d.rid.nunique(),flush=True)
def blok(df):
    r=df.rid.values;st=np.r_[0,np.nonzero(np.diff(r))[0]+1];n=len(df);seg=np.repeat(np.arange(len(st)),np.diff(np.r_[st,n]));return st,seg
def maskler(df):
    sr=df.sr.values;return [((sr>=k)|(sr<=0)) for k in range(1,6)],[(sr==k) for k in range(1,6)]
def adimlar(sv,a,st,seg,mk):
    out=[]
    for k in range(5):
        z=a[k]*sv;m=np.where(mk[k],z,-1e18);mx=np.maximum.reduceat(m,st);e=np.exp(m-mx[seg])*mk[k];Z=np.add.reduceat(e,st);p=e/Z[seg];out.append((p,Z,mx))
    return out
def ll_pos(df,sv,a):
    st,seg=blok(df);mk,ch=maskler(df);ad=adimlar(sv,a,st,seg,mk);res=[]
    for k in range(5):
        p=ad[k][0];lp_=np.log(np.maximum(p[ch[k]],1e-300));res.append(lp_)   # koşu başına bir eleman (sıra k atı), rid sırasıyla
    return res
def fit_s(tr,lam,th0,a0):
    X0=tr[feat];mu,sd=X0.mean(),X0.std(ddof=0);X=((X0-mu)/sd).values;lp=tr.lp.values
    st,seg=blok(tr);mk,ch=maskler(tr);nf=X.shape[1]
    def f(par):
        w0,w,a=par[0],par[1:1+nf],np.r_[1.0,par[1+nf:]]
        sv=w0*lp+X@w;ll=0.0;gs=np.zeros(len(sv));ga=np.zeros(4)
        for k in range(5):
            z=a[k]*sv;m=np.where(mk[k],z,-1e18);mx=np.maximum.reduceat(m,st);e=np.exp(m-mx[seg])*mk[k];Z=np.add.reduceat(e,st);p=e/Z[seg]
            ll+=(z[ch[k]]).sum()-(np.log(Z)+mx).sum()
            g=ch[k].astype(float)-p;gs+=a[k]*g
            if k>0: ga[k-1]=(sv*g).sum()
        gr=-np.r_[(gs*lp).sum(),X.T@gs,ga];gr[1:1+nf]+=lam*w
        return -ll+0.5*lam*(w@w),gr
    p0=np.r_[th0[0],th0[1:],a0[1:]]
    r=minimize(f,p0,jac=True,method="L-BFGS-B",options={"maxiter":300})
    return r.x[:1+nf],np.r_[1.0,r.x[1+nf:]],mu,sd
d["q"]=pd.PeriodIndex(pd.to_datetime(d.tarih),freq="Q").astype(str)
rows=[]
for q in [x for x in sorted(d.q.unique()) if x>="2025Q1"]:
    te=d[d.q==q].copy();tr=d[d.tarih<te.tarih.min()]
    if tr.rid.nunique()<5000 or te.rid.nunique()<50: continue
    thA,muA,sdA,_=_fit(tr.assign(kazandi=(tr.sr==1).astype(float)),feat,M.get("lam",100.0))
    thB,aB,muB,sdB=fit_s(tr,M.get("lam",100.0),thA,GM)
    te=te.sort_values(O.K+["no"]).reset_index(drop=True)
    svA=thA[0]*te.lp.values+(((te[feat]-muA)/sdA).values)@thA[1:]
    svB=thB[0]*te.lp.values+(((te[feat]-muB)/sdB).values)@thB[1:]
    A=ll_pos(te,svA,GM);B=ll_pos(te,svB,aB)
    dif=np.sum([B[k]-A[k] for k in range(1,5)],axis=0)
    print(q,"koşu",len(dif),"a=",np.round(aB,2),"kazanç %.4f nats/koşu"%dif.mean(),"| sıra bazında",[round(float((B[k]-A[k]).mean()),4) for k in range(1,5)],flush=True)
    rows.append(dif)
al=np.concatenate(rows);bs=np.random.default_rng(0).choice(al,(2000,len(al))).mean(1) if len(al)<20000 else np.array([np.random.default_rng(i).choice(al,len(al)).mean() for i in range(1000)])
print("TOPLAM koşu",len(al),"kazanç %.4f nats/koşu (CI %.4f..%.4f)"%(al.mean(),np.percentile(bs,2.5),np.percentile(bs,97.5)),"| pozitif fold",sum(r.mean()>0 for r in rows),"/",len(rows))
