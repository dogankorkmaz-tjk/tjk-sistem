"""T128: piyasa fiyatı neden böyle? (hipotez_defteri.md ön kaydı)"""
import sys,glob,json,gzip,os,collections,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from scipy.optimize import minimize_scalar
rng=np.random.default_rng(128)
def log(*a): print(*a,flush=True)
fs=[f for f in sorted(glob.glob('data/temiz/20*.csv.gz')) if os.path.basename(f)[:7]>='2024-10']
d=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
d=d[(d.kosmadi!=True)&d.p_piyasa.notna()&d.kazandi.notna()].copy()
MS={};PS={};AGE={};G={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=os.path.basename(f)[:10]
    if t<'2024-10-01': continue
    try: j=json.load(gzip.open(f))
    except Exception: continue
    for hip,ks in (j.get('program') or {}).items():
        for k in ks:
            try: kn=int(k['number']); MS[(t,hip,kn)]=float(k.get('distance') or np.nan); PS[(t,hip,kn)]=k.get('raceCourseType')
            except Exception: continue
            for h in k.get('horses',[]):
                try:
                    key=(t,hip,kn,int(h['number'])); G[key]=h.get('start'); a=str(h.get('age') or '').split('y')[0]; AGE[key]=float(a) if a.strip().isdigit() else np.nan
                except Exception: pass
k4=list(zip(d.tarih,d.hipodrom,d.kosu,d.no))
d['kapi']=[G.get(k,np.nan) for k in k4]; d['yas']=[AGE.get(k,np.nan) for k in k4]
d['mes']=[MS.get((t,h,k),np.nan) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]; d['pist']=[PS.get((t,h,k)) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d=VO.ekle(d)
d['rid']=d.tarih+'|'+d.hipodrom+'|'+d.kosu.astype(str)
d['n']=d.groupby('rid').no.transform('count'); d=d[(d.n>=5)&d.mes.notna()&d.pist.notna()].copy()
d['p']=d.p_piyasa/d.groupby('rid').p_piyasa.transform('sum'); d['lp']=np.log(d.p)
d['y']=d.lp-d.groupby('rid').lp.transform('mean')
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
# sıralı özellikler (yalnız önceki günlerden)
d['res']=np.nan; ph={};pj=collections.defaultdict(lambda:[0.,0]);pp=collections.defaultdict(lambda:[0.,0.]);last={}
F=collections.defaultdict(list)
byday=d.groupby('tarih').indices
for t in sorted(byday):
    for i in byday[t]:
        r=d.iloc[i]; at=r['at']; jk=r.jokey
        h=ph.get(at,[]); F['form5'].append(np.mean(h[-5:]) if h else np.nan); F['lastres'].append(h[-1] if h else np.nan); F['nkos'].append(len(h))
        F['dinlen'].append((pd.Timestamp(t)-last[at]).days if at in last else np.nan)
        w,n=pj[jk]; F['jok'].append((w+0.1*5)/(n+5))
        pa=pp[(at,r.pist)]; F['pist_art'].append(pa[0]/(pa[1]+2) if pa[1]>0 else np.nan); F['pist_n'].append(pa[1])
    for i in byday[t]:
        r=d.iloc[i]; at=r['at']; res=r.kazandi-r.p
        ph.setdefault(at,[]).append(res); last[at]=pd.Timestamp(t); pj[r.jokey][0]+=r.kazandi; pj[r.jokey][1]+=1; pp[(at,r.pist)][0]+=res; pp[(at,r.pist)][1]+=1
order=[i for t in sorted(byday) for i in byday[t]]
for k,v in F.items(): d.loc[order,k]=v
for c in ['kilo','hnd','yas','kapi']: d[c+'_r']=d[c]-d.groupby('rid')[c].transform('mean')
fcols=[c for c in d.columns if c.startswith('f_v')]; 
grp={'form':['form5','lastres','nkos','dinlen'],'jokey':['jok'],'yuk':['kilo_r','hnd_r','yas_r','kilo','hnd','yas'],'kapi':['kapi','kapi_r'],'pist_mes':['pist_art','pist_n','mes']+[],'stil':fcols}
d['pist_k']=d.pist.astype('category').cat.codes; grp['pist_mes']+=['pist_k']; d['n']=d.n
allc=sorted({c for v in grp.values() for c in v}|{'n'}); log('at',len(d),'koşu',d.rid.nunique(),'özellikler',len(allc))
d['ay']=d.tarih.str[:7]; ays=[a for a in sorted(d.ay.unique()) if a>='2025-12']
def fit(cols,tr,te):
    m=HGB(max_iter=200,learning_rate=0.06,max_depth=4,min_samples_leaf=60,random_state=1); m.fit(d.loc[tr,cols],d.loc[tr,'y']); return m.predict(d.loc[te,cols])
pred={};predd={g:np.full(len(d),np.nan) for g in grp}; pall=np.full(len(d),np.nan)
for a in ays:
    tr=(d.ay<a).values; te=(d.ay==a).values
    if tr.sum()<5000: continue
    pall[te]=fit(allc,tr,te)
    for g,cs in grp.items(): predd[g][te]=fit([c for c in allc if c not in cs],tr,te)
T=~np.isnan(pall); y=d.y.values
def r2(p): m=T&~np.isnan(p); return 1-((y[m]-p[m])**2).sum()/((y[m]-y[m].mean())**2).sum()
R=r2(pall); log('NEDEN: tüm özelliklerle R2',round(R,4),'test at',int(T.sum()))
for g in grp: log('  grup bırakma',g,'R2 düşüşü',round(R-r2(predd[g]),4))
d['art']=d.y-pall; D=d[T].copy()
# --- hızlı sürüm: koşu başına skor/hessian vektörleşik, gün ağırlıklı bootstrap (yavaş sürüm iptal edildi) ---
D=D.sort_values(['rid']).reset_index(drop=True)
rid_codes,rid_idx=np.unique(D.rid.values,return_inverse=True); R=len(rid_codes)
starts=np.r_[0,np.flatnonzero(np.diff(rid_idx))+1]; cnt=np.diff(np.r_[starts,len(D)])
lp=D.lp.values; art=D.art.values; win=(D.kazandi.values==1)
has=np.add.reduceat(win.astype(int),starts)==1
rday=D.groupby('rid').tarih.first().reindex(rid_codes).values
ud,day_idx=np.unique(rday,return_inverse=True)
def fitc(w,c=0.,it=25):
    for _ in range(it):
        z=lp+c*art; zm=np.maximum.reduceat(z,starts); e=np.exp(z-np.repeat(zm,cnt)); S=np.add.reduceat(e,starts)
        s=e/np.repeat(S,cnt)
        m1=np.add.reduceat(s*art,starts); m2=np.add.reduceat(s*art*art,starts); aw=np.add.reduceat(art*win,starts)
        g=(w*has*(aw-m1)).sum(); h=-(w*has*(m2-m1**2)).sum()
        if abs(h)<1e-12: break
        c=c-g/h
        if abs(g/h)<1e-8: break
    return c
def loglik(c,w):
    z=lp+c*art; zm=np.maximum.reduceat(z,starts); S=np.add.reduceat(np.exp(z-np.repeat(zm,cnt)),starts)
    zw=np.add.reduceat(z*win,starts); return (w*has*(zw-zm-np.log(S))).sum()
w1=np.ones(R); c0=fitc(w1); log('ARTIK: c =',round(c0,4),'log-olabilirlik kazancı (nat/koşu)',round((loglik(c0,w1)-loglik(0,w1))/has.sum(),6))
B=[];G=[]
for b in range(1000):
    k=np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud)); w=k[day_idx].astype(float); cb=fitc(w,c0); B.append(cb); G.append((loglik(cb,w)-loglik(0,w))/(w*has).sum())
log('c %95 GA (gün bootstrap 1000):',np.round(np.percentile(B,[2.5,97.5]),4),'| kazanç GA',np.round(np.percentile(G,[2.5,97.5]),6))
D['artbant']=pd.qcut(D.art,5,labels=False)
log('artık beşlik: ort. O/E (gözlenen kazanan / piyasa beklentisi)')
for q,x in D.groupby('artbant'): log('  ',q,round(x.kazandi.sum()/x.p.sum(),3),'n',len(x))
log('BİTTİ')
