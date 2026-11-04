"""T120: tempo / öncü sayısı öngörülebilir mi + zengin at özellikleri (hipotez_defteri.md ön kaydı)."""
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
G={};MS={};PS={};SIRE={};EQ={};AGE={}
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
                    key=(t,hip,kn,int(h['number'])); G[key]=h.get('start'); EQ[key]=(h.get('equipment') or '').split()
                    SIRE[key]=((h.get('parents') or {}).get('father') or {}).get('name'); a=str(h.get('age') or '').split('y')[0]; AGE[key]=float(a) if a.strip().isdigit() else np.nan
                except Exception: pass
key4=list(zip(d.tarih,d.hipodrom,d.kosu,d.no))
d['kapi']=[G.get(k,np.nan) for k in key4]; d['sire']=[SIRE.get(k) for k in key4]; d['yas']=[AGE.get(k,np.nan) for k in key4]; d['eq']=[EQ.get(k,[]) for k in key4]
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
d['e_erken']=[E.get(k,np.nan) for k in key4]; d=d[d.e_erken.notna()].copy()
d['rid']=d.tarih+'|'+d.hipodrom+'|'+d.kosu.astype(str)
d['n']=d.groupby('rid').no.transform('count'); d=d[d.n>=5].copy()
d['p']=d.p_piyasa/d.groupby('rid').p_piyasa.transform('sum')
d['rk']=d.groupby('rid').e_erken.rank(method='min'); d['lead2']=(d.rk<=2).astype(int); d['lead1']=(d.rk<=1).astype(int)
d=d[d.kapi.notna()&d.mes.notna()&d.pist.notna()].copy()
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
log('at',len(d),'koşu',d.rid.nunique(),'gün',d.tarih.nunique())
# ekipman jetonları
cnt=collections.Counter(t for l in d.eq for t in set(l)); top=[t for t,_ in cnt.most_common(15)]; log('ekipman jetonları',top)
for t in top: d['eq_'+t]=[int(t in l) for l in d.eq]
# sıralı özellikler: jokey öncü oranı, baba eğilimi, ikili karşılaşmalar
K=20; jl={};sr={};pair=collections.defaultdict(lambda:[0.,0]);glob_rate=d.lead2.mean()
n=len(d);jok=np.zeros(n);sire_e=np.zeros(n);pw=np.zeros(n);pwc=np.zeros(n);fstr=np.zeros(n)
tarih=d.tarih.values;jk=d.jokey.values;at=d['at'].values;sr_n=d.sire.values;ek=d.e_erken.values;nn=d.n.values;l2=d.lead2.values
gix=d.groupby('tarih').indices
for t in sorted(gix):
    ix=gix[t]
    for i in ix:
        s=jl.get(jk[i],(0,0)); jok[i]=(s[0]+5*glob_rate)/(s[1]+5)-glob_rate
        if sr_n[i] in sr: s=sr[sr_n[i]]; sire_e[i]=(s[0]+K*0.5)/(s[1]+K)-0.5
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
d['jok']=jok;d['sire_e']=sire_e;d['pw']=pw;d['pwc']=pwc
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
R=T.groupby('rid').agg(tarih=('tarih','first'),n=('n','first'),mes=('mes','first'),pist=('pist','first'),sp0=('p0','sum'),mp0=('p0','max'),sp1=('p1','sum'),mp1=('p1','max'),nf=('f1',lambda s:(s<-0.12).sum())).reset_index()
R['H1']=[RH.get(tuple([r.split('|')[0],r.split('|')[1],int(r.split('|')[2])]),(np.nan,)*3)[0] for r in R.rid]
R['H3']=[RH.get(tuple([r.split('|')[0],r.split('|')[1],int(r.split('|')[2])]),(np.nan,)*3)[1] for r in R.rid]
R['H2']=[RH.get(tuple([r.split('|')[0],r.split('|')[1],int(r.split('|')[2])]),(np.nan,)*3)[2] for r in R.rid]
R['band']=pd.cut(R.mes,[0,1399,1799,2199,9999],labels=False); R['pc']=(R.pist=='Çim').astype(float);R['ps']=(R.pist=='Sentetik').astype(float)
# H2: mesafe bandı × pist grubu içi z
R['grp']=R.band.astype(str)+R.pist.astype(str); R['H2z']=R.groupby('grp').H2.transform(lambda s:(s-s.mean())/(s.std()+1e-9))
R=R.sort_values('tarih').reset_index(drop=True); R['ay']=R.tarih.str[:7]
S0=['n','mes','pc','ps'];S1=S0+['sp0','mp0','nf'];S2=S0+['sp1','mp1','nf']
def spear_boot(R,hedef,P,B=1500):
    ok=R[R[hedef].notna()].copy(); ay=sorted(ok.ay.unique()); out={}
    pr={k:np.full(len(ok),np.nan) for k in P}
    for a in ay:
        if a<'2025-12': continue          # ilk 2 ay yalnız eğitim (yarış düzeyi yürüyüş)
        tr=ok[ok.ay<a];te=(ok.ay==a).values
        if len(tr)<300: continue
        for k,cols in P.items():
            m=LinearRegression().fit(tr[cols],tr[hedef]); pr[k][te]=m.predict(ok.loc[te,cols])
    m=~np.isnan(pr['S0']); ok=ok[m].reset_index(drop=True); y=ok[hedef].rank().values
    rk={k:pd.Series(v[m]).rank().values for k,v in pr.items()}
    def cor(a,b): return np.corrcoef(a,b)[0,1]
    pt={k:cor(y,v) for k,v in rk.items()}
    days=ok.tarih.values; ud=np.unique(days); di={t:np.where(days==t)[0] for t in ud}
    diffs={'S1-S0':[],'S2-S0':[],'S2-S1':[]}
    for _ in range(B):
        ix=np.concatenate([di[t] for t in rng.choice(ud,len(ud))]); yy=pd.Series(ok[hedef].values[ix]).rank().values
        c={k:cor(yy,pd.Series(pr[k][m][ix]).rank().values) for k in rk}
        diffs['S1-S0'].append(c['S1']-c['S0']);diffs['S2-S0'].append(c['S2']-c['S0']);diffs['S2-S1'].append(c['S2']-c['S1'])
    return len(ok),pt,{k:(round(pt[k.split('-')[0]]-pt[k.split('-')[1]],4),np.percentile(v,[2.5,97.5]).round(4).tolist()) for k,v in diffs.items()}
log('\nYARIŞ DÜZEYİ (Spearman ρ; S0 yapı tabanı, S1 = +M0 öncü özetleri, S2 = +M1 zengin özetler; aylık yürüyüş, test 2025-12→)')
for h,ad in (('H1','H1 farklı lider sayısı (ilk %25)'),('H3','H3 farklı ilk-2 at sayısı (ilk %25)'),('H2z','H2 tempo (400m sönme, grup içi z)')):
    n_,pt,df=spear_boot(R,h,{'S0':S0,'S1':S1,'S2':S2})
    log(f"{ad} | koşu {n_} | ρ S0 {pt['S0']:.3f} S1 {pt['S1']:.3f} S2 {pt['S2']:.3f} | S1−S0 {df['S1-S0']} S2−S0 {df['S2-S0']} S2−S1 {df['S2-S1']}")
log('hedef dağılımları: H1',R.H1.value_counts().sort_index().to_dict(),'H3',R.H3.value_counts().sort_index().to_dict())
log('\nBİTTİ')
