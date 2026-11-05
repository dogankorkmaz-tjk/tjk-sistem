"""T132: özellik katsayıları mesafe/pistle değişiyor mu? (hipotez_defteri.md ön kaydı 2026-11-06)"""
import sys,glob,json,gzip,os,collections,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from scipy.optimize import minimize_scalar
rng=np.random.default_rng(125)
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
d['ay']=d.tarih.str[:7]
from scipy.optimize import minimize
rng=np.random.default_rng(132)
log('hazır',len(d),'at',d.rid.nunique(),'koşu')
d=d.sort_values(['rid','no']).reset_index(drop=True)
d['mes_b']=np.where(d.mes<1400,0,np.where(d.mes<1800,1,2))
ps=d.pist.astype(str).str.lower(); d['cim']=ps.str.contains('çim|cim|turf|grass').astype(float)
log('mesafe bandı',d.groupby('mes_b').rid.nunique().to_dict(),'| çim koşu',d[d.cim==1].rid.nunique(),'| pist değerleri',d.pist.value_counts().head(6).to_dict())
d['dl']=np.log1p(d.dinlen)
BASE=['kilo_r','hnd_r','yas_r','form5','lastres','dl','jok','kapi_r','pist_art']
d=d[d.groupby('rid').kazandi.transform('sum')==1].copy().reset_index(drop=True)
rid=d.rid.values; st=np.r_[0,np.flatnonzero(rid[1:]!=rid[:-1])+1]; cnt=np.diff(np.r_[st,len(d)]); rix=np.repeat(np.arange(len(st)),cnt)
rday=d.tarih.values[st]; rmon=d.ay.values[st]
y=d.kazandi.values.astype(float); lp=d.lp.values
def build(tr_mask):
    Z=d[BASE].copy(); mu=Z[tr_mask].mean(); sd=Z[tr_mask].std().replace(0,1); Z=((Z-mu)/sd).fillna(0.0).values
    mo=(d.mes_b.values==1).astype(float)-(d.mes_b.values==1)[tr_mask].mean(); lo=(d.mes_b.values==2).astype(float)-(d.mes_b.values==2)[tr_mask].mean(); ci=d.cim.values-d.cim.values[tr_mask].mean()
    XA=Z; XB=np.hstack([Z,Z*mo[:,None],Z*lo[:,None],Z*ci[:,None]]); return XA,XB
def fit(X,mask,pen,w=None,x0=None):
    rm=np.zeros(len(st),bool); rm[np.unique(rix[mask])]=True
    wr=np.ones(len(st)) if w is None else w
    wa=wr[rix]*mask
    def f(c):
        s=lp+X@c; m=np.maximum.reduceat(s,st); e=np.exp(s-m[rix]); S=np.add.reduceat(e,st); p=e/S[rix]
        ll=(wa*(y*(s-m[rix]-np.log(S)[rix]))).sum()
        g=X.T@(wa*(y-p))
        return -ll+0.5*(pen*c*c).sum(), -g+pen*c
    r=minimize(f,np.zeros(X.shape[1]) if x0 is None else x0,jac=True,method='L-BFGS-B'); return r.x
def llrace(X,c):
    s=lp+X@c; m=np.maximum.reduceat(s,st); e=np.exp(s-m[rix]); S=np.add.reduceat(e,st)
    return np.add.reduceat(y*(s-m[rix]-np.log(S)[rix]),st)
nb=len(BASE); penA=np.ones(nb); penB=np.r_[np.ones(nb),np.full(3*nb,30.)]
meses=[m for m in sorted(set(rmon)) if '2025-04'<=m<='2026-10']
gain=np.full(len(st),np.nan)
for m in meses:
    te=(d.ay.values==m); tr=(d.tarih.values<m+'-01')
    XA,XB=build(tr); cA=fit(XA,tr,penA); cB=fit(XB,tr,penB)
    la=llrace(XA,cA); lb=llrace(XB,cB); ri=np.unique(rix[te]); gain[ri]=lb[ri]-la[ri]
    log(m,'koşu',len(ri),'kazanç/koşu %+.5f'%np.nanmean(gain[ri]))
ok=~np.isnan(gain); g=gain[ok]; days=rday[ok]
ud,inv=np.unique(days,return_inverse=True); S=np.bincount(inv,weights=g); N=np.bincount(inv)
bs=[]
for _ in range(1000):
    k=np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud)); bs.append((k*S).sum()/(k*N).sum())
lo_,hi_=np.percentile(bs,[2.5,97.5])
log('=== T132 KARAR: B−A kazanç %+.5f nat/koşu [%+.5f, %+.5f]  koşu %d gün %d'%(g.mean(),lo_,hi_,len(g),len(ud)),'-> KABUL' if lo_>0 else '-> ayırt edilemedi')
# betimsel: tam örneklem B katsayıları, gün-ağırlıklı bootstrap
allm=np.ones(len(d),bool); XA,XB=build(allm); c0=fit(XB,allm,penB)
names=BASE+[b+'×orta' for b in BASE]+[b+'×uzun' for b in BASE]+[b+'×çim' for b in BASE]
dayidx=pd.Series(np.arange(len(st))).groupby(rday).indices; dk=list(dayidx)
B=[]
for r in range(400):
    pk=rng.integers(0,len(dk),len(dk)); w=np.zeros(len(st))
    for j in pk: w[dayidx[dk[j]]]+=1
    B.append(fit(XB,allm,penB,w=w,x0=c0))
B=np.array(B); lo=np.percentile(B,2.5,0); hi=np.percentile(B,97.5,0)
for i,nm in enumerate(names):
    if i<nb or nm.split('×')[0] in ('kilo_r','hnd_r') : log('  %-16s %+.4f [%+.4f, %+.4f]'%(nm,c0[i],lo[i],hi[i]))
log('bitti')
