"""Faz 4 (ön kayıt 15 Ekim 2026 00:35): empirik Bayes önsel gücüyle Jason walk-forward. Kullanım: python3 -I eb_onsel_testi.py <scratch>"""
import sys,types,numpy as np,pandas as pd
R='/home/claude/tjk-sistem';sys.path.insert(0,R);S=sys.argv[1]
import tjk
src=open(R+'/tjk/ozellik.py',encoding='utf-8').read()
for a,b in [("M = 5.0","M = 24.0"),("onceki_gunler(d, 'antrenor', 30)","onceki_gunler(d, 'antrenor', 84)"),("onceki_gunler(d, 'sahip', 30)","onceki_gunler(d, 'sahip', 42)"),("onceki_gunler(d, 'baba', 60)","onceki_gunler(d, 'baba', 136)")]:
    assert a in src,a;src=src.replace(a,b)
m=types.ModuleType('tjk.ozellik');m.__package__='tjk';m.__file__=R+'/tjk/ozellik.py';sys.modules['tjk.ozellik']=m;exec(compile(src,m.__file__,'exec'),m.__dict__);tjk.ozellik=m
from tjk import ortak as O, mesafe as MS
from tjk.golge import _fit,_oku,EK,LPEK
from tjk.calistir import yukle_model
from tjk.walkforward import skorla
M=yukle_model();d=MS.ekle(m.hazirla(_oku("temiz"),_oku("program"),M))
d["f_lp2"]=np.log(d.p_piyasa.clip(lower=1e-6))**2
d=d[d.temiz&d.kazandi.notna()&d.lp.notna()].copy();d["tarih"]=d.tarih.astype(str)
d["q"]=pd.PeriodIndex(pd.to_datetime(d.tarih),freq="Q").astype(str);f=M["feat"]+EK+LPEK;rows=[]
for k in [x for x in sorted(d.q.unique()) if x>="2024Q2"]:
    te=d[d.q==k].sort_values(O.K+["no"]).reset_index(drop=True);tr=d[d.tarih<te.tarih.min()].copy();te["rid"]=te.groupby(O.K).ngroup()
    th,mu,sd,nk=_fit(tr,f,M.get("lam",100.0));te["p_EB"]=skorla(te,f,th,mu,sd);te["fold"]=k;rows.append(te[["fold","tarih","hipodrom","kosu","no","kazandi","p_EB"]]);print(k,flush=True)
E_=pd.concat(rows);P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
x=E_.merge(P[['tarih','hipodrom','kosu','no','p_Jason','p_piyasa']],on=['tarih','hipodrom','kosu','no']);w=x[x.kazandi==1].copy()
w['dlt']=np.log(w.p_EB)-np.log(w.p_Jason);w['g']=w.tarih+w.hipodrom
s=w.groupby('g').dlt.agg(['sum','size']);rng=np.random.default_rng(11);bs=[]
for _ in range(2000):
    t=s.iloc[rng.integers(0,len(s),len(s))];bs.append(t['sum'].sum()/t['size'].sum())
fq=w.groupby('fold').dlt.mean()
print('koşu',len(w),'EB−Jason %+.5f GA [%+.5f, %+.5f]'%(w.dlt.mean(),*np.percentile(bs,[2.5,97.5])),'pozitif çeyrek',(fq>0).sum(),'/',len(fq))
print('EB−piyasa %+.4f, Jason−piyasa %+.4f'%((np.log(w.p_EB)-np.log(w.p_piyasa)).mean(),(np.log(w.p_Jason)-np.log(w.p_piyasa)).mean()))
print(fq.round(5).to_string())
