"""T123 (T122 türevi): hücre içi tempo / öncü sayısı öngörülebilir mi + zengin at özellikleri (hipotez_defteri.md ön kaydı)."""
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
G={};MS={};PS={};SIRE={};EQ={};AGE={};CINS={};COACH={};EQC={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=os.path.basename(f)[:10]
    if t<'2024-10-01': continue
    try: j=json.load(gzip.open(f))
    except Exception: continue
    for hip,ks in (j.get('program') or {}).items():
        for k in ks:
            try: kn=int(k['number']); MS[(t,hip,kn)]=float(k.get('distance') or np.nan); PS[(t,hip,kn)]=k.get('raceCourseType'); CINS[(t,hip,kn)]=k.get('typeDescription')
            except Exception: continue
            for h in k.get('horses',[]):
                try:
                    key=(t,hip,kn,int(h['number'])); G[key]=h.get('start'); COACH[key]=((h.get('coach') or {}).get('shortName')); ec=h.get('equipmentChanges') or {}; EQC[key]=len(ec.get('added') or [])+len(ec.get('removed') or []); EQ[key]=(h.get('equipment') or '').split()
                    SIRE[key]=((h.get('parents') or {}).get('father') or {}).get('name'); a=str(h.get('age') or '').split('y')[0]; AGE[key]=float(a) if a.strip().isdigit() else np.nan
                except Exception: pass
key4=list(zip(d.tarih,d.hipodrom,d.kosu,d.no))
d['kapi']=[G.get(k,np.nan) for k in key4]; d['sire']=[SIRE.get(k) for k in key4]; d['yas']=[AGE.get(k,np.nan) for k in key4]; d['ekp']=[EQ.get(k,[]) for k in key4]; d['coach']=[COACH.get(k) for k in key4]; d['eqc']=[EQC.get(k,0) for k in key4]; d['cins']=[CINS.get((k[0],k[1],k[2])) for k in key4]
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
aylar=sorted(set(d.tarih.str[:7])); d['p0']=np.nan;d['p1']=np.nan
for ay in aylar:
    if ay<'2025-04': continue
    tr=d[d.tarih<ay+'-01'];te=d.tarih.str[:7]==ay
    for nm,cols in (('p0',M0),('p1',M1)):
        m=make_pipeline(StandardScaler(),LogisticRegression(C=0.5,max_iter=400)).fit(tr[cols].fillna(0),tr.lead2)
        d.loc[te,nm]=m.predict_proba(d.loc[te,cols].fillna(0))[:,1]
T=d[d.tarih>='2025-10-01'].copy()
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
# katsayılar (M1, tüm veri) — hangi özellik taşıyor
mm=make_pipeline(StandardScaler(),LogisticRegression(C=0.5,max_iter=400)).fit(d[d.tarih<'2025-10-01'][M1].fillna(0),d[d.tarih<'2025-10-01'].lead2)
co=sorted(zip(M1,mm[-1].coef_[0]),key=lambda x:-abs(x[1])); log('M1 standardize katsayılar (eğitim<2025-10):',[(a,round(b,3)) for a,b in co[:12]])
# yarış düzeyi


from sklearn.ensemble import HistGradientBoostingRegressor
W=d[d.sira==1].groupby('rid').derece_sn.first()
A=d[d.tarih>='2025-04-01'].copy(); A['dusuk']=(A.f1<-0.2).astype(int)
R=A.groupby('rid').agg(tarih=('tarih','first'),hip=('hipodrom','first'),cins=('cins','first'),n=('n','first'),mes=('mes','first'),pist=('pist','first'),yas=('yas','mean'),kilo=('kilo','mean'),hnd=('hndf','mean'),
    sp0=('p0','sum'),mp0=('p0','max'),sp1=('p1','sum'),mp1=('p1','max'),nf=('dusuk','sum'),f1min=('f1','min'),f1ort=('f1','mean'),f1std=('f1','std'),
    cmin=('coach_e','min'),cort=('coach_e','mean'),jmax=('jok','max'),eqc=('eqc','sum'),pwk=('pwk','mean')).reset_index()
rhx=lambda r,i:RH.get((r.split('|')[0],r.split('|')[1],int(r.split('|')[2])),(np.nan,)*3)[i]
R['H2']=[rhx(r,2) for r in R.rid]; R['W']=R.rid.map(W)
R['cell']=R.hip+'|'+R.pist.astype(str)+'|'+(R.mes/100).round().astype('Int64').astype(str)
cs=R.groupby('cell').rid.transform('count'); R=R[cs>=20].copy()
for h in ('H2','W'): R[h+'c']=R.groupby('cell')[h].transform(lambda s:(s-s.mean())/(s.std()+1e-9))
R['cins_k']=R.cins.astype('category').cat.codes
R=R.sort_values('tarih').reset_index(drop=True); R['ay']=R.tarih.str[:7]
S0=['n'];S3=S0+['cins_k','yas','kilo','hnd'];S4=S3+['sp0','mp0','nf','f1min','f1ort','f1std','cmin','cort','jmax','eqc','sp1','mp1']
def spear_boot2(R,hedef,P,B=1500):
    ok=R[R[hedef].notna()].copy().reset_index(drop=True); pr={k:np.full(len(ok),np.nan) for k in P}
    for a in sorted(ok.ay.unique()):
        if a<'2025-12': continue
        tr=ok[ok.ay<a];te=(ok.ay==a).values
        if len(tr)<300: continue
        for k,cols in P.items():
            m=HistGradientBoostingRegressor(max_depth=3,learning_rate=0.05,max_iter=150,min_samples_leaf=40,random_state=0).fit(tr[cols],tr[hedef]); pr[k][te]=m.predict(ok.loc[te,cols])
    m=~np.isnan(pr['S0']); ok=ok[m].reset_index(drop=True); y=ok[hedef].rank().values; rk={k:pd.Series(v[m]).rank().values for k,v in pr.items()}
    cor=lambda a,b:np.corrcoef(a,b)[0,1]; pt={k:cor(y,v) for k,v in rk.items()}
    days=ok.tarih.values;ud=np.unique(days);di={t:np.where(days==t)[0] for t in ud}; pairs=[('S3','S0'),('S4','S3'),('S4','S0')]; diffs={p:[] for p in pairs}
    for _ in range(B):
        ix=np.concatenate([di[t] for t in rng.choice(ud,len(ud))]); yy=pd.Series(ok[hedef].values[ix]).rank().values; c={k:cor(yy,pd.Series(pr[k][m][ix]).rank().values) for k in rk}
        for a_,b_ in pairs: diffs[(a_,b_)].append(c[a_]-c[b_])
    return len(ok),pt,{f'{a_}-{b_}':(round(pt[a_]-pt[b_],4),np.percentile(v,[2.5,97.5]).round(4).tolist()) for (a_,b_),v in diffs.items()}
log('\nT123 HÜCRE İÇİ HEDEFLER (hücre = hipodrom×pist×mesafe, ≥20 koşu): koşu',len(R),'hücre',R.cell.nunique())
for h,ad in (('H2c','H2c tempo sönmesi hücre içi z'),('Wc','H5 kazanan derecesi hücre içi z (yüksek = yavaş)')):
    n_,pt,df=spear_boot2(R,h,{'S0':S0,'S3':S3,'S4':S4})
    log(f"{ad} | koşu {n_} | ρ S0 {pt['S0']:.3f} S3 {pt['S3']:.3f} S4 {pt['S4']:.3f} | S3−S0 {df['S3-S0']} S4−S3 {df['S4-S3']} S4−S0 {df['S4-S0']}")
log('\nBİTTİ')
