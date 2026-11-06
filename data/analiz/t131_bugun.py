"""T125: tempo/stil piyasa ofseti üstünde bilgi katıyor mu? (hipotez_defteri.md ön kaydı)"""
import sys,glob,json,gzip,os,collections,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
# (sklearn içe aktarımı kaldırıldı 6 Kasım 2026: kullanılmıyordu, üretimde kurulu değil)
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

# --- T131: bugünün atlarını (bugun.json) yer tutucu satırlarla ekle; özellikler yalnız önceki koşulardan ---
import json as _j,sys as _s
BG=_j.load(open('docs/data/bugun.json')); BT=BG['tarih']; _slug={'Ankara':'ankara','İzmir':'izmir','Bursa':'bursa','İstanbul':'istanbul','Adana':'adana','Kocaeli':'kocaeli','Elazığ':'elazig','Diyarbakır':'diyarbakir','Şanlıurfa':'sanliurfa'}
_rows=[]
for hh in BG['hipodromlar']:
    hs=_slug.get(hh['ad'],hh['ad'].lower())
    for kk in hh['kosular']:
        MS[(BT,hs,int(kk['kosu']))]=float(kk['mesafe']); PS[(BT,hs,int(kk['kosu']))]=kk['pist']
        n_=len(kk['atlar'])
        for a_ in kk['atlar']:
            _rows.append(dict(tarih=BT,hipodrom=hs,kosu=int(kk['kosu']),sira=99,no=int(a_['no']),at=a_['at'],jokey=a_['jokey'],apranti=bool(a_.get('apr')),kilo=a_.get('kg'),derece_sn=np.nan,kosmadi=False,ganyan=np.nan,hnd=a_.get('hk'),p_ham=1.0/n_,p_piyasa=1.0/n_,kazandi=0,getiri=-1.0,dilim=''))
d=pd.concat([d,pd.DataFrame(_rows)],ignore_index=True); log('bugün',BT,'at',len(_rows))
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

# --- bugünün uyum skoru (dondurulmuş katsayı/standardizasyon) ---
FZ=_j.load(open('data/analiz/t126_c_dondurulmus.json')); c=np.array(FZ['c'])
d=d.sort_values('rid').reset_index(drop=True)
d['fe']=(1-d.f_v1).fillna(0.5); d['cl']=d.f_v2.fillna(0.0); d['pa']=d.pist_art.fillna(0.0)
d['tot']=d.groupby('rid').fe.transform('sum'); d['rp']=(d.tot-d.fe)/(d.n-1); d['mesk']=(d.mes-1400)/400.
for k_ in ('fe','cl','rp','mesk','pa'): m_,s_=FZ['std'][k_]; d[k_]=(d[k_]-m_)/s_
X=np.c_[d.fe,d.fe*d.rp,d.cl*d.rp,d.cl,d.fe*d.mesk,d.pa]; d['U']=X@c
B=d[d.tarih==BT].copy(); B['rkU']=B.groupby('rid').U.rank(ascending=False,method='first').astype(int)
B=B.sort_values(['hipodrom','kosu','rkU'])[['tarih','hipodrom','kosu','no','at','U','rkU','f_v1','f_v2','pist_art']]
os.makedirs('data/t131_kayit',exist_ok=True); B.to_csv(f'data/t131_kayit/{BT}_uyum.csv',index=False)
log(B[B.rkU<=3].to_string(index=False)); log('BİTTİ')
