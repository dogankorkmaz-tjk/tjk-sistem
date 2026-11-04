"""ANA MODEL G1-S v3 + galop (MJ) taban ile MJV (= MJ + video stil f_v1..f_v5) farkı: pratik etki (kazanan log-kayıp, tepe at isabeti, tepe at ROI). Kaynak: v3 galoplu S3g önbellekleri."""
import pickle,glob,numpy as np,pandas as pd,random
random.seed(7)
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','kazandi','ganyan','p_piyasa','kosmadi']) for f in sorted(glob.glob('data/temiz/2025-1*.csv.gz')+glob.glob('data/temiz/2026-*.csv.gz'))])
T=T[T.kosmadi!=True]; W={}
for r in T.itertuples():
    W.setdefault((r.tarih,r.hipodrom,int(r.kosu)),{})[int(r.no)]=(r.kazandi,r.ganyan,r.p_piyasa)
def yukle(v,a): return pickle.load(open(f'/tmp/claude-0/cacheg_{v}_{a}.pkl','rb'))
def sm(S): S=S-S.max(1,keepdims=True); e=np.exp(S); return e/e.sum(1,keepdims=True)
rows=[]
for a in [f'2025-{m}' for m in ('12',)]+[f'2026-{m:02d}' for m in range(1,11)]:
    X=yukle('MJV',a); Y=yukle('MJ',a); assert X['keys']==Y['keys']
    if np.isnan(X['S3g']).any() or np.isnan(Y['S3g']).any(): print('atlandı (galop aşaması yok/NaN):',a); continue
    for k,key in enumerate(X['keys']):
        w=W.get(tuple(key)); 
        if not w: continue
        nos=X['nos'][k]; pj=sm(X['S3g'][k:k+1])[0]; pb=sm(Y['S3g'][k:k+1])[0]
        def at(p):
            i=int(np.argmax(p[:len(nos)])); n=nos[i]; kz,g,pm=w.get(n,(np.nan,np.nan,np.nan)); return n,kz,g
        kz_no=[n for n in nos if w.get(n,(0,))[0]==1]
        if len(kz_no)!=1: continue
        iw=nos.index(kz_no[0]); nj,kj,gj=at(pj); nb,kb,gb=at(pb)
        rows.append(dict(ay=a,gun=key[0],ll_v=-np.log(max(pj[iw],1e-9)),ll_b=-np.log(max(pb[iw],1e-9)),hit_v=float(kj==1),hit_b=float(kb==1),roi_v=(gj if kj==1 else 0.0),roi_b=(gb if kb==1 else 0.0),ayni=float(nj==nb)))
D=pd.DataFrame(rows); print('koşu',len(D),'| aynı tepe at oranı %.3f'%D.ayni.mean())
def boot(D,col_a,col_b):
    g=D.groupby('gun'); ug=list(g.groups); s={k:(v[col_a].sum()-v[col_b].sum(),len(v)) for k,v in g}
    r=[]
    for _ in range(1000):
        pk=[random.choice(ug) for _ in ug]; r.append(sum(s[k][0] for k in pk)/sum(s[k][1] for k in pk))
    return np.percentile(r,[2.5,97.5])
for ad,sub in (('H 2025-12..2026-03',D[D.ay<='2026-03']),('B 2026-04..2026-10',D[D.ay>='2026-04']),('TÜMÜ',D)):
    print(ad,'koşu',len(sub))
    for ad2,a,b,sg in (('kazanan log-kayıp (− iyi)','ll_v','ll_b',1),('tepe at isabeti (+ iyi)','hit_v','hit_b',1),('tepe ata 1 TL ganyan geri dönüş/koşu (+ iyi)','roi_v','roi_b',1)):
        m=(sub[a].sum()-sub[b].sum())/len(sub); lo,hi=boot(sub,a,b); print(f'   {ad2}: MJV {sub[a].mean():.4f} | MJ {sub[b].mean():.4f} | fark {m:+.4f} [{lo:+.4f},{hi:+.4f}]')
