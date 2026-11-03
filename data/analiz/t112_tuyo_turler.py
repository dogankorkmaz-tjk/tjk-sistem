import pandas as pd, json, glob, math, os, numpy as np
from tjk.sabit_golge import _dk
TIP={'G':1001,'P2':1002,'P3':1100,'P4':1101,'FH':1103}; N={'G':1,'P2':2,'P3':3,'P4':4}
R={t:[] for t in TIP}
for f in sorted(glob.glob('data/piyasa/2026-*.csv.gz')):
    t=os.path.basename(f)[:10]; gy=f'docs/data/gun/{t}.json'
    if not os.path.exists(gy): continue
    g=json.load(open(gy)); w0,l2=g['w0_aday'],g.get('lp2_aday',0.0); P=pd.read_csv(f); P['dk']=P.saat.map(_dk); P=P[P.oran>1.0]
    for h in g['hipodromlar']:
        for k in h['kosular']:
            s=k.get('sonuc') or {}
            if not s or not k.get('saat'): continue
            at=[a for a in k['atlar'] if a.get('agf') and not a.get('kosmaz') and a.get('z2') is not None]
            if len(at)<4: continue
            tot=sum(a['agf'] for a in at); pp={a['no']:a['agf']/tot for a in at}
            sc={a['no']:w0*math.log(max(pp[a['no']],1e-6))+l2*math.log(max(pp[a['no']],1e-6))**2+a['z2'] for a in at}
            m=max(sc.values()); e={n:math.exp(v-m) for n,v in sc.items()}; Z=sum(e.values()); pj={n:v/Z for n,v in e.items()}
            tuyo={n for n in pj if pj[n]>=0.06 and pj[n]/pp[n]>=1.30}
            Rt=_dk(k['saat']); fav=min(s,key=lambda a:s[a]['g'])
            for tur,tip in TIP.items():
                x=P[(P.tip==tip)&(P.hipodrom==h['id'])&(P.kosu==k['kosu'])]
                if x.empty: continue
                e_=x[x.dk<=Rt-7]; l_=x[x.dk<=Rt+3]
                if e_.empty: continue
                ilk=e_.sort_values('dk').groupby('no').first().oran; g7=l_.sort_values('dk').groupby('no').last().oran
                for no in ilk.index.intersection(g7.index):
                    sr=(s.get(str(no)) or {}).get('sira')
                    if sr is None or (tur=='FH' and str(no)==str(fav)): continue
                    w=int(sr==(2 if s[fav]['sira']==1 else 1)) if tur=='FH' else int(sr<=N[tur])
                    R[tur].append((t,no in tuyo,ilk[no],g7[no],w))
rng=np.random.default_rng(1)
def ci(S,c):
    gs=[(x.w*x[c]).values for _,x in S.groupby('t')]
    if not gs: return (0,0)
    b=[np.concatenate([gs[i] for i in rng.integers(0,len(gs),len(gs))]).mean() for _ in range(3000)]
    return tuple(np.percentile(b,[2.5,97.5]).round(2))
print('tür | tüyo n | isabet | ort oran7 | ROI7 [GA] | ROIilk [GA] | tüm atlar ROI7')
for tur,r in R.items():
    D=pd.DataFrame(r,columns=['t','tuyo','ilk','g7','w']); S=D[D.tuyo]
    print(tur,len(S),round(S.w.mean(),3),round(S.g7.mean(),2),round((S.w*S.g7).mean(),3),ci(S,'g7'),round((S.w*S.ilk).mean(),3),ci(S,'ilk'),round((D.w*D.g7).mean(),3),'gün',S.t.nunique())
