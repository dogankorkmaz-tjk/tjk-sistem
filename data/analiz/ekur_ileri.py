"""T34 ileri gölge: ekür çifti içi bölüşüm θ=3,7 (dondurulmuş) vs θ=1 (G1-S). Gün dosyaları docs/data/gun/*.json ('ek' = ekür grubu). python3 data/analiz/ekur_ileri.py [başlangıç=2026-10-29]"""
import glob,json,sys,numpy as np
BAS=sys.argv[1] if len(sys.argv)>1 else "2026-10-29";TH=3.7;GAM=[1,0.80,0.67,0.59,0.52]
rows=[]
for f in sorted(glob.glob('docs/data/gun/*.json')):
    o=json.load(open(f));t=o['tarih']
    if t<BAS or 'w0_g1' not in o: continue
    for h in o['hipodromlar']:
        for k in h['kosular']:
            at=[a for a in k['atlar'] if not a.get('kosmaz') and a.get('z6') is not None and a.get('agf')];sn=k.get('sonuc')
            if not sn or len(at)<6: continue
            sr=[(sn.get(str(a['no'])) or {}).get('sira') for a in at]
            if any(x is None for x in sr): continue
            order=list(np.argsort(sr))
            if [sr[i] for i in order[:5]]!=[1,2,3,4,5]: continue
            tot=sum(a['agf'] for a in at);s=o['w0_g1']*np.log(np.array([a['agf']/tot for a in at]))+np.array([a['z6'] for a in at]);p=np.exp(s-s.max());p/=p.sum()
            grp={}
            for i,a in enumerate(at):
                if a.get('ek'): grp.setdefault(a['ek'],[]).append(i)
            pr=[v for v in grp.values() if len(v)==2]
            if not pr: continue
            def ll(pp):
                m=np.ones(len(pp),bool);out=np.zeros(5)
                for kk in range(5):
                    z=np.where(m,GAM[kk]*np.log(np.clip(pp,1e-12,None)),-1e9);z-=z.max();out[kk]=z[order[kk]]-np.log(np.exp(z[m]).sum());m[order[kk]]=False
                return out
            q=p.copy()
            for i,j in pr:
                if q[i]<q[j]: i,j=j,i
                P=q[i]+q[j];sh=q[i]/P;l=np.log(sh/(1-sh));a_=P/(1+np.exp(-TH*l));q[i]=a_;q[j]=P-a_
            rows.append((t,ll(q)-ll(p)))
print("ekür koşu",len(rows))
if rows:
    D=np.array([r[1] for r in rows]);gun=np.array([r[0] for r in rows]);ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};rng=np.random.default_rng(1)
    for nm,ix in [("kazanan",[0]),("ikili",[0,1]),("üçlü",[0,1,2]),("ilk4",[0,1,2,3]),("ilk5",[0,1,2,3,4])]:
        x=D[:,ix].sum(1);bs=[x[np.concatenate([gi[ug[i]] for i in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(1000)]
        print(f"{nm:8s} {x.mean():+.4f} nats/koşu (θ=3,7 − θ=1; pozitif = bölüşüm düzeltmesi iyi) GA [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
