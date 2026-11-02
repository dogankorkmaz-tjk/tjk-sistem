import pandas as pd,numpy as np,glob,json,math
def dk(s):
    p=[int(x) for x in str(s).split(':')];return p[0]*60+p[1]+(p[2]/60 if len(p)>2 else 0)
HK={'DBAKIR':'diyarbakir'}
rows=[]
for fm in sorted(glob.glob('data/muh/2026-*.json')):
    gun=fm[-15:-5]
    try:G=json.load(open(f'docs/data/gun/{gun}.json'));M=json.load(open(fm));P=pd.read_csv(f'data/piyasa/{gun}.csv.gz')
    except Exception: continue
    P=P[(P.tip==1001)&(P.oran>1.0)];w0,l2=G['w0_aday'],G.get('lp2_aday',0.0)
    for h in G['hipodromlar']:
        for k in h['kosular']:
            S=k.get('sonuc') or {}
            if not S or not k.get('saat'): continue
            m=M.get(f"{HK.get(h['id'].upper(),h['id'].upper())}-{k['kosu']}")
            if not m: continue
            st=dk(k['saat']);an=[a for a in m['anlik'] if a.get('g') and a['t'] and dk(a['t'])<=st-5]
            if not an: continue
            g5=an[-1]['g'];at=[a for a in k['atlar'] if not a.get('kosmaz') and a.get('z2') is not None]
            gg={a['no']:float(g5[str(a['no'])]) for a in at if str(a['no']) in g5 and float(g5[str(a['no'])])>1}
            if len(gg)<len(at)*0.8 or len(gg)<4: continue
            pm=pd.Series({n:1/v for n,v in gg.items()});pm/=pm.sum()
            s={n:w0*math.log(max(pm[n],1e-6))+l2*math.log(max(pm[n],1e-6))**2+a['z2'] for a in at for n in [a['no']] if n in pm.index}
            mx=max(s.values());e={n:math.exp(v-mx) for n,v in s.items()};Z=sum(e.values())
            x=P[(P.hipodrom==h['id'])&(P.kosu==k['kosu'])];x=x.assign(t=x.saat.map(dk));x=x[x.t<=st-5]
            o5=x.sort_values('t').groupby('no').oran.last()
            for n,v in e.items():
                sv=S.get(str(n))
                if not sv: continue
                rows.append(dict(gun=gun,h=h['id'],k=k['kosu'],no=n,pjm=v/Z,pj_final=sv['pm2'],pm5=pm[n],g=sv['g'],sira=sv['sira'],o5=o5.get(n,np.nan)))
D=pd.DataFrame(rows);print(len(D),'at',D.groupby(['gun','h','k']).ngroups,'koşu')
print('corr(log p_Jason[muhtemel T-5], log pm2[kapanış]) = %.3f ; ort |fark| %.3f'%(np.corrcoef(np.log(D.pjm),np.log(D.pj_final))[0,1],(D.pjm-D.pj_final).abs().mean()))
print('corr(log muhtemel T-5 payı, log kapanış 1/g) = %.3f'%np.corrcoef(np.log(D.pm5),-np.log(D.g))[0,1])
x=D.dropna(subset=['o5']);
for nm,pc in(('Jason(muhtemel T-5)','pjm'),('Jason(kapanış pm2)','pj_final')):
    y=x[x[pc]*x.o5>=1.2];print(f'{nm}×sabit oran T-5 ≥1.2: n={len(y)} kazanan={int((y.sira==1).sum())} ROI={((y.sira==1)*y.o5).mean():.3f}')
y=x[(x.pjm*x.o5>=1.2)&(x.pjm>=x.pm5)];print(f'Kol B (muhtemel, p≥muhtemel payı): n={len(y)} kazanan={int((y.sira==1).sum())} ROI={((y.sira==1)*y.o5).mean():.3f}')
