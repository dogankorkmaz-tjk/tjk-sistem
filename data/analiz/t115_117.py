"""T115 öncü tahmini, T116 piyasa hata atlası, T117 beklenmedik koşan at etiketleri — hipotez_defteri.md ön kaydına göre (4 Kasım 2026)."""
import sys,glob,json,gzip,os,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
rng=np.random.default_rng(115)
def log(*a): print(*a,flush=True)
# 1) veri
fs=[f for f in sorted(glob.glob('data/temiz/20*.csv.gz')) if os.path.basename(f)[:7]>='2024-10']
d=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
d=d[(d.kosmadi!=True)&d.p_piyasa.notna()&d.kazandi.notna()].copy()
# start (kapı) + mesafe: atyarisi arşivi program
G={};MS={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=os.path.basename(f)[:10]
    if t<'2024-10-01': continue
    try: j=json.load(gzip.open(f))
    except Exception: continue
    for hip,ks in (j.get('program') or {}).items():
        for k in ks:
            try: MS[(t,hip,int(k['number']))]=float(k.get('distance') or np.nan)
            except Exception: pass
            for h in k.get('horses',[]):
                try: G[(t,hip,int(k['number']),int(h['number']))]=h.get('start')
                except Exception: pass
d['kapi']=[G.get((t,h,k,n),np.nan) for t,h,k,n in zip(d.tarih,d.hipodrom,d.kosu,d.no)]
d['mes']=[MS.get((t,h,k),np.nan) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
log('arşivden kapı dolu oran',round(d.kapi.notna().mean(),3),'mesafe',round(d.mes.notna().mean(),3))
d=VO.ekle(d)
# 2) video hedef: erken sıra
E={}
for f in glob.glob('data/video_seyir/20*.json'):
    b=os.path.basename(f)[:-5].split('_')
    if len(b)!=3: continue
    try: j=json.load(open(f))
    except Exception: continue
    if j.get('okuyucu')!='rakam1' or not j.get('ozet'): continue
    for no,o in j['ozet'].items(): E[(b[0],b[1],int(b[2]),int(no))]=(o['erken'],o.get('orta'),o.get('gec'),o.get('son'),len(j['ozet']))
for i,c in enumerate(['e_erken','e_orta','e_gec','e_son','nv']): d[c]=[E.get((t,h,k,n),(np.nan,)*5)[i] for t,h,k,n in zip(d.tarih,d.hipodrom,d.kosu,d.no)]
d=d[d.e_erken.notna()].copy()
d['rid']=d.tarih+'|'+d.hipodrom+'|'+d.kosu.astype(str)
d['p']=d.p_piyasa/d.groupby('rid').p_piyasa.transform('sum')
d['n']=d.groupby('rid').no.transform('count')
d['rk']=d.groupby('rid').e_erken.rank(method='min')
d['lead1']=(d.rk<=1).astype(int); d['lead2']=(d.rk<=2).astype(int)
d=d[d.n>=5].copy()
log('video-hedefli at',len(d),'koşu',d.rid.nunique(),'gün',d.tarih.nunique(),'| ilk tarih',d.tarih.min(),'son',d.tarih.max())
# 3) T115: jokey öncü oranı (önceki günler, büzmeli) + yürüyüş
d=d.sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
jl={};jr=np.zeros(len(d))
glob_rate=d.lead2.mean()
for t,ix in d.groupby('tarih').indices.items():
    for i in ix:
        s=jl.get(d.jokey.values[i],(0,0)); jr[i]=(s[0]+5*glob_rate)/(s[1]+5)-glob_rate
    for i in ix:
        s=jl.get(d.jokey.values[i],(0,0)); jl[d.jokey.values[i]]=(s[0]+d.lead2.values[i],s[1]+1)
d['jok']=jr
d['kapir']=(d.kapi-1)/(d.n-1)
d['kapi_ok']=d.kapi.notna()
d['kisa']=(d.mes<1400).astype(float); d['uzun']=(d.mes>=2000).astype(float)
d['f1']=d.f_v1.fillna(0)
d['vyok']=(d.f_v1==0).astype(float)
test=d[d.tarih>='2025-10-01'].copy()
FE={'model':['f1','vyok','kapir','jok','kisa','uzun'],'kapi':['kapir']}
def auc_ric(df,col):
    a=[]
    for r,x in df.groupby('rid'):
        if x.lead2.sum() in (0,len(x)): continue
        a.append((x.tarih.iloc[0],roc_auc_score(x.lead2,x[col])))
    return a
def boot(a,b,B=2000):
    ta=pd.DataFrame(a,columns=['t','a']).groupby('t').a.mean(); tb=pd.DataFrame(b,columns=['t','a']).groupby('t').a.mean()
    z=(ta-tb).dropna().values; m=z.mean()
    bs=[z[rng.integers(0,len(z),len(z))].mean() for _ in range(B)]
    return round(m,4),np.percentile(bs,[2.5,97.5]).round(4).tolist(),len(z)
res={}
for tgt in ('lead2','lead1'):
    preds={k:np.full(len(d),np.nan) for k in FE}
    aylar=sorted(set(test.tarih.str[:7]))
    for ay in aylar:
        tr=d[(d.tarih<ay+'-01')&d.kapi_ok]; te=(d.tarih.str[:7]==ay)
        for k,cols in FE.items():
            m=LogisticRegression(C=1.0,max_iter=300).fit(tr[cols].fillna(0),tr[tgt])
            preds[k][te.values]=m.predict_proba(d.loc[te,cols].fillna(0))[:,1]
    for k in FE: d[f'{tgt}_{k}']=preds[k]
test=d[d.tarih>='2025-10-01'].copy(); test=test[test.kapi_ok]
log(f'\nT115 test: {test.rid.nunique()} koşu, {test.tarih.nunique()} gün, {len(test)} at')
test['rnd']=rng.random(len(test))
a_m=auc_ric(test.assign(lead2=test.lead2),'lead2_model'); a_k=auc_ric(test,'lead2_kapi'); a_r=auc_ric(test,'rnd')
log('koşu-içi AUC (öncü=ilk2 erken sıra): model',round(np.mean([x[1] for x in a_m]),4),'kapı',round(np.mean([x[1] for x in a_k]),4),'rastgele',round(np.mean([x[1] for x in a_r]),4))
b=boot(a_m,a_k); log('AUC(model)−AUC(kapı):',b[0],'GA',b[1],'gün',b[2]); T115_gecti=b[1][0]>0
def isabet(col,tg):
    h=[];
    for r,x in test.groupby('rid'): h.append((x.tarih.iloc[0],int(x.loc[x[col].idxmax(),tg])))
    return np.mean([y for _,y in h]),len(h)
for tg,col in (('lead1','lead1_model'),):
    log('ilk-1 isabeti model',isabet(col,'lead1'),'kapı',isabet('lead1_kapi','lead1'),'rastgele beklenen',round((1/test.groupby('rid').n.first()).mean(),4))
# öncü sayısı
sg=test.groupby('rid').agg(g=('lead2','sum'),s=('lead2_model','sum')); log('Σp ile gerçek öncü sayısı korelasyonu (ilk2 hedefinde sabit ~2, bilgi yok):',round(sg.corr().iloc[0,1],3) if sg.g.std()>0 else 'sabit')
# stil-öncü sayısı: f1<-0.12 olan at sayısı
test['onc']=(test.f1<-0.12).astype(int); sg2=test.groupby('rid').agg(g=('e_erken',lambda s:(s<=2.5).sum()),s=('onc','sum')); log('gerçek (erken sıra ≤2,5) öncü sayısı vs stil-öncü sayısı korelasyonu:',round(sg2.corr().iloc[0,1],3))
log('KARAR T115:','anlamlı' if T115_gecti else 'anlamlı değil → T118 YAPILMAZ')
# 4) T116 piyasa hata atlası (tüm video-hedefli veri, iki yarı)
A=d[(d.f1!=0)].copy()
mid=sorted(A.tarih.unique())[len(A.tarih.unique())//2]
A['yari']=np.where(A.tarih<mid,1,2)
A['stil']=np.where(A.f1<-0.12,'öncü',np.where(A.f1>0.12,'kapanış','orta'))
A['kapig']=pd.cut(A.kapir,[-0.01,0.34,0.67,1.01],labels=['iç','orta','dış'])
A['band']=pd.cut(A.mes,[0,1399,1999,9999],labels=['kısa','orta','uzun'])
A['oran']=pd.cut(A.p,[0,0.05,0.12,0.25,1],labels=['uzun(<5%)','orta-uzun','orta','favori(≥25%)'])
A['hnd_b']=pd.cut(A.hnd,[-1,45,55,65,200],labels=['≤45','46-55','56-65','>65'])
# jokey sınıfı: önceki 90 gün piyasa-üstü: basit — jokey genel O/E önceki günler
jo={};jt=np.zeros(len(A));A=A.sort_values('tarih').reset_index(drop=True)
for t,ix in A.groupby('tarih').indices.items():
    for i in ix:
        s=jo.get(A.jokey.values[i],(0.,0.)); jt[i]=(s[0]+2)/(s[1]+2)
    for i in ix:
        s=jo.get(A.jokey.values[i],(0.,0.)); jo[A.jokey.values[i]]=(s[0]+A.kazandi.values[i],s[1]+A.p.values[i])
A['jokoe']=jt; q=A.jokoe.quantile([.33,.67]).values; A['jok_s']=np.where(A.jokoe<q[0],'alt',np.where(A.jokoe<q[1],'orta','üst'))
def oe(S):
    if len(S)<30: return None
    a=np.array([(x.kazandi.sum(),x.p.sum()) for _,x in S.groupby('tarih')]); pt=a[:,0].sum()/a[:,1].sum()
    bs=[(lambda ix:a[ix,0].sum()/a[ix,1].sum())(rng.integers(0,len(a),len(a))) for _ in range(1500)]
    return len(S),int(S.kazandi.sum()),round(S.p.sum(),1),pt,bs
gr=[('stil',s) for s in A.stil.unique()]+[('kapig',s) for s in A.kapig.dropna().unique()]+[('band',s) for s in A.band.dropna().unique()]+[('oran',s) for s in A.oran.dropna().unique()]+[('hnd_b',s) for s in A.hnd_b.dropna().unique()]+[('jok_s',s) for s in A.jok_s.unique()]
k=len(gr); lo,hi=2.5/k,100-2.5/k
log(f'\nT116: {len(A)} at, {A.rid.nunique()} koşu, bölme tarihi {mid}, grup sayısı {k} (Bonferroni %{100-5/k:.2f} GA)')
log('grup | n | kazanan | beklenen | O/E | GA(Bonf) | yarı1 O/E | yarı2 O/E | aday?')
for c,v in gr:
    S=A[A[c]==v]; r=oe(S)
    if not r: continue
    n,w,e,pt,bs=r; ga=np.percentile(bs,[lo,hi]).round(2); y=[ (lambda x:x.kazandi.sum()/x.p.sum())(S[S.yari==h]) if (S.yari==h).sum()>0 else np.nan for h in (1,2)]
    aday = n>=300 and ((ga[1]<1 and y[0]<1 and y[1]<1) or (ga[0]>1 and y[0]>1 and y[1]>1))
    log(f'{c}={v} | {n} | {w} | {e} | {pt:.3f} | {ga.tolist()} | {y[0]:.3f} | {y[1]:.3f} | {"ADAY" if aday else "-"}')
# 5) T117 etiketler: önceki koşu etiketi → 60 gün içindeki SONRAKİ koşu O/E
d=d.sort_values(['at','tarih']).reset_index(drop=True)
d['pl']=d.e_gec.fillna(d.e_son); d['bit']=d.sira
d['et_a']=((d.e_orta<=3)&(d.bit>d.n/2)).astype(int)                 # tempo kurbanı
d['et_b']=(((d.e_orta-d.e_son)>=4)&(d.bit>3)).astype(int)            # geç kapanan (son parça kazancı ≥4, ilk3 dışı)
d['et_c']=((d.bit<=3)&(d.p<=0.05)).astype(int)                      # beklenenden iyi
d['et_d']=((d.p>=0.25)&(d.bit>5)).astype(int)                       # beklenenden kötü
d['dt']=pd.to_datetime(d.tarih)
rows=[]
for at_,x in d.groupby('at'):
    x=x.sort_values('dt')
    for i in range(1,len(x)):
        pr=x.iloc[i-1]; cu=x.iloc[i]
        if (cu.dt-pr.dt).days<=60: rows.append((cu.tarih,cu.kazandi,cu.p,int(cu.bit<=3),pr.et_a,pr.et_b,pr.et_c,pr.et_d))
R=pd.DataFrame(rows,columns=['tarih','kaz','p','ilk3','et_a','et_b','et_c','et_d'])
log(f'\nT117: ardışık çift sayısı {len(R)}')
for e,ad in (('et_a','tempo kurbanı'),('et_b','geç kapanan'),('et_c','beklenenden iyi'),('et_d','beklenenden kötü')):
    S=R[R[e]==1]
    if len(S)<30: log(ad,'n',len(S),'yetersiz'); continue
    a=np.array([(x.kaz.sum(),x.p.sum()) for _,x in S.groupby('tarih')]); pt=a[:,0].sum()/a[:,1].sum()
    bs=[(lambda ix:a[ix,0].sum()/a[ix,1].sum())(rng.integers(0,len(a),len(a))) for _ in range(1500)]; ga=np.percentile(bs,[1.25,98.75]).round(2)
    log(f'{ad} | n={len(S)} | kazanan {int(S.kaz.sum())} beklenen {S.p.sum():.1f} | O/E {pt:.3f} GA(Bonf 4) {ga.tolist()} | sonraki ilk3 oranı {S.ilk3.mean():.3f} | {"ADAY" if (len(S)>=200 and (ga[0]>1 or ga[1]<1)) else "bilgi taşımıyor/yetersiz"}')
log('\nBİTTİ')
