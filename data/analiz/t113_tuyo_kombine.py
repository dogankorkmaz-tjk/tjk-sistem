import pandas as pd, json, glob, math, os, itertools, numpy as np
from tjk.sabit_golge import _dk
TIP={'G':1001,'P2':1002,'P3':1100,'P4':1101,'FH':1103}; N={'G':1,'P2':2,'P3':3,'P4':4}
L={t:{} for t in TIP}   # tur -> gün -> [(yarış, oran, w)]
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
            tuyo=[n for n in pj if pj[n]>=0.06 and pj[n]/pp[n]>=1.30]
            Rt=_dk(k['saat']); fav=min(s,key=lambda a:s[a]['g'])
            for tur,tip in TIP.items():
                x=P[(P.tip==tip)&(P.hipodrom==h['id'])&(P.kosu==k['kosu'])&(P.dk<=Rt+3)]
                if x.empty: continue
                g7=x.sort_values('dk').groupby('no').last().oran
                for no in tuyo:
                    if no not in g7.index or (tur=='FH' and str(no)==str(fav)): continue
                    sr=(s.get(str(no)) or {}).get('sira')
                    if sr is None: continue
                    w=int(sr==(2 if s[fav]['sira']==1 else 1)) if tur=='FH' else int(sr<=N[tur])
                    L[tur].setdefault(t,[]).append(((h['id'],k['kosu']),float(g7[no]),w))
rng=np.random.default_rng(1)
print('tür k | bahis | isabet | ROI [GA] | gün')
for tur in TIP:
    for kk in (1,2,3):
        gs=[];n=0;hit=0
        for t,b in L[tur].items():
            r=[]
            for c in itertools.combinations(b,kk):
                if len({x[0] for x in c})<kk: continue
                o=np.prod([x[1] for x in c]); w=all(x[2] for x in c); r.append(o*w); hit+=w
            if r: gs.append(np.array(r)); n+=len(r)
        if not gs: continue
        a=np.concatenate(gs); bs=[np.concatenate([gs[i] for i in rng.integers(0,len(gs),len(gs))]).mean() for _ in range(3000)]
        print(tur,kk,n,round(hit/n,3),round(a.mean(),3),[float(v) for v in np.percentile(bs,[2.5,97.5]).round(2)],len(gs))
