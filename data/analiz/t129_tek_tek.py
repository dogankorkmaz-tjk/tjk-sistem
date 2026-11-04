"""T129: piyasanın tek tek fiyatlamaları (şeffaf doğrusal model) (hipotez_defteri.md ön kaydı)"""
import sys,glob,json,gzip,os,collections,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from scipy.optimize import minimize_scalar
rng=np.random.default_rng(129)
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
# --- T129: koşu sabit etkili doğrusal model, standartlaştırılmış katsayı = 1 SS değişim → log-olasılık (≈ oran %) ---
d['lnk']=np.log1p(d.nkos); d['lnd']=np.log1p(d.dinlen.clip(lower=0)); d['kapi_r2']=d.kapi_r**2; d['hnd_r2']=d.hnd_r**2; d['kilo_r2']=d.kilo_r**2
d['kum']=(d.pist.astype(str).str.contains('um',case=False)).astype(float); d['sent']=(d.pist.astype(str).str.contains('ent',case=False)).astype(float)
d['mes_k']=(d.mes-1400)/400.
sc=[c for c in fcols][:6]
for c in sc: d[c+'_xkum']=d[c]*d.kum; d[c+'_xsent']=d[c]*d.sent; d[c+'_xmes']=d[c]*d.mes_k
d['pist_art_xkum']=d.pist_art.fillna(0)*d.kum; d['pist_art_xsent']=d.pist_art.fillna(0)*d.sent
X=['form5','lastres','lnk','lnd','jok','pist_art','pist_art_xkum','pist_art_xsent','kilo_r','kilo_r2','hnd_r','hnd_r2','yas_r','kapi_r','kapi_r2']+sc+[c+s for c in sc for s in ('_xkum','_xsent','_xmes')]
D=d[d.ay>='2025-12'].copy()
for c in X: D[c]=D[c].astype(float); D[c+'_na']=D[c].isna().astype(float) if D[c].isna().mean()>0.02 else 0.; D[c]=D[c].fillna(D[c].median())
na=[c+'_na' for c in X if isinstance(D[c+'_na'],pd.Series)]
Z=X+na
for c in X: D[c]=(D[c]-D[c].mean())/(D[c].std()+1e-12)
rid=D.rid.values; Y=D.y.values
M=D[Z].values.astype(float); m=pd.DataFrame(M).groupby(rid).transform('mean').values; Xd=M-m   # koşu içi ortalamadan fark (sabit etki)
keep=Xd.std(0)>1e-9; Z=[z for z,k in zip(Z,keep) if k]; Xd=Xd[:,keep]; Yd=Y-pd.Series(Y).groupby(rid).transform('mean').values
ud,di=np.unique(D.tarih.values,return_inverse=True)
def ols(w): 
    XtW=Xd.T*w; return np.linalg.solve(XtW@Xd+1e-6*np.eye(Xd.shape[1]),XtW@Yd)
b0=ols(np.ones(len(D))); B=[]
for b in range(1000):
    k=np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud)); B.append(ols(k[di].astype(float)))
B=np.array(B); lo,hi=np.percentile(B,[2.5,97.5],axis=0); se=B.std(0)
res=Yd-Xd@b0; r2=1-(res**2).sum()/(Yd**2).sum()
K=len(X); zb=2.58 if K<50 else 2.9
vif=np.diag(np.linalg.inv(np.corrcoef(Xd[:,:len(X)].T)+1e-6*np.eye(len(X)))) if len(X)==Xd.shape[1] else None
log('T129 koşu içi R2',round(r2,4),'at',len(D),'koşu',D.rid.nunique(),'özellik',len(Z))
log('katsayı (1 SS → log olasılık), 95 pct gün-küme GA, Bonferroni anlamlı (|b|/se>',zb,')')
for z,b,l,h,s in sorted(zip(Z,b0,lo,hi,se),key=lambda t:-abs(t[1]/(t[4]+1e-12))):
    log(f'  {z:22s} {b:+.4f} [{l:+.4f},{h:+.4f}] {"*" if abs(b/(s+1e-12))>zb else ""}')
if vif is not None: log('VIF en yüksek 5:',sorted(zip(np.round(vif,1),X),reverse=True)[:5])
log('BİTTİ')
