"""T125: tempo/stil piyasa ofseti üstünde bilgi katıyor mu? (hipotez_defteri.md ön kaydı)"""
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
# --- T125 ---
d=d.sort_values('rid').reset_index(drop=True)
d['fe']=(1-d.f_v1).fillna(0.5); d['cl']=d.f_v2.fillna(0.0)
d['tot']=d.groupby('rid').fe.transform('sum'); d['rp']=(d.tot-d.fe)/(d.n-1)      # rakip öncülük ortalaması (öncü baskısı)
d['mesk']=(d.mes-1400)/400.
for c in ('fe','cl','rp','mesk'): d[c]=(d[c]-d[c].mean())/d[c].std()
d['X1']=d.fe; d['X2']=d.fe*d.rp; d['X3']=d.cl*d.rp; d['X4']=d.cl; d['X5']=d.fe*d.mesk
XC=['X1','X2','X3','X4','X5']
T=d[d.ay>='2025-12'].reset_index(drop=True)
ri=np.unique(T.rid.values,return_inverse=True)[1]; st=np.r_[0,np.flatnonzero(np.diff(ri))+1]; cnt=np.diff(np.r_[st,len(T)])
lp=T.lp.values; X=T[XC].values; win=(T.kazandi.values==1); has=np.add.reduceat(win.astype(int),st)==1
day=T.groupby('rid').tarih.first().reindex(np.unique(T.rid.values)).values; ud,di=np.unique(day,return_inverse=True); K_=len(XC)
Xw=np.add.reduceat(X*win[:,None],st)
def parts(c):
    z=lp+X@c; zm=np.maximum.reduceat(z,st); e=np.exp(z-np.repeat(zm,cnt)); S=np.add.reduceat(e,st); s=e/np.repeat(S,cnt)
    m=np.add.reduceat(s[:,None]*X,st); return z,zm,S,s,m
def fit(w,c):
    for _ in range(30):
        z,zm,S,s,m=parts(c); g=((Xw-m)*(w*has)[:,None]).sum(0)
        H=np.zeros((K_,K_))
        for a in range(K_):
            for b in range(a,K_):
                v=(np.add.reduceat(s*X[:,a]*X[:,b],st)-m[:,a]*m[:,b])*w*has; H[a,b]=H[b,a]=-v.sum()
        step=np.linalg.solve(H-1e-9*np.eye(K_),g); c=c-step
        if np.abs(step).max()<1e-8: break
    return c
def ll(w,c):
    z,zm,S,s,m=parts(c); zw=np.add.reduceat(z*win,st); return (w*has*(zw-zm-np.log(S))).sum()
w1=np.ones(len(st)); c0=fit(w1,np.zeros(K_)); gain=(ll(w1,c0)-ll(w1,np.zeros(K_)))/has.sum()
log('T125 koşu',has.sum(),'at',len(T),'| katsayılar (fe, fe×rp, cl×rp, cl, fe×mesafe):',np.round(c0,4),'| log-olabilirlik kazancı nat/koşu',round(gain,6))
B=[];G=[]
for b in range(500):
    w=np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud))[di].astype(float); cb=fit(w,c0); B.append(cb); G.append((ll(w,cb)-ll(w,np.zeros(K_)))/(w*has).sum())
B=np.array(B); lo,hi=np.percentile(B,[2.5,97.5],axis=0); log('katsayı %95 GA:'); 
for n_,a,l,h in zip(XC,c0,lo,hi): log(f'   {n_} {a:+.4f} [{l:+.4f},{h:+.4f}]')
g_lo,g_hi=np.percentile(G,[2.5,97.5]); log('ANA KARAR kazanç GA nat/koşu',round(g_lo,6),round(g_hi,6),'=> ALT GA>0: tempo/stil piyasanın ÜSTÜNE bilgi taşıyor' if g_lo>0 else '=> alt GA<=0: kanıt yok')
# alt analiz: (a) piyasa favorisi ∧ öncü (fe üst çeyrek) ∧ rp üst çeyrek ; (b) yatan (cl üst çeyrek) ∧ rp üst çeyrek
T['rk']=T.groupby('rid').p.rank(ascending=False,method='first'); qrp=T.rp.quantile(.75); qfe=T.fe.quantile(.75); qcl=T.cl.quantile(.75)
def oe(mask,ad):
    S=T[mask]; dd=S.groupby('tarih').agg(o=('kazandi','sum'),e=('p','sum')); idx=np.arange(len(dd)); r=[]
    for _ in range(1000):
        k=rng.integers(0,len(dd),len(dd)); r.append(dd.o.values[k].sum()/dd.e.values[k].sum())
    log(f'   {ad}: n={len(S)} gözlenen {int(S.kazandi.sum())} beklenen {S.p.sum():.1f} O/E {S.kazandi.sum()/S.p.sum():.3f} GA [{np.percentile(r,2.5):.3f},{np.percentile(r,97.5):.3f}]')
log('ALT ANALİZ (betimleyici, ayrı Bonferroni):')
oe((T.rk==1)&(T.fe>=qfe)&(T.rp>=qrp),'(a) favori ∧ öncü ∧ yüksek rakip öncü baskısı (beklenen O/E<1)')
oe((T.cl>=qcl)&(T.rp>=qrp),'(b) yatan ∧ yüksek rakip öncü baskısı (beklenen O/E>1)')
oe((T.rk==1)&(T.fe>=qfe)&(T.rp<=T.rp.quantile(.25)),'(kontrol) favori ∧ öncü ∧ DÜŞÜK rakip öncü baskısı')
log('BİTTİ')
