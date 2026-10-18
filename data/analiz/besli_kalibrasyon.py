"""Sıralı 5'li kalibrasyon testi (ön kayıt 19 Ekim 2026 03:35). Kullanım: python3 -I besli_kalibrasyon.py <oos_p.pkl klasörü>"""
import sys,glob,os,numpy as np,pandas as pd
from multiprocessing import Pool
from scipy.optimize import minimize
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/';S=sys.argv[1]
sys.path.insert(0,R)
from tjk import besli
P=pd.read_pickle(S+'/oos_p.pkl');P['tarih']=P.tarih.astype(str);K=['tarih','hipodrom','kosu']
P['sr']=pd.to_numeric(P.sira,errors='coerce').fillna(0);P=P[P.p_Jason.notna()]
# --- eğitim: 2024 tüm koşular, ilk 5 çözülmüş
ok=P.groupby(K).sr.apply(lambda x:all((x==k).sum()==1 for k in range(1,6)))
E=P[(P.tarih<'2025-01-01')].merge(ok.rename('ok').reset_index(),on=K);E=E[E.ok]
R_=[]
for k,g in E.groupby(K):
    g=g.sort_values('p_Jason',ascending=False) if False else g
    p=g.p_Jason.values/g.p_Jason.sum();ordr=[int(np.where(g.sr.values==j)[0][0]) for j in range(1,6)];R_.append((p,ordr))
print('eğitim koşu',len(R_),flush=True)
def nll(a):
    A=np.r_[1.0,a];tot=0.0
    for p,o in R_:
        W=[np.maximum(p,1e-9)**g for g in A];used=[]
        for kk in range(5):
            den=W[kk].sum()-sum(W[kk][u] for u in used);tot-=np.log(W[kk][o[kk]]/den);used.append(o[kk])
    return tot
a0=np.array([0.80,0.69,0.69,0.69])
res=minimize(nll,a0,method='Nelder-Mead',options={'maxiter':200,'xatol':1e-2,'fatol':1e-2});aN=np.r_[1.0,res.x]
print('mevcut üsler',besli.G_M,'nll',round(nll(a0),1),'| öğrenilmiş',np.round(aN,3),'nll',round(res.fun,1),flush=True)
# --- sınama
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')]);O=O[O.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu'])
O['tarih']=O.tarih.astype(str);O=O[O.tarih>='2025-01-01']
parse=lambda k:[set(int(x) for x in s.split(',')) for s in str(k).split('/')]
PP={k:g for k,g in P.groupby(K)}
def isle(r):
    g=PP.get((r['tarih'],r['hipodrom'],r['kosu']))
    if g is None or len(g)<5: return []
    g=g.sort_values('no');nos=g.no.tolist();devir=str(r['tur']).endswith('DEVİR');win=None if devir else parse(r['kombo'])
    p=g.p_Jason.values.astype(float);p=list(p/p.sum());out=[]
    for ad,G in (('V0',list(besli.G_M)),('V1',list(aN))):
        for B in (96,150):
            k=besli.kupon_g(p,B,G)
            if not k: continue
            sets,pr=k;cost=besli.gecerli_say(sets)*besli.BIRIM
            hit=(not devir) and all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
            out.append((r['tarih'],r['hipodrom'],r['kosu'],ad,B,cost,hit,float(r['tutar']) if hit else 0.0,pr))
    return out
if __name__=='__main__':
    rows=[];rs=O.to_dict('records')
    with Pool(2) as pool:
        for i,x in enumerate(pool.imap(isle,rs,chunksize=8)):
            rows+=x
            if i%100==0: print('ilerleme',i,len(rs),flush=True)
    d=pd.DataFrame(rows,columns=['t','h','k','model','B','cost','hit','pay','pr']);d.to_csv(S+'/besli_kalib.csv',index=False)
    for B in (96,150):
        a=d[(d.model=='V0')&(d.B==B)];b=d[(d.model=='V1')&(d.B==B)];m=a.merge(b,on=['t','h','k'],suffixes=('_0','_1'))
        rng=np.random.default_rng(5);bs=[]
        for _ in range(4000):
            ix=rng.integers(0,len(m),len(m));s=m.iloc[ix];bs.append(s.pay_1.sum()/s.cost_1.sum()-s.pay_0.sum()/s.cost_0.sum())
        print(f'B={B} koşu {len(m)} | V0 tutan {int(m.hit_0.sum())} ({m.hit_0.mean()*100:.1f}%) beklenen %{m.pr_0.mean()*100:.1f} ROI {m.pay_0.sum()/m.cost_0.sum():.3f} | V1 tutan {int(m.hit_1.sum())} ({m.hit_1.mean()*100:.1f}%) beklenen %{m.pr_1.mean()*100:.1f} ROI {m.pay_1.sum()/m.cost_1.sum():.3f} | fark {m.pay_1.sum()/m.cost_1.sum()-m.pay_0.sum()/m.cost_0.sum():+.3f} GA97,5 {np.percentile(bs,[1.25,98.75]).round(3)}')
