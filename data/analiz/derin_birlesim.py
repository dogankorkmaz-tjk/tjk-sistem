"""Derin sıralara birleşim Jason-D (ön kayıt 19 Ekim 2026 13:30). Kullanım: python3 -I bagimsiz_jason.py"""
import sys,os,numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'));sys.path.insert(0,R)
import glob
from tjk import ortak as O, mesafe as MS, besli
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
GM=np.array([1,0.80,0.69,0.69,0.69])
def pl_ll(vecs,sr):
    o=[int(np.where(sr==j)[0][0]) for j in range(1,6)];used=[];ll=0.0
    for k in range(5):
        W=np.maximum(vecs[k],1e-9)**GM[k];den=W.sum()-sum(W[u] for u in used);ll+=np.log(W[o[k]]/den);used.append(o[k])
    return ll
def boot(g,x,B=3000,seed=11):
    t_=pd.DataFrame({"g":g,"x":x}).groupby("g").x.agg(["sum","size"]);rng=np.random.default_rng(seed);o=[]
    for _ in range(B):
        i=rng.integers(0,len(t_),len(t_));o.append(t_["sum"].values[i].sum()/t_["size"].values[i].sum())
    return np.percentile(o,[2.5,97.5])
O_=pd.concat([pd.read_csv(f) for f in glob.glob(R+'/data/odeme/*.csv.gz')]);O_=O_[O_.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu']);O_['tarih']=O_.tarih.astype(str)
parse=lambda k:[set(int(x) for x in s.split(',')) for s in str(k).split('/')]
CUR=[None]
def _Wd(p,G):
    W=[[max(v,1e-9)**g for v in vec] for vec,g in zip(CUR[0],G)];return W,[sum(w) for w in W]
_Worig=besli._W
YIL={"2024":("2023-12-31","2024-01-01","2024-12-31"),"2025":("2024-12-31","2025-01-01","2025-12-31"),"2026":("2025-12-31","2026-01-01","2026-12-31")}
for ad,(son_tr,bas_,bit) in YIL.items():
    tr=d[d.tarih<=son_tr].copy();te=d[(d.tarih>=bas_)&(d.tarih<=bit)].copy()
    FY=[f for f in feat if tr[f].std(ddof=0)>1e-9]   # 2023 eğitiminde sabit kalan özellikler atılır (teknik düzeltme, tasarım aynı)
    thC,muC,sdC,_=_fit(tr,FY+["f_lp2"]);te["pC"]=skor(te,thC,muC,sdC,FY+["f_lp2"],True)
    G=HistGradientBoostingClassifier(max_iter=200,random_state=0).fit(tr[FY].fillna(0),(pd.to_numeric(tr.sira,errors='coerce').fillna(99)<=5).astype(int));te["pG"]=G.predict_proba(te[FY].fillna(0))[:,1]
    s=np.log(te.pC.clip(1e-9))+0.5*np.log(te.pG.clip(1e-9));s=s-s.groupby(te.rid.values).transform("max");e=np.exp(s);te["pB"]=e/e.groupby(te.rid.values).transform("sum")
    te["sr"]=pd.to_numeric(te.sira,errors="coerce").fillna(0);rows=[]
    for k,g in te.groupby(O.K):
        if not all((g.sr==j).sum()==1 for j in range(1,6)): continue
        sr=g.sr.values;pc=g.pC.values;pb=g.pB.values
        rows.append((g.tarih.iloc[0],pl_ll([pc]*5,sr),pl_ll([pb]*5,sr),pl_ll([pc,pc,pb,pb,pb],sr)))
    Z=pd.DataFrame(rows,columns=["t","c","b","d"])
    for ad2,col in (("D (derin)","d"),("B (tüm sıralar)","b")):
        x=(Z[col]-Z.c).values;lo,hi=boot(Z.t.values,x);print(f"== {ad} {'BİRİNCİL' if ad=='2024' and col=='d' else 'betimleyici'} PL {ad2} − Jason: {x.mean():+.4f} nats/koşu GA [{lo:+.4f},{hi:+.4f}] | koşu {len(Z)}",flush=True)
    if ad=="2024": continue
    Od=O_[(O_.tarih>=bas_)&(O_.tarih<=bit)];TG={k:g for k,g in te.groupby(O.K)};rows=[]
    for r in Od.to_dict("records"):
        g=TG.get((r["tarih"],r["hipodrom"],r["kosu"]))
        if g is None or len(g)<5: continue
        g=g.sort_values("no");nos=g.no.tolist();devir=str(r["tur"]).endswith("DEVİR");win=None if devir else parse(r["kombo"])
        pc=g.pC.values.astype(float);pc=list(pc/pc.sum());pb=g.pB.values.astype(float);pb=list(pb/pb.sum())
        for ad2 in ("C","D"):
            if ad2=="C": besli._W=_Worig
            else: besli._W=_Wd;CUR[0]=[pc,pc,pb,pb,pb]
            kp=besli.kupon_g(pc,150,list(besli.G_M));besli._W=_Worig
            if not kp: continue
            sets,pr=kp;cost=besli.gecerli_say(sets)*besli.BIRIM;hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
            rows.append((r["tarih"],r["hipodrom"],r["kosu"],ad2,cost,hit,float(r["tutar"]) if hit else 0.0,pr))
    Dk=pd.DataFrame(rows,columns=["t","h","k","m","cost","hit","pay","pr"]);a=Dk[Dk.m=="C"];b=Dk[Dk.m=="D"];m=a.merge(b,on=["t","h","k"],suffixes=("_C","_D"))
    rng=np.random.default_rng(5);bs=[]
    for _ in range(3000):
        ix=rng.integers(0,len(m),len(m));q=m.iloc[ix];bs.append(q.pay_D.sum()/q.cost_D.sum()-q.pay_C.sum()/q.cost_C.sum())
    print(f"   {ad} KUPON B=150: koşu {len(m)} | C tutan {int(m.hit_C.sum())} ROI {m.pay_C.sum()/m.cost_C.sum():.3f} beklenen %{m.pr_C.mean()*100:.1f} | D tutan {int(m.hit_D.sum())} ROI {m.pay_D.sum()/m.cost_D.sum():.3f} beklenen %{m.pr_D.mean()*100:.1f} | ROI farkı {m.pay_D.sum()/m.cost_D.sum()-m.pay_C.sum()/m.cost_C.sum():+.3f} GA {np.percentile(bs,[2.5,97.5]).round(3)}",flush=True)
