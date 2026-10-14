"""Hibrit (1-2 Jason, 3-5 Jason-S) olabilirlik testi. Kullanım: python3 -I data/analiz/hibrit_testi.py <scratch>"""
import sys,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
exec(open('/home/claude/tjk-sistem/data/analiz/siralama_ps_uret.py').read().split('d["q"]=')[0])
d["q"]=pd.PeriodIndex(pd.to_datetime(d.tarih),freq="Q").astype(str)
GJ=np.array([1,0.80,0.69,0.69,0.69])
res=[]
for q in [x for x in sorted(d.q.unique()) if x>="2025Q1"]:
    te=d[d.q==q].copy();tr=d[d.tarih<te.tarih.min()]
    if tr.rid.nunique()<5000 or te.rid.nunique()<50: continue
    thA,muA,sdA,_=_fit(tr.assign(kazandi=(tr.sr==1).astype(float)),feat,M.get("lam",100.0))
    thB,aB,muB,sdB=fit_s(tr,M.get("lam",100.0),thA,GM)
    te=te.sort_values(O.K+["no"]).reset_index(drop=True)
    X=te[feat]
    svA=thA[0]*te.lp.values+(((X-muA)/sdA).values)@thA[1:]
    svB=thB[0]*te.lp.values+(((X-muB)/sdB).values)@thB[1:]
    lj=ll_pos(te,svA,GJ);ls=ll_pos(te,svB,aB)
    rid=te.rid.unique()[:len(lj[0])]
    day=te.groupby("rid").tarih.first().values
    df=pd.DataFrame({"q":q,"day":day})
    for k in range(5): df[f"J{k+1}"]=lj[k];df[f"S{k+1}"]=ls[k]
    res.append(df);print(q,len(df),np.round(aB,2),flush=True)
R=pd.concat(res);R.to_pickle(sys.argv[1]+"/hibrit_ll.pkl")
rng=np.random.default_rng(7);days=R.day.unique()
def boot(col):
    g=R.groupby("day")[col].agg(["sum","count"]);out=[]
    for _ in range(2000):
        s=g.loc[rng.choice(g.index,len(g))];out.append(s["sum"].sum()/s["count"].sum())
    return np.percentile(out,[2.5,97.5])
for k in range(1,6):
    R[f"d{k}"]=R[f"S{k}"]-R[f"J{k}"]
    lo,hi=boot(f"d{k}");print(f"sıra {k}: Jason-S − Jason = {R[f'd{k}'].mean():+.4f} nats/koşu GA [{lo:+.4f},{hi:+.4f}] çeyrek+ {int((R.groupby('q')[f'd{k}'].mean()>0).sum())}/{R.q.nunique()}")
R["d12"]=R.d1+R.d2;lo,hi=boot("d12");print(f"sıra1+2: Jason-S − Jason = {R.d12.mean():+.4f} GA [{lo:+.4f},{hi:+.4f}]")
R["hib_vs_S"]=-R.d12;lo,hi=boot("hib_vs_S");print(f"HİBRİT − Jason-S (toplam) = {R.hib_vs_S.mean():+.4f} GA [{lo:+.4f},{hi:+.4f}]")
R["hib_vs_J"]=R.d3+R.d4+R.d5;lo,hi=boot("hib_vs_J");print(f"HİBRİT − Jason (toplam) = {R.hib_vs_J.mean():+.4f} GA [{lo:+.4f},{hi:+.4f}]")
R["S_vs_J"]=R[[f"d{k}" for k in range(1,6)]].sum(axis=1);lo,hi=boot("S_vs_J");print(f"Jason-S − Jason (toplam 1-5) = {R.S_vs_J.mean():+.4f} GA [{lo:+.4f},{hi:+.4f}]")
