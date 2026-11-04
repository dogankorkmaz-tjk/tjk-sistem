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
# --- T126 ---
d=d.sort_values('rid').reset_index(drop=True)
d['fe']=(1-d.f_v1).fillna(0.5); d['cl']=d.f_v2.fillna(0.0); d['pa']=d.pist_art.fillna(0.0)
d['tot']=d.groupby('rid').fe.transform('sum'); d['rp']=(d.tot-d.fe)/(d.n-1); d['mesk']=(d.mes-1400)/400.
STD={c:[float(d[c].mean()),float(d[c].std())] for c in ('fe','cl','rp','mesk','pa')}
for c in ('fe','cl','rp','mesk','pa'): d[c]=(d[c]-d[c].mean())/d[c].std()
d['X1']=d.fe; d['X2']=d.fe*d.rp; d['X3']=d.cl*d.rp; d['X4']=d.cl; d['X5']=d.fe*d.mesk; d['X6']=d.pa
XC=['X1','X2','X3','X4','X5','X6']; K_=len(XC)
def arrays(S):
    S=S.sort_values('rid'); ri=np.unique(S.rid.values,return_inverse=True)[1]; st=np.r_[0,np.flatnonzero(np.diff(ri))+1]; cnt=np.diff(np.r_[st,len(S)])
    return S,st,cnt,S.lp.values,S[XC].values,(S.kazandi.values==1)
def fitc(S):
    S,st,cnt,lp,X,win=arrays(S); has=np.add.reduceat(win.astype(int),st)==1; Xw=np.add.reduceat(X*win[:,None],st); c=np.zeros(K_)
    for _ in range(25):
        z=lp+X@c; zm=np.maximum.reduceat(z,st); e=np.exp(z-np.repeat(zm,cnt)); s=e/np.repeat(np.add.reduceat(e,st),cnt); m=np.add.reduceat(s[:,None]*X,st)
        g=((Xw-m)*has[:,None]).sum(0); H=np.zeros((K_,K_))
        for a in range(K_):
            for b in range(a,K_): H[a,b]=H[b,a]=-((np.add.reduceat(s*X[:,a]*X[:,b],st)-m[:,a]*m[:,b])*has).sum()
        stp=np.linalg.solve(H-1e-9*np.eye(K_),g); c=c-stp
        if np.abs(stp).max()<1e-8: break
    return c
d['ay']=d.tarih.str[:7]; ays=[a for a in sorted(d.ay.unique()) if a>='2026-02']
d['U']=np.nan; cs={}
for a in ays:
    tr=d[(d.ay<a)&(d.ay>='2025-10')]; cs[a]=fitc(tr); te=(d.ay==a).values; d.loc[te,'U']=d.loc[te,XC].values@cs[a]
log('walk-forward c (son ay):',np.round(cs[ays[-1]],3))
T=d[d.U.notna()].copy()
T['rkp']=T.groupby('rid').p.rank(ascending=False,method='first'); T['rkU']=T.groupby('rid').U.rank(ascending=False,method='first')
T['pay']=T.kazandi*T.ganyan.fillna(0)
def rap(mask,ad,ana=False):
    S=T[mask]; g=S.groupby('tarih').agg(o=('kazandi','sum'),e=('p','sum'),pay=('pay','sum'),n=('kazandi','size')); o,e,pay,n=[g[c].values for c in ('o','e','pay','n')]
    r=[];q=[]
    for _ in range(2000):
        k=rng.integers(0,len(g),len(g)); r.append(o[k].sum()/e[k].sum()); q.append(pay[k].sum()/n[k].sum())
    log(f'{ad}: bahis {int(n.sum())} kazanan {int(o.sum())} beklenen {e.sum():.1f} | O/E {o.sum()/e.sum():.3f} [{np.percentile(r,2.5):.3f},{np.percentile(r,97.5):.3f}] | ROI {pay.sum()/n.sum():.3f} [{np.percentile(q,2.5):.3f},{np.percentile(q,97.5):.3f}]'+(' <== ANA TEST' if ana else ''))
    return np.percentile(r,2.5)
log('T126 test aylar',ays[0],'..',ays[-1],'koşu',T.rid.nunique())
lo=rap((T.rkp>=3)&(T.rkU<=2),'ANA: piyasa sırası>=3 ∧ uyum sırası<=2',True)
log('KARAR:','O/E GA alt sınırı>1 → uyum değer taşıyor' if lo>1 else 'O/E GA alt sınırı<=1 → kanıt yok')
log('BANTLAR (betimleyici):')
for ad,m in (('3-6',(T.rkp>=3)&(T.rkp<=6)),('7-10',(T.rkp>=7)&(T.rkp<=10)),('11+',T.rkp>=11)): rap(m&(T.rkU<=2),'  piyasa sırası '+ad+' ∧ uyum<=2')
rap((T.rkp<=2)&(T.rkU<=2),'  KONTROL favori(1-2) ∧ uyum<=2')
rap((T.rkp>=3)&(T.rkU>=T.groupby('rid').rkU.transform('max')-1),'  KONTROL piyasa>=3 ∧ uyum EN DÜŞÜK 2')
rap(T.rkp>=3,'  KONTROL piyasa>=3 (tümü)')
import json
son=fitc(d[(d.ay<'2026-11')&(d.ay>='2025-10')]); json.dump({'c':[float(x) for x in son],'XC':XC,'std':STD,'egitim':'2025-10..2026-10','sabitlendi':'2026-11-05'},open('data/analiz/t126_c_dondurulmus.json','w'),indent=1); log('dondurulmuş c',np.round(son,4))
log('BİTTİ')
