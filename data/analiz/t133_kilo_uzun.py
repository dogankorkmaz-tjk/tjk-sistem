"""T133: kilo x uzun mesafe, Benter(S3g)/Jason(pj)/v3-galopsuz(S3) tabanları üstünde (hipotez_defteri.md ön kaydı 2026-11-06)"""
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
import pickle
rng=np.random.default_rng(133)
log('hazır',len(d))
d['uzun']=(d.mes>=1800).astype(float)
KR={(t,h,int(k),int(n)):(kr,u) for t,h,k,n,kr,u in zip(d.tarih,d.hipodrom,d.kosu,d.no,d.kilo_r,d.uzun)}
sdk=float(d.kilo_r.std()); log('kilo_r std',sdk)
def yuk(v,a): return pickle.load(open(f'/tmp/claude-0/cacheg_{v}_{a}.pkl','rb'))
def toplam(taban):
    R=[]   # (ay, gun, skor[], x[], kazanan_idx)
    if taban in ('A','C'):
        key='S3g' if taban=='A' else 'S3'
        for a in [f'2025-12']+[f'2026-{m:02d}' for m in range(1,11)]:
            if taban=='A' and a<'2026-03': continue
            X=yuk('MJ',a)
            if np.isnan(X[key]).any(): continue
            for k,kk in enumerate(X['keys']):
                nos=X['nos'][k]; S=X[key][k][:len(nos)]
                kw=[(KR.get((kk[0],kk[1],int(kk[2]),int(n)))) for n in nos]
                if any(v is None for v in kw): continue
                wi=[i for i,n in enumerate(nos) if (kk[0],kk[1],int(kk[2]),int(n)) in WIN]
                if len(wi)!=1: continue
                x=np.array([v[0]*v[1] for v in kw])/sdk; R.append((a,kk[0],S.copy(),np.nan_to_num(x),wi[0]))
    else:
        J=pd.read_pickle('/tmp/claude-0/jason_wf.pkl'); J['ay']=J.tarih.str[:7]
        for (t,h,k),g in J.groupby(['tarih','hipodrom','kosu'],sort=False):
            nos=g.no.astype(int).values
            kw=[KR.get((t,h,int(k),int(n))) for n in nos]
            if any(v is None for v in kw) or g.kazandi.sum()!=1: continue
            x=np.array([v[0]*v[1] for v in kw])/sdk; R.append((g.ay.iloc[0],t,np.log(np.clip(g.pj.values,1e-9,None)),np.nan_to_num(x),int(np.argmax(g.kazandi.values))))
    return R
WIN=set((t,h,int(k),int(n)) for t,h,k,n,z in zip(d.tarih,d.hipodrom,d.kosu,d.no,d.kazandi) if z==1)
def pad(R):
    M=max(len(r[2]) for r in R); S=np.full((len(R),M),-1e9); X=np.zeros((len(R),M))
    for i,r in enumerate(R): S[i,:len(r[2])]=r[2]; X[i,:len(r[3])]=r[3]
    return S,X,np.array([r[4] for r in R])
def ll(S,X,w,b):
    s=S+b*X; m=s.max(1,keepdims=True); e=np.exp(s-m); lse=m[:,0]+np.log(e.sum(1)); return s[np.arange(len(S)),w]-lse
def fitb(S,X,w,wt=None):
    wt=np.ones(len(S)) if wt is None else wt; b=0.
    for _ in range(25):
        s=S+b*X; s=s-s.max(1,keepdims=True); e=np.exp(s); p=e/e.sum(1,keepdims=True)
        mx=(p*X).sum(1); g=(wt*(X[np.arange(len(S)),w]-mx)).sum(); h=-(wt*((p*X*X).sum(1)-mx**2)).sum()
        if abs(h)<1e-12: break
        step=-g/h; b+=step
        if abs(step)<1e-8: break
    return b
AD={'A':'Benter (S3g)','B':'Jason (pj)','C':'v3 galopsuz (S3)'}
for tb in ('A','B','C'):
    R=toplam(tb)
    if not R: log(tb,'veri yok'); continue
    S,X,w=pad(R); ay=np.array([r[0] for r in R]); gun=np.array([r[1] for r in R]); ms=sorted(set(ay))
    log('====',AD[tb],'koşu',len(R),'aylar',ms[0],'..',ms[-1],'| uzun koşu payı',float((X!=0).any(1).mean()))
    gain=np.full(len(R),np.nan)
    for m in ms[1:]:
        tr=ay<m; te=ay==m
        if tr.sum()<100: continue
        b=fitb(S[tr],X[tr],w[tr]); gain[te]=ll(S[te],X[te],w[te],b)-ll(S[te],X[te],w[te],0.)
        log('  ',m,'β̂ %+.4f'%b,'kazanç/koşu %+.5f'%np.nanmean(gain[te]))
    ok=~np.isnan(gain); ud,inv=np.unique(gun[ok],return_inverse=True); Sg=np.bincount(inv,weights=gain[ok]); Ng=np.bincount(inv)
    bs=[]; 
    for _ in range(1000):
        k=np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud)); bs.append((k*Sg).sum()/(k*Ng).sum())
    lo,hi=np.percentile(bs,[2.5,97.5])
    # tam pencere β̂ + gün-küme bootstrap
    b0=fitb(S,X,w); ug,gi=np.unique(gun,return_inverse=True); bb=[]
    for _ in range(400):
        k=np.bincount(rng.integers(0,len(ug),len(ug)),minlength=len(ug)); bb.append(fitb(S,X,w,wt=k[gi].astype(float)))
    blo,bhi=np.percentile(bb,[2.5,97.5])
    kabul=(lo>0) and (bhi<0)
    log('  >> %s: yürüyüş kazancı %+.5f nat/koşu [%+.5f, %+.5f] (%d koşu, %d gün) | β̂ tam pencere %+.4f [%+.4f, %+.4f] -> %s'%(AD[tb],np.nanmean(gain),lo,hi,ok.sum(),len(ud),b0,blo,bhi,'KABUL' if kabul else 'ayırt edilemedi'))
log('bitti')
