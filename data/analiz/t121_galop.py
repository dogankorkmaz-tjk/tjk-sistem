"""T121-A (T120/T122 türevi): galop + soy + antrenör özellikleri, at düzeyi öncü tahmini; tempo / öncü sayısı öngörülebilir mi + zengin at özellikleri (hipotez_defteri.md ön kaydı)."""
import sys,glob,json,gzip,os,collections,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
from sklearn.linear_model import LogisticRegression,LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
rng=np.random.default_rng(120)
def log(*a): print(*a,flush=True)
fs=[f for f in sorted(glob.glob('data/temiz/20*.csv.gz')) if os.path.basename(f)[:7]>='2024-10']
d=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
d=d[(d.kosmadi!=True)&d.p_piyasa.notna()&d.kazandi.notna()].copy()
G={};MS={};PS={};SIRE={};EQ={};AGE={};CINS={};COACH={};EQC={};FOM={};FOF={};SALE={};ARAP={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=os.path.basename(f)[:10]
    if t<'2024-10-01': continue
    try: j=json.load(gzip.open(f))
    except Exception: continue
    for hip,ks in (j.get('program') or {}).items():
        for k in ks:
            try: kn=int(k['number']); MS[(t,hip,kn)]=float(k.get('distance') or np.nan); PS[(t,hip,kn)]=k.get('raceCourseType'); CINS[(t,hip,kn)]=k.get('typeDescription'); AR=int('arap' in str(k.get('groupName','')).lower())
            except Exception: continue
            for h in k.get('horses',[]):
                try:
                    key=(t,hip,kn,int(h['number'])); G[key]=h.get('start'); COACH[key]=((h.get('coach') or {}).get('shortName')); FOM[key]=(((h.get('parents') or {}).get('fatherOfMother')) or {}).get('name'); FOF[key]=(((h.get('parents') or {}).get('fatherOfFather')) or {}).get('name'); SALE[key]=int(bool(h.get('salePrice'))); ARAP[key]=AR; ec=h.get('equipmentChanges') or {}; EQC[key]=len(ec.get('added') or [])+len(ec.get('removed') or []); EQ[key]=(h.get('equipment') or '').split()
                    SIRE[key]=((h.get('parents') or {}).get('father') or {}).get('name'); a=str(h.get('age') or '').split('y')[0]; AGE[key]=float(a) if a.strip().isdigit() else np.nan
                except Exception: pass
key4=list(zip(d.tarih,d.hipodrom,d.kosu,d.no))
d['kapi']=[G.get(k,np.nan) for k in key4]; d['sire']=[SIRE.get(k) for k in key4]; d['yas']=[AGE.get(k,np.nan) for k in key4]; d['ekp']=[EQ.get(k,[]) for k in key4]; d['coach']=[COACH.get(k) for k in key4]; d['eqc']=[EQC.get(k,0) for k in key4]; d['cins']=[CINS.get((k[0],k[1],k[2])) for k in key4]; d['fom']=[FOM.get(k) for k in key4]; d['fof']=[FOF.get(k) for k in key4]; d['sale']=[SALE.get(k,0) for k in key4]; d['arap']=[ARAP.get(k,0) for k in key4]
d['mes']=[MS.get((t,h,k),np.nan) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]; d['pist']=[PS.get((t,h,k)) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d=VO.ekle(d)
E={};RH={}
for f in glob.glob('data/video_seyir/20*.json'):
    b=os.path.basename(f)[:-5].split('_')
    if len(b)!=3: continue
    try: j=json.load(open(f))
    except Exception: continue
    if j.get('okuyucu')!='rakam1' or not j.get('ozet'): continue
    for no,o in j['ozet'].items(): E[(b[0],b[1],int(b[2]),int(no))]=o['erken']
    z=[x['sira'] for x in j['zaman'] if x['sira']]; kapi=list(j['numaralar'])[:j.get('kutu',10)]
    while z and z[0]==kapi: z.pop(0)
    L=len(z); bl={int(k):v for k,v in (j.get('bolum') or {}).items() if k.isdigit()}
    fade=bl[400]/(bl[800]-bl[400]) if 400 in bl and 800 in bl and bl[800]>bl[400] else np.nan
    if L>=10:
        f25=z[:max(int(L*0.25),1)]; RH[(b[0],b[1],int(b[2]))]=(len({fr[0] for fr in f25}),len({h for fr in f25 for h in fr[:2]}),fade)
d['e_erken']=[E.get(k,np.nan) for k in zip(d.tarih,d.hipodrom,d.kosu,d.no)]; d=d[d.e_erken.notna()].copy()   # (düzeltme: VO.ekle satırları yeniden sıraladığı için anahtarlar güncel sütunlardan)
d['rid']=d.tarih+'|'+d.hipodrom+'|'+d.kosu.astype(str)
d['n']=d.groupby('rid').no.transform('count'); d=d[d.n>=5].copy()
d['p']=d.p_piyasa/d.groupby('rid').p_piyasa.transform('sum')
d['rk']=d.groupby('rid').e_erken.rank(method='min'); d['lead2']=(d.rk<=2).astype(int); d['lead1']=(d.rk<=1).astype(int)
d=d[d.kapi.notna()&d.mes.notna()&d.pist.notna()].copy()
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
log('at',len(d),'koşu',d.rid.nunique(),'gün',d.tarih.nunique())
assert d.groupby('rid').lead2.sum().between(2,4).mean()>0.9   # hedef sağlama
# ekipman jetonları
cnt=collections.Counter(t for l in d.ekp for t in set(l)); top=[t for t,_ in cnt.most_common(15)]; log('ekipman jetonları',top)
for t in top: d['eq_'+t]=[int(t in l) for l in d.ekp]
# sıralı özellikler: jokey öncü oranı, baba eğilimi, ikili karşılaşmalar
K=20; jl={};sr={};pair=collections.defaultdict(lambda:[0.,0]);glob_rate=d.lead2.mean()
cs={};coach_e=np.zeros(len(d));n=len(d);jok=np.zeros(n);sire_e=np.zeros(n);pw=np.zeros(n);pwc=np.zeros(n);fstr=np.zeros(n)
tarih=d.tarih.values;jk=d.jokey.values;at=d['at'].values;sr_n=d.sire.values;co_n=d.coach.values;ek=d.e_erken.values;nn=d.n.values;l2=d.lead2.values
gix=d.groupby('tarih').indices
for t in sorted(gix):
    ix=gix[t]
    for i in ix:
        s=jl.get(jk[i],(0,0)); jok[i]=(s[0]+5*glob_rate)/(s[1]+5)-glob_rate
        if sr_n[i] in sr: s=sr[sr_n[i]]; sire_e[i]=(s[0]+K*0.5)/(s[1]+K)-0.5
        if co_n[i] in cs: s=cs[co_n[i]]; coach_e[i]=(s[0]+K*0.5)/(s[1]+K)-0.5
    rg=d.iloc[ix].groupby('rid').indices
    for rid,loc in rg.items():
        r=[ix[q] for q in loc]
        for i in r:
            sm=0.;c=0
            for j_ in r:
                if j_==i: continue
                a,b=(at[i],at[j_]); p=pair.get((a,b) if a<b else (b,a))
                if p and p[1]>0:
                    v=p[0]/p[1]*(1 if a<b else -1); w=p[1]/(p[1]+3); sm+=w*v; c+=1     # pair değeri: a<b için (e_b-e_a)>0 => a önde
            pw[i]=sm/c if c else 0.; pwc[i]=c
    for i in ix:
        s=jl.get(jk[i],(0,0)); jl[jk[i]]=(s[0]+l2[i],s[1]+1)
        if co_n[i] is not None:
            s=cs.get(co_n[i],(0.,0)); cs[co_n[i]]=(s[0]+(ek[i]-1)/(nn[i]-1),s[1]+1)
        if sr_n[i] is not None:
            s=sr.get(sr_n[i],(0.,0)); sr[sr_n[i]]=(s[0]+(ek[i]-1)/(nn[i]-1),s[1]+1)
    for rid,loc in rg.items():
        r=[ix[q] for q in loc]
        for a_i in range(len(r)):
            for b_i in range(a_i+1,len(r)):
                i,j_=r[a_i],r[b_i]; a,b=at[i],at[j_]
                v=(ek[j_]-ek[i])/(nn[i]-1)
                if a<b: p=pair[(a,b)]; p[0]+=v; p[1]+=1
                else: p=pair[(b,a)]; p[0]+=-v; p[1]+=1
d['jok']=jok;d['coach_e']=coach_e;d['sire_e']=sire_e;d['pw']=pw;d['pwc']=pwc
d['f1']=d.f_v1.fillna(0);d['vyok']=(d.f_v1==0).astype(float)
d['kapir']=(d.kapi-1)/(d.n-1);d['kisa']=(d.mes<1400).astype(float);d['uzun']=(d.mes>=2000).astype(float)
d['f1_rel']=d.f1-d.groupby('rid').f1.transform('mean')
d['gucp']=d.groupby('rid').p.transform('max'); d['gucs']=(d.gucp>d.gucp.median()).astype(float); d['f1_guc']=d.f1*d.gucs
d['yas']=d.yas.fillna(d.yas.median()); d['kilo']=d.kilo.fillna(d.kilo.median()); d['hndf']=d.hnd.fillna(d.hnd.median())
d['pwk']=(d.pwc>0).astype(float)
log('rakip karşılaşma kapsamı (en az 1 önceki ortak koşu olan at oranı):',round(d.pwk.mean(),3),'| ortalama rakip sayısı',round(d.pwc.mean(),2),'| baba bilgisi dolu',round(d.sire.notna().mean(),3))
M0=['f1','vyok','kapir','jok','kisa','uzun']
M1=M0+['yas','kilo','hndf','sire_e','f1_rel','f1_guc','pw','pwk']+['eq_'+t for t in top]

def seq_enc(col):
    st={};out=np.zeros(len(d));v=d[col].values
    for t in sorted(gix):
        ix=gix[t]
        for i in ix:
            if v[i] in st: q=st[v[i]]; out[i]=(q[0]+K*0.5)/(q[1]+K)-0.5
        for i in ix:
            if v[i] is not None and v[i]==v[i]: q=st.get(v[i],(0.,0)); st[v[i]]=(q[0]+(ek[i]-1)/(nn[i]-1),q[1]+1)
    return out
d['fom_e']=seq_enc('fom'); d['fof_e']=seq_enc('fof')
g=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('data/galop/20*.csv.gz'))],ignore_index=True)
g['at']=g['at'].astype(str).str.upper().str.strip(); g['dt']=pd.to_datetime(g['it'])
for c in ('p400','p600'): g['z'+c[1:]]=g.groupby(['hip','pist','tur'])[c].transform(lambda s:(s-s.mean())/(s.std()+1e-9))
vl=400/g.p400; vp=200/(g.p600-g.p400); g['kap']=np.where((g.p600>g.p400)&g.p400.notna(),vl/vp-1,np.nan)
GG={a:(x.dt.values.astype('datetime64[D]'),x.z400.values,x.z600.values,x.kap.values) for a,x in g.sort_values('dt').groupby('at')}
gn=np.zeros(len(d));ggun=np.full(len(d),60.);gz4=np.zeros(len(d));gz6=np.zeros(len(d));gk=np.zeros(len(d));gv=np.zeros(len(d))
dtd=pd.to_datetime(d.tarih).values.astype('datetime64[D]')
for i,a in enumerate(d['at'].astype(str).str.upper().str.strip().values):
    x=GG.get(a)
    if x is None: continue
    lo=np.searchsorted(x[0],dtd[i]-np.timedelta64(45,'D')); hi=np.searchsorted(x[0],dtd[i])   # tarih < t
    if hi<=lo: continue
    gv[i]=1;gn[i]=hi-lo;ggun[i]=(dtd[i]-x[0][hi-1]).astype(int)
    z4=x[1][lo:hi];z6=x[2][lo:hi];kk=x[3][lo:hi]
    gz4[i]=np.nanmin(z4) if np.isfinite(z4).any() else 0; gz6[i]=np.nanmin(z6) if np.isfinite(z6).any() else 0; gk[i]=np.nanmean(kk) if np.isfinite(kk).any() else 0
d['g_n']=gn;d['g_gun']=ggun;d['g_z400']=gz4;d['g_z600']=gz6;d['g_kap']=gk;d['g_var']=gv
log('galop kapsamı (atın son 45 günde ≥1 galobu olan satır oranı):',round(d.g_var.mean(),3),'| test (2026-02→):',round(d[d.tarih>='2026-02-01'].g_var.mean(),3))
M2=M1+['g_n','g_gun','g_z400','g_z600','g_kap','g_var','fom_e','fof_e','coach_e','eqc','arap','sale']
aylar=sorted(set(d.tarih.str[:7])); d['p0']=np.nan;d['p1']=np.nan;d['p2']=np.nan
for ay in aylar:
    if ay<'2026-02': continue
    tr=d[d.tarih<ay+'-01'];te=d.tarih.str[:7]==ay
    for nm,cols in (('p0',M0),('p1',M1),('p2',M2)):
        m=make_pipeline(StandardScaler(),LogisticRegression(C=0.5,max_iter=400)).fit(tr[cols].fillna(0),tr.lead2)
        d.loc[te,nm]=m.predict_proba(d.loc[te,cols].fillna(0))[:,1]
T=d[d.tarih>='2026-02-01'].copy()
log(f'\nTEST {T.rid.nunique()} koşu {T.tarih.nunique()} gün {len(T)} at')
def aucr(df,col):
    o=[]
    for r,x in df.groupby('rid'):
        if x.lead2.sum() in (0,len(x)): continue
        o.append((x.tarih.iloc[0],roc_auc_score(x.lead2,x[col])))
    return o
def bdiff(a,b,B=2000):
    ta=pd.DataFrame(a,columns=['t','a']).groupby('t').a.mean(); tb=pd.DataFrame(b,columns=['t','a']).groupby('t').a.mean(); z=(ta-tb).dropna().values
    bs=[z[rng.integers(0,len(z),len(z))].mean() for _ in range(B)]; return round(z.mean(),4),np.percentile(bs,[2.5,97.5]).round(4).tolist()
a0=aucr(T,'p0');a1=aucr(T,'p1')
log('AT DÜZEYİ koşu-içi AUC: M0',round(np.mean([x[1] for x in a0]),4),'M1',round(np.mean([x[1] for x in a1]),4),'| M1−M0',bdiff(a1,a0))
# alt küme: rakip karşılaşması olan atları çok içeren koşular
T['kos_pwk']=T.groupby('rid').pwk.transform('mean'); hi=T[T.kos_pwk>=T.kos_pwk.median()]
ah0=aucr(hi,'p0');ah1=aucr(hi,'p1'); log('rakip karşılaşma kapsamı yüksek yarı koşular: M0',round(np.mean([x[1] for x in ah0]),4),'M1',round(np.mean([x[1] for x in ah1]),4),'| fark',bdiff(ah1,ah0))
def top1(col): return np.mean([int(x.loc[x[col].idxmax(),'lead1']) for _,x in T.groupby('rid')])
log('1. öncüyü bulma isabeti M0',round(top1('p0'),3),'M1',round(top1('p1'),3),'rastgele',round((1/T.groupby('rid').n.first()).mean(),3))

a2=aucr(T,'p2')
log('\nT121-A AT DÜZEYİ (test 2026-02→): AUC M0',round(np.mean([x[1] for x in a0]),4),'M1',round(np.mean([x[1] for x in a1]),4),'M2',round(np.mean([x[1] for x in a2]),4))
log('M2−M1',bdiff(a2,a1),'| M2−M0',bdiff(a2,a0),'| M1−M0',bdiff(a1,a0))
ag=T[T.g_var==1]; ag0=aucr(ag,'p0');ag1=aucr(ag,'p1');ag2=aucr(ag,'p2'); log('galobu olan atlar (alt küme) M0/M1/M2',round(np.mean([x[1] for x in ag0]),4),round(np.mean([x[1] for x in ag1]),4),round(np.mean([x[1] for x in ag2]),4),'M2−M1',bdiff(ag2,ag1))
def top1b(col): return np.mean([int(x.loc[x[col].idxmax(),'lead1']) for _,x in T.groupby('rid')])
log('1. öncüyü bulma M0',round(top1b('p0'),3),'M1',round(top1b('p1'),3),'M2',round(top1b('p2'),3))
mm=make_pipeline(StandardScaler(),LogisticRegression(C=0.5,max_iter=400)).fit(d[d.tarih<'2026-02-01'][M2].fillna(0),d[d.tarih<'2026-02-01'].lead2)
log('M2 standardize katsayılar:',[(a,round(float(b),3)) for a,b in sorted(zip(M2,mm[-1].coef_[0]),key=lambda x:-abs(x[1]))[:14]])
log('\nBİTTİ')
