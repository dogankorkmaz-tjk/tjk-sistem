# T111 geriye dönük (bilgi amaçlı): erken (ilk yayın) sabit oran vs yarışa 7 dk kala oran, Jason adayları
import pandas as pd, json, glob, math, os, numpy as np
from tjk.sabit_golge import _dk
rows=[]
for f in sorted(glob.glob('data/piyasa/2026-*.csv.gz')):
    t=os.path.basename(f)[:10]; gy=f'docs/data/gun/{t}.json'
    if not os.path.exists(gy): continue
    g=json.load(open(gy)); w0,l2=g['w0_aday'],g.get('lp2_aday',0.0)
    d=pd.read_csv(f); d=d[(d.tip==1001)&(d.oran>1.0)]; d['dk']=d.saat.map(_dk)
    for h in g['hipodromlar']:
        for k in h['kosular']:
            s=k.get('sonuc') or {}; kaz=s.get('kazanan') if isinstance(s,dict) else None
            if not k.get('saat') or not s: continue
            at=[a for a in k['atlar'] if a.get('agf') and not a.get('kosmaz') and a.get('z2') is not None]
            if len(at)<4: continue
            x=d[(d.hipodrom==h['id'])&(d.kosu==k['kosu'])]
            if x.empty: continue
            R=_dk(k['saat'])
            tot=sum(a['agf'] for a in at); pp={a['no']:a['agf']/tot for a in at}
            sc={a['no']:w0*math.log(max(pp[a['no']],1e-6))+l2*math.log(max(pp[a['no']],1e-6))**2+a['z2'] for a in at}
            m=max(sc.values()); e={n:math.exp(v-m) for n,v in sc.items()}; Z=sum(e.values())
            ear=x[x.dk<=R-7]; 
            if ear.empty: continue
            ilk=ear.sort_values('dk').groupby('no').first().oran; son=ear.sort_values('dk').groupby('no').last().oran
            gec=x[x.dk<=R+3]; g7=gec.sort_values('dk').groupby('no').last().oran
            for a in at:
                n=a['no']
                if n in ilk.index and n in g7.index:
                    rows.append(dict(t=t,hip=h['id'],kosu=k['kosu'],no=n,pj=e[n]/Z,ilk=ilk[n],g7=g7[n],ilk_dk=R-x[x.no==n].dk.min(),win=int((s.get(str(n)) or {}).get('sira')==1)))
D=pd.DataFrame(rows); print('at-satırı',len(D),'gün',D.t.nunique(),'yarış',D.groupby(['t','hip','kosu']).ngroups)
print('ilk/g7 oran medyan oranı',(D.ilk/D.g7).median().round(3),'ort log',np.log(D.ilk/D.g7).mean().round(4))
for ad,c in (('GE (ilk oran)','ilk'),('G (7dk)','g7')):
    S=D[D.pj*D[c]>=1.2]; ret=(S.win*S[c]).sum(); print(ad,'bahis',len(S),'kazanan',S.win.sum(),'ROI',round(ret/max(len(S),1),3))
# aynı atlar üzerinde (GE seçilenler), her iki oranla
S=D[D.pj*D.ilk>=1.2]; print('GE seçilenler: ilk oranla ROI',round((S.win*S.ilk).mean(),3),'7dk oranla ROI',round((S.win*S.g7).mean(),3),'n',len(S))

# gün-küme bootstrap (GE)
S=D[D.pj*D.ilk>=1.2].copy(); S['r']=S.win*S.ilk; gs=[x.r.values for _,x in S.groupby('t')]
rng=np.random.default_rng(1); b=[]
for _ in range(4000):
    ix=rng.integers(0,len(gs),len(gs)); a=np.concatenate([gs[i] for i in ix]); b.append(a.mean())
print('GE ROI GA',np.percentile(b,[2.5,97.5]).round(2))
print('tüm atlar (Jason seçimi yok) ilk oranla ROI',round((D.win*D.ilk).mean(),3),'7dk oranla',round((D.win*D.g7).mean(),3))
print('pj>=%6 ve pj/pp>=1.3 (tüyo benzeri) n:')
