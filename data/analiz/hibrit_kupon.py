"""Hibrit kupon geriye testi (ön kayıt 14 Ekim 2026 ~11:30). Jason / Jason-S / Hibrit(1-2 Jason, 3-5 Jason-S). Kullanım: python3 -I hibrit_kupon.py <scratch>"""
import sys,glob,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/tjk-sistem')
exec(open('/home/claude/tjk-sistem/data/analiz/siralama_ps_uret.py').read().split('d["q"]=')[0])
from tjk import besli
d["q"]=pd.PeriodIndex(pd.to_datetime(d.tarih),freq="Q").astype(str)
S=sys.argv[1];GJ=[1,0.80,0.69,0.69,0.69]
def sm(sv,te):
    e=np.exp(sv-pd.Series(sv).groupby(te.rid.values).transform("max").values);return e/pd.Series(e).groupby(te.rid.values).transform("sum").values
import os
out=[]
for q in ([] if os.path.exists(S+"/p_hib.pkl") else [x for x in sorted(d.q.unique()) if x>="2025Q1"]):
    te=d[d.q==q].copy();tr=d[d.tarih<te.tarih.min()]
    if tr.rid.nunique()<5000 or te.rid.nunique()<50: continue
    thA,muA,sdA,_=_fit(tr.assign(kazandi=(tr.sr==1).astype(float)),feat,M.get("lam",100.0))
    thB,aB,muB,sdB=fit_s(tr,M.get("lam",100.0),thA,GM)
    te=te.sort_values(O.K+["no"]).reset_index(drop=True);X=te[feat]
    te["pJ"]=sm(thA[0]*te.lp.values+(((X-muA)/sdA).values)@thA[1:],te)
    te["pS"]=sm(thB[0]*te.lp.values+(((X-muB)/sdB).values)@thB[1:],te)
    for k in range(1,5): te[f"a{k+1}"]=aB[k]
    out.append(te[["tarih","hipodrom","kosu","no","pJ","pS","a2","a3","a4","a5"]]);print(q,flush=True)
P=pd.read_pickle(S+"/p_hib.pkl") if os.path.exists(S+"/p_hib.pkl") else pd.concat(out)
P["tarih"]=P.tarih.astype(str);P.to_pickle(S+"/p_hib.pkl")
R='/home/claude/tjk-sistem/'
O_=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O_=O_[O_.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu'])
parse=lambda k:[set(int(x) for x in s.split(',')) for s in str(k).split('/')]
import time,pickle;T0=time.time();BUD=float(os.environ.get("BUTCE_SN","520"));CK=S+"/hibrit_rows.pkl"
_W0=besli._W;GM0=list(besli.G_M)
rows,done=(pickle.load(open(CK,"rb")) if os.path.exists(CK) else ([],set()));n=0;bitti=True
for r in O_.itertuples():
    if (r.tarih,r.hipodrom,r.kosu) in done: continue
    if time.time()-T0>BUD: bitti=False;break
    g=P[(P.tarih==r.tarih)&(P.hipodrom==r.hipodrom)&(P.kosu==r.kosu)]
    if len(g)<5: continue
    g=g.sort_values('no');nos=g.no.tolist();devir=r.tur.endswith('DEVİR');win=None if devir else parse(r.kombo)
    a=[1.0,g.a2.iloc[0],g.a3.iloc[0],g.a4.iloc[0],g.a5.iloc[0]]
    pJ=g.pJ.values.astype(float);pJ=pJ/pJ.sum();pS=g.pS.values.astype(float);pS=pS/pS.sum()
    def hib(p,G,pJ=pJ,pS=pS,a=a):
        W=[[max(v,1e-9)**GJ[k] for v in pJ] if k<2 else [max(v,1e-9)**a[k] for v in pS] for k in range(5)];return W,[sum(w) for w in W]
    for model in ('Jason','Jason-S','Hibrit'):
        besli._W=_W0
        if model=='Jason': besli.G_M=GJ;p=list(pJ)
        elif model=='Jason-S': besli.G_M=a;p=list(pS)
        else: besli.G_M=GJ;besli._W=hib;p=list(pJ)
        for B in (48,96,150):
            k=besli.kupon_g(p,B)
            if not k: continue
            sets,pr=k;cost=besli.gecerli_say(sets)*besli.BIRIM
            hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
            rows.append((r.tarih,r.hipodrom,r.kosu,model,B,cost,hit,float(r.tutar) if hit else 0.0,pr))
    n+=1;done.add((r.tarih,r.hipodrom,r.kosu))
    if n%25==0: pickle.dump((rows,done),open(CK,'wb'));print(len(done),flush=True)
besli._W=_W0;besli.G_M=GM0
pickle.dump((rows,done),open(CK,'wb'))
if not bitti: print('DEVAM',len(done),flush=True);sys.exit(0)
dd=pd.DataFrame(rows,columns=['t','h','k','model','B','cost','hit','pay','pr']);dd.to_csv(S+'/hibrit_kupon.csv',index=False);print('koşu',n)
def kar(x,y,B):
    m=x.merge(y,on=['t','h','k'],suffixes=('_x','_y'));rng=np.random.default_rng(5);bs=[]
    for _ in range(2000):
        s=m.sample(len(m),replace=True,random_state=int(rng.integers(1e9)));bs.append(s.pay_y.sum()/s.cost_y.sum()-s.pay_x.sum()/s.cost_x.sum())
    return len(m),m,np.mean(bs),np.percentile(bs,2.5),np.percentile(bs,97.5)
for B in (48,96,150):
    for mod in ('Jason','Jason-S','Hibrit'):
        x=dd[(dd.model==mod)&(dd.B==B)];print(f'B={B} {mod}: koşu {len(x)} tutan {int(x.hit.sum())} ({x.hit.mean()*100:.1f}%) beklenen %{x.pr.mean()*100:.1f} maliyet {x.cost.sum():.0f} ROI(A) {x.pay.sum()/x.cost.sum():.2f}')
    for a_,b_ in (('Jason','Hibrit'),('Jason-S','Hibrit')):
        x=dd[(dd.model==a_)&(dd.B==B)];y=dd[(dd.model==b_)&(dd.B==B)];nn,m,mu,lo,hi=kar(x,y,B);print(f'   {b_} − {a_}: ROI farkı {mu:+.2f} GA [{lo:+.2f},{hi:+.2f}] tutan {int(m.hit_y.sum())} vs {int(m.hit_x.sum())}')
