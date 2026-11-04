"""T119: mesafe × pist × tempo hücrelerinde öncü/kapanışçı avantajı (hipotez_defteri.md ön kaydı)."""
import sys,glob,json,gzip,os,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
rng=np.random.default_rng(119)
def log(*a): print(*a,flush=True)
fs=[f for f in sorted(glob.glob('data/temiz/20*.csv.gz')) if os.path.basename(f)[:7]>='2024-10']
d=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
d=d[(d.kosmadi!=True)&d.p_piyasa.notna()&d.kazandi.notna()&d.ganyan.notna()].copy()
MS={};PS={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=os.path.basename(f)[:10]
    if t<'2024-10-01': continue
    try: j=json.load(gzip.open(f))
    except Exception: continue
    for hip,ks in (j.get('program') or {}).items():
        for k in ks:
            try: MS[(t,hip,int(k['number']))]=float(k.get('distance') or np.nan); PS[(t,hip,int(k['number']))]=k.get('raceCourseType')
            except Exception: pass
d['mes']=[MS.get((t,h,k),np.nan) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d['pist']=[PS.get((t,h,k)) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d=VO.ekle(d)
E={};BL={}
for f in glob.glob('data/video_seyir/20*.json'):
    b=os.path.basename(f)[:-5].split('_')
    if len(b)!=3: continue
    try: j=json.load(open(f))
    except Exception: continue
    if j.get('okuyucu')!='rakam1' or not j.get('ozet'): continue
    for no,o in j['ozet'].items(): E[(b[0],b[1],int(b[2]),int(no))]=o['erken']
    bl={int(k):v for k,v in (j.get('bolum') or {}).items() if k.isdigit()}
    BL[(b[0],b[1],int(b[2]))]=(bl[400]/(bl[800]-bl[400]) if 400 in bl and 800 in bl and bl[800]>bl[400] else np.nan)
d['e_erken']=[E.get((t,h,k,n),np.nan) for t,h,k,n in zip(d.tarih,d.hipodrom,d.kosu,d.no)]
d=d[d.e_erken.notna()].copy()
d['rid']=d.tarih+'|'+d.hipodrom+'|'+d.kosu.astype(str)
d['n']=d.groupby('rid').no.transform('count'); d=d[d.n>=5].copy()
d['p']=d.p_piyasa/d.groupby('rid').p_piyasa.transform('sum')
d['fade']=[BL.get((t,h,k),np.nan) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d=d[(d.f_v1!=0)&d.mes.notna()&d.pist.notna()].copy()
d['stil']=np.where(d.f_v1<-0.12,'öncü',np.where(d.f_v1>0.12,'kapanış','orta'))
d['band']=pd.cut(d.mes,[0,1399,1799,2199,9999],labels=['<1400','1400-1799','1800-2199','≥2200']).astype(str)
nf=d.groupby('rid').stil.transform(lambda s:(s=='öncü').sum()); d['nF']=np.where(nf<=1,'0-1',np.where(nf==2,'2','3+'))
d['erk_kaz']=((d.kazandi==1)&(d.e_erken<=2.5)).astype(int); d['erk2']=(d.e_erken<=2.5).astype(int)
mid=sorted(d.tarih.unique())[len(d.tarih.unique())//2]; d['yari']=np.where(d.tarih<mid,1,2)
log('at',len(d),'koşu',d.rid.nunique(),'gün',d.tarih.nunique(),'bölme',mid,'| pist',d.pist.value_counts().to_dict(),'| stil',d.stil.value_counts().to_dict())
def gun(S,cols):
    return S.groupby('tarih')[cols].sum().values
def stat(S,B=1500):
    """O/E ve ROI, gün-küme bootstrap"""
    if len(S)==0: return None
    S=S.assign(g=S.kazandi*S.ganyan)
    a=gun(S,['kazandi','p','g']); n=S.groupby('tarih').size().values
    oe=a[:,0].sum()/a[:,1].sum(); roi=a[:,2].sum()/n.sum()
    bo=[];br=[]
    for _ in range(B):
        ix=rng.integers(0,len(a),len(a)); bo.append(a[ix,0].sum()/a[ix,1].sum()); br.append(a[ix,2].sum()/n[ix].sum())
    return dict(n=len(S),w=int(a[:,0].sum()),oe=oe,roi=roi,oe_b=np.array(bo),roi_b=np.array(br),a=a,days=S.tarih.unique())
def endeks(Sc,Sk,k,B=1500):
    """O/E(öncü)-O/E(kapanış), ortak gün bootstrap"""
    days=sorted(set(Sc.tarih)|set(Sk.tarih)); ix_d={t:i for i,t in enumerate(days)}
    def mat(S):
        m=np.zeros((len(days),2))
        for t,x in S.groupby('tarih'): m[ix_d[t]]=[x.kazandi.sum(),x.p.sum()]
        return m
    A=mat(Sc);K=mat(Sk); pt=A[:,0].sum()/max(A[:,1].sum(),1e-9)-K[:,0].sum()/max(K[:,1].sum(),1e-9)
    bs=[]
    for _ in range(B):
        ix=rng.integers(0,len(days),len(days)); bs.append(A[ix,0].sum()/max(A[ix,1].sum(),1e-9)-K[ix,0].sum()/max(K[ix,1].sum(),1e-9))
    lo,hi=np.percentile(bs,[2.5/k,100-2.5/k]); return pt,lo,hi
def ozet(S): 
    r=stat(S); 
    return None if r is None else r
def satir(ad,S,k):
    On=S[S.stil=='öncü'];Ka=S[S.stil=='kapanış'];Or=S[S.stil=='orta']
    if len(On)<30 or len(Ka)<30: log(f'{ad} | yetersiz (öncü {len(On)}, kapanış {len(Ka)})'); return
    ro=stat(On);rk=stat(Ka);rr=stat(Or)
    pt,lo,hi=endeks(On,Ka,k)
    y=[endeks(On[On.yari==h],Ka[Ka.yari==h],1,B=300)[0] if ((On.yari==h).sum()>=30 and (Ka.yari==h).sum()>=30) else np.nan for h in (1,2)]
    aday=len(On)>=150 and len(Ka)>=150 and len(S)>=300 and np.isfinite(y[0]) and np.isfinite(y[1]) and ((lo>0 and y[0]>0 and y[1]>0) or (hi<0 and y[0]<0 and y[1]<0))
    rg=lambda r:f"{r['roi']:.2f}[{np.percentile(r['roi_b'],2.5):.2f};{np.percentile(r['roi_b'],97.5):.2f}]"
    log(f"{ad} | n öncü {ro['n']} orta {rr['n'] if rr else 0} kap {rk['n']} | O/E öncü {ro['oe']:.3f} orta {rr['oe']:.3f} kap {rk['oe']:.3f} | endeks {pt:+.3f} GA(Bonf) [{lo:+.3f};{hi:+.3f}] yarı1 {y[0]:+.3f} yarı2 {y[1]:+.3f} | ROI öncü {rg(ro)} kap {rg(rk)} | {'ADAY' if aday else '-'}")
cells=[]
for b in ['<1400','1400-1799','1800-2199','≥2200']:
    for p in ['Kum','Çim','Sentetik']: cells.append(('mesafe×pist',f'{b} {p}',(d.band==b)&(d.pist==p)))
for b in ['<1400','1400-1799','1800-2199','≥2200']: cells.append(('mesafe',b,d.band==b))
for p in ['Kum','Çim','Sentetik']: cells.append(('pist',p,d.pist==p))
for t in ['0-1','2','3+']: cells.append(('tempo(öncü sayısı)',t,d.nF==t))
for t in ['0-1','2','3+']:
    for b in ['<1400','1400-1799','1800-2199','≥2200']: cells.append(('tempo×mesafe',f'{t} {b}',(d.nF==t)&(d.band==b)))
k=len(cells); log(f'\nHücre sayısı k={k}, Bonferroni %{100-5/k:.2f} GA. endeks = O/E(öncü) − O/E(kapanış)')
log('hücre | n | O/E | endeks | ROI | aday')
satir('GENEL',d,k)
for grp,ad,m in cells: satir(f'{grp}: {ad}',d[m],k)
# kazananın erken sırası payı
log('\nKAZANAN ERKEN SIRA ≤2,5 (yarışı önden başlayan at kazandı) payı vs beklenen (rastgele 2/n kadar; piyasa beklentisi = Σp erken≤2,5 olanların)')
for grp,ad,m in cells[:12]+cells[12:19]+cells[19:]:
    S=d[m]
    if len(S)<300: continue
    w=S.groupby('rid').erk_kaz.sum().mean(); exp=S[S.erk2==1].groupby('rid').p.sum().reindex(S.rid.unique()).fillna(0).mean()
    log(f'{grp}: {ad} | koşu {S.rid.nunique()} | önden başlayan kazandı {w:.3f} | piyasa beklentisi {exp:.3f} | fark {w-exp:+.3f}')
# gerçek tempo (video sönmesi) betimleyici
Z=d[d.fade.notna()].copy(); q=Z.fade.quantile([.33,.67]).values
Z['tp']=np.where(Z.fade<q[0],'hızlı-erken(az sönme)',np.where(Z.fade<q[1],'orta','yavaş-erken'))
log('\nGERÇEK TEMPO (yarış SONRASI, betimleyici; fade=son400/ önceki400 oranı terzileri):')
for t in Z.tp.unique():
    S=Z[Z.tp==t]; On=S[S.stil=='öncü'];Ka=S[S.stil=='kapanış']
    if len(On)>30 and len(Ka)>30:
        ro,rk=stat(On,500),stat(Ka,500); log(f'{t} | öncü n {ro["n"]} O/E {ro["oe"]:.3f} | kapanış n {rk["n"]} O/E {rk["oe"]:.3f} | fark {ro["oe"]-rk["oe"]:+.3f}')
log('\nBİTTİ')
