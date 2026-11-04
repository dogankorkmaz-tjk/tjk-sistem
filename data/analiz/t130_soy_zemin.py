"""T130: soy–zemin uyumu (baba/anne babası/anne ıslak−kuru piyasa artığı); hipotez_defteri.md ön kaydı"""
import sys,glob,json,gzip,os,collections,numpy as np,pandas as pd
rng=np.random.default_rng(130)
def log(*a): print(*a,flush=True)
THR=12.5   # T-ıslak vekil sonucu: 3 günlük yağış eşiği (Youden)
H=pd.read_csv('data/hava/gunluk.csv'); H['tarih']=H.tarih.astype(str); H=H.sort_values(['hipodrom','tarih'])
H['p3']=H.groupby('hipodrom').yagis_mm.transform(lambda s:s.rolling(3,min_periods=1).sum()); H['islak']=(H.p3>=THR).astype(int)
fs=sorted(glob.glob('data/temiz/20*.csv.gz'))
d=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
d=d[(d.kosmadi!=True)&d.p_piyasa.notna()&d.kazandi.notna()&d.sira.notna()].copy()
PS={};SIRE={};DSIRE={};DAM={};HIPK={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=os.path.basename(f)[:10]
    try: j=json.load(gzip.open(f))
    except Exception: continue
    for hip,ks in (j.get('program') or {}).items():
        for k in ks:
            try: kn=int(k['number']); PS[(t,hip,kn)]=k.get('raceCourseType')
            except Exception: continue
            for h in k.get('horses',[]):
                try:
                    key=(t,hip,kn,int(h['number'])); p=h.get('parents') or {}
                    SIRE[key]=(p.get('father') or {}).get('name'); DSIRE[key]=(p.get('fatherOfMother') or {}).get('name'); DAM[key]=(p.get('mother') or {}).get('name')
                except Exception: pass
k4=list(zip(d.tarih,d.hipodrom,d.kosu,d.no))
d['sire']=[SIRE.get(k) for k in k4]; d['dsire']=[DSIRE.get(k) for k in k4]; d['dam']=[DAM.get(k) for k in k4]
d['pist']=[PS.get((t,h,k)) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d=d.merge(H[['tarih','hipodrom','islak']],on=['tarih','hipodrom'],how='left'); d=d[d.islak.notna()&d.pist.notna()].copy()
d['rid']=d.tarih+'|'+d.hipodrom+'|'+d.kosu.astype(str); d['n']=d.groupby('rid').no.transform('count'); d=d[d.n>=5].copy()
d['p']=d.p_piyasa/d.groupby('rid').p_piyasa.transform('sum'); d['lp']=np.log(d.p); d['y']=d.lp-d.groupby('rid').lp.transform('mean')
rk=d.groupby('rid').p.rank(ascending=False,method='first'); d['res']=(((rk-1)-(d.sira-1))/(d.n-1)).clip(-1,1)   # piyasa sıralamasına göre artık, [-1,1]
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
log('at',len(d),'koşu',d.rid.nunique(),'ıslak vekil koşu',d[d.islak==1].rid.nunique(),'| pist türleri',d.pist.value_counts().to_dict())
# sıralı özellik: (baba, pist, ıslak) artık toplamı; ıslak−kuru fark, K=20 önsel
K=20.
acc={n:collections.defaultdict(lambda:[0.,0]) for n in ('sire','dsire','dam')}
F={n:np.full(len(d),np.nan) for n in ('sire','dsire','dam')}
byday=d.groupby('tarih').indices
for t in sorted(byday):
    ix=byday[t]
    for i in ix:
        r=d.iloc[i]
        for n in ('sire','dsire','dam'):
            a=getattr(r,n)
            if a is None or (isinstance(a,float) and np.isnan(a)): continue
            sw,nw=acc[n][(a,r.pist,1)]; sd,nd=acc[n][(a,r.pist,0)]
            F[n][i]=sw/(nw+K)-sd/(nd+K)
    for i in ix:
        r=d.iloc[i]
        for n in ('sire','dsire','dam'):
            a=getattr(r,n)
            if a is None or (isinstance(a,float) and np.isnan(a)): continue
            v=acc[n][(a,r.pist,int(r.islak))]; v[0]+=r.res; v[1]+=1
for n in F: d[n+'_wet']=np.nan_to_num(F[n]); 
d['soy_wet']=0.5*d.sire_wet+0.5*d.dsire_wet
# yardımcı kontroller (T129'dakinin kısaltılmışı)
ph={};pj=collections.defaultdict(lambda:[0.,0]);d['form5']=np.nan;d['jok']=np.nan;d['nk']=0.
for t in sorted(byday):
    for i in byday[t]:
        r=d.iloc[i]; h=ph.get(r['at'],[]); d.at[i,'form5']=np.mean(h[-5:]) if h else 0.; d.at[i,'nk']=np.log1p(len(h)); w,n=pj[r.jokey]; d.at[i,'jok']=(w+0.5)/(n+5)
    for i in byday[t]:
        r=d.iloc[i]; ph.setdefault(r['at'],[]).append(r.kazandi-r.p); pj[r.jokey][0]+=r.kazandi; pj[r.jokey][1]+=1
d['hnd_r']=d.hnd-d.groupby('rid').hnd.transform('mean'); d['kilo_r']=d.kilo-d.groupby('rid').kilo.transform('mean')
d['ay']=d.tarih.str[:7]; T=d[d.ay>='2025-01'].copy()    # değerlendirme: yeterli soy geçmişi için
# Test 1: koşu içi doğrusal model, ıslak ve kuru koşularda ayrı
def fe(D,cols):
    M=D[cols].values.astype(float); M=M-pd.DataFrame(M).groupby(D.rid.values).transform('mean').values; Y=D.y.values-D.groupby('rid').y.transform('mean').values
    s=M.std(0); s[s==0]=1; M=M/s; ud,di=np.unique(D.tarih.values,return_inverse=True)
    def ols(w): XtW=M.T*w; return np.linalg.solve(XtW@M+1e-6*np.eye(len(cols)),XtW@Y)
    b0=ols(np.ones(len(D))); B=np.array([ols(np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud))[di].astype(float)) for _ in range(500)])
    return b0,np.percentile(B,[2.5,97.5],axis=0)
cols=['sire_wet','dsire_wet','dam_wet','form5','jok','nk','hnd_r','kilo_r']
for ad,D in (('ISLAK',T[T.islak==1]),('KURU (kontrol)',T[T.islak==0])):
    b,ci=fe(D,cols); log('TEST 1',ad,'koşu',D.rid.nunique(),'at',len(D)); 
    for c,x,l,h in zip(cols,b,ci[0],ci[1]): log(f'   {c:10s} {x:+.4f} [{l:+.4f},{h:+.4f}]')
# Test 2: piyasa ofseti + c·soy_wet, ıslak koşularda (kayıtlı ana test)
def test2(D,col,etiket):
    D=D.sort_values('rid').reset_index(drop=True); ri=np.unique(D.rid.values,return_inverse=True)[1]; st=np.r_[0,np.flatnonzero(np.diff(ri))+1]; cnt=np.diff(np.r_[st,len(D)])
    lp=D.lp.values; x=(D[col].values-D[col].mean()); sd=x.std() if x.std()>0 else 1; x=x/sd; win=(D.kazandi.values==1); has=np.add.reduceat(win.astype(int),st)==1
    day=D.groupby('rid').tarih.first().reindex(np.unique(D.rid.values)).values; ud,di=np.unique(day,return_inverse=True)
    def fitc(w,c=0.):
        for _ in range(30):
            z=lp+c*x; zm=np.maximum.reduceat(z,st); e=np.exp(z-np.repeat(zm,cnt)); s=e/np.repeat(np.add.reduceat(e,st),cnt)
            m1=np.add.reduceat(s*x,st); m2=np.add.reduceat(s*x*x,st); aw=np.add.reduceat(x*win,st)
            g=(w*has*(aw-m1)).sum(); h=-(w*has*(m2-m1**2)).sum()
            if abs(h)<1e-12: break
            c-=g/h
            if abs(g/h)<1e-8: break
        return c
    c0=fitc(np.ones(len(st))); B=[fitc(np.bincount(rng.integers(0,len(ud),len(ud)),minlength=len(ud))[di].astype(float),c0) for _ in range(1000)]
    lo,hi=np.percentile(B,[2.5,97.5]); log(f'TEST 2 {etiket} [{col}] koşu {has.sum()} | c (1 SS) = {c0:+.4f}  95% GA [{lo:+.4f},{hi:+.4f}]','=> ALT GA>0: piyasa EKSİK fiyatlıyor' if lo>0 else '=> GA 0\'ı kapsıyor/altında: kanıt yok')
Wt=T[T.islak==1]
test2(Wt,'soy_wet','ANA TEST (ıslak koşular, kayıtlı soy_wet=0,5 baba+0,5 anne babası)')
for c in ('sire_wet','dsire_wet','dam_wet'): test2(Wt,c,'betimleyici')
test2(T[T.islak==0],'soy_wet','kontrol (kuru koşular)')
# kum/çim ayrı (betimleyici)
for p in ('Kum','Çim'):
    S=Wt[Wt.pist.astype(str).str.contains(p[:2],case=False)]
    if S.rid.nunique()>=100: test2(S,'soy_wet','betimleyici '+p)
log('BİTTİ')
