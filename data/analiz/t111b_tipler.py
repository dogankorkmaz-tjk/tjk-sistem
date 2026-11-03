import pandas as pd, json, glob, os, numpy as np
from tjk.sabit_golge import _dk
K={1001:1,1002:2,1100:3,1101:4}
for tip,n in list(K.items())+[(1103,'FH')]:
    r=[]
    for f in sorted(glob.glob('data/piyasa/2026-*.csv.gz')):
        t=os.path.basename(f)[:10]; gy=f'docs/data/gun/{t}.json'
        if not os.path.exists(gy): continue
        g=json.load(open(gy)); d=pd.read_csv(f); d=d[(d.tip==tip)&(d.oran>1.0)]; d['dk']=d.saat.map(_dk)
        for h in g['hipodromlar']:
            for k in h['kosular']:
                s=k.get('sonuc') or {}
                if not s or not k.get('saat'): continue
                x=d[(d.hipodrom==h['id'])&(d.kosu==k['kosu'])]
                if x.empty: continue
                R=_dk(k['saat']); e=x[x.dk<=R-7]; l=x[x.dk<=R+3]
                if e.empty: continue
                ilk=e.sort_values('dk').groupby('no').first().oran; g7=l.sort_values('dk').groupby('no').last().oran
                fav=min(s,key=lambda a:s[a]['g']) if s else None
                for no in ilk.index.intersection(g7.index):
                    sr=(s.get(str(no)) or {}).get('sira')
                    if sr is None: continue
                    if tip==1103:
                        if str(no)==str(fav): continue
                        w=int(sr==1 or (sr==2 and str(fav) in [a for a in s if s[a]['sira']==1]))
                        w=int(sr==(2 if s[fav]['sira']==1 else 1))
                    else: w=int(sr<=n)
                    r.append((t,ilk[no],g7[no],w))
    D=pd.DataFrame(r,columns=['t','ilk','g7','w'])
    print(tip,n,'satır',len(D),'gün',D.t.nunique(),'ilk/g7 medyan',round((D.ilk/D.g7).median(),3),'ROI ilk',round((D.w*D.ilk).mean(),3),'g7',round((D.w*D.g7).mean(),3))
