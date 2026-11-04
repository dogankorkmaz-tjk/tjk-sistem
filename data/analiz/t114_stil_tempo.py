import sys,glob,json,os,numpy as np,pandas as pd
sys.path.insert(0,'data/analiz'); sys.path.insert(0,'.')
import video_ozellik as VO
d=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('data/temiz/202[56]-*.csv.gz')) if os.path.basename(f)[:7]>='2025-10'],ignore_index=True)
d=d[(d.kosmadi!=True)&d.p_piyasa.notna()&d.kazandi.notna()].copy()
d=VO.ekle(d)
# mesafe: video bolum en büyük anahtar
M={}
for f in glob.glob('data/video_seyir/20*.json'):
    b=os.path.basename(f)[:-5].split('_')
    if len(b)!=3: continue
    try: j=json.load(open(f))
    except Exception: continue
    ks=[int(k) for k in (j.get('bolum') or {}) if k.isdigit() and int(k)<=3000]
    if ks: M[(b[0],b[1],int(b[2]))]=max(ks)
d['mes']=[M.get((t,h,k),np.nan) for t,h,k in zip(d.tarih,d.hipodrom,d.kosu)]
d['p']=d.p_piyasa/d.groupby(['tarih','hipodrom','kosu']).p_piyasa.transform('sum')
d=d[d.f_v1!=0].copy()   # geçmişi olmayan hariç
d['stil']=np.where(d.f_v1<-0.12,'öncü',np.where(d.f_v1>0.12,'kapanış','orta'))
d['band']=pd.cut(d.mes,[0,1399,1999,9999],labels=['kısa','orta','uzun'])
nf=d.groupby(['tarih','hipodrom','kosu']).stil.transform(lambda s:(s=='öncü').sum()); d['nF']=np.where(nf<=1,'0-1',np.where(nf==2,'2','3+'))
rng=np.random.default_rng(114)
def oe(S):
    if len(S)==0: return None
    gs=[(x.kazandi.sum(),x.p.sum()) for _,x in S.groupby('tarih')]
    a=np.array(gs); pt=a[:,0].sum()/a[:,1].sum()
    b=[(lambda ix:a[ix,0].sum()/a[ix,1].sum())(rng.integers(0,len(a),len(a))) for _ in range(2000)]
    return len(S),int(S.kazandi.sum()),round(S.p.sum(),1),round(pt,3),np.percentile(b,[2.5,97.5]).round(2).tolist()
print('toplam at',len(d),'koşu',d.groupby(['tarih','hipodrom','kosu']).ngroups,'gün',d.tarih.nunique())
print('stil dağılımı',d.stil.value_counts().to_dict())
print('\nSTİL × MESAFE: n | kazanan | beklenen | O/E | GA')
for s in ('öncü','orta','kapanış'):
    for bnd in ('kısa','orta','uzun'): print(s,bnd,oe(d[(d.stil==s)&(d.band==bnd)]))
print('\nSTİL × KOŞUDAKİ ÖNCÜ SAYISI')
for s in ('öncü','orta','kapanış'):
    for n in ('0-1','2','3+'): print(s,n,oe(d[(d.stil==s)&(d.nF==n)]))
print('\nSTİL (genel)')
for s in ('öncü','orta','kapanış'): print(s,oe(d[d.stil==s]))
print('\nROI (1 TL ganyan, büyük ödemeler dahil) | n | ROI | GA')
def roi(S):
    gs=[((x.kazandi*x.ganyan).sum(),len(x)) for _,x in S.groupby('tarih')]; a=np.array(gs)
    b=[(lambda ix:a[ix,0].sum()/a[ix,1].sum())(rng.integers(0,len(a),len(a))) for _ in range(2000)]
    return len(S),round(a[:,0].sum()/a[:,1].sum(),3),np.percentile(b,[2.5,97.5]).round(2).tolist()
for s in ('öncü','orta','kapanış'): print(s,roi(d[d.stil==s]))
print('öncü kısa',roi(d[(d.stil=='öncü')&(d.band=='kısa')]),'öncü orta',roi(d[(d.stil=='öncü')&(d.band=='orta')]))
print('tüm atlar',roi(d))
