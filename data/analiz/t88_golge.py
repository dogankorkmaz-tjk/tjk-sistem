"""T88 ileri kol ölçümü: G1-S-Aç (geç) vs sabit G1-S-G (geç) 96 TL, aynı koşularda. python3 data/analiz/t88_golge.py"""
import json,glob,numpy as np
rng=np.random.default_rng(88)
R=[]
for f in sorted(glob.glob('data/besli/*.json')):
    g=f.split('/')[-1][:-5]
    for c in json.load(open(f)).values():
        if not c.get('sonuc'): continue
        K=(c.get('gec') or {}).get('kuponlar',[])
        a=next((q for q in K if q['model']=='G1-S-Aç (geç)' and 'isabet' in q),None)
        s=next((q for q in K if q['model']=='G1-S-G (geç)' and q['butce']==96 and 'isabet' in q),None)
        if a and s: R.append((g,a['bedel_gecerli'],a['kazanc'],int(a['isabet']),s['bedel_gecerli'],s['kazanc'],int(s['isabet']),a['butce']))
if not R: print('henüz sonuçlanmış koşu yok'); raise SystemExit
import pandas as pd
D=pd.DataFrame(R,columns=['gun','ha','ka','ia','hs','ks','is','B'])
def roi(x,h,k): return x[k].sum()/x[h].sum()
gl=D.gun.unique();bs=[]
for _ in range(3000):
    x=pd.concat([D[D.gun==k] for k in rng.choice(gl,len(gl))]);bs.append(roi(x,'ha','ka')-roi(x,'hs','ks'))
o=[f"koşu {len(D)}, gün {len(gl)}; bütçe dağılımı {D.B.value_counts().to_dict()}",
 f"Aç: harcama {D.ha.sum():.0f} kazanç {D.ka.sum():.0f} geri dönüş {roi(D,'ha','ka'):.3f} tutma {D['ia'].sum()}",
 f"Sabit96: harcama {D.hs.sum():.0f} kazanç {D.ks.sum():.0f} geri dönüş {roi(D,'hs','ks'):.3f} tutma {D['is'].sum()}",
 f"fark (Aç−Sabit96) {roi(D,'ha','ka')-roi(D,'hs','ks'):+.3f} GA95 {np.percentile(bs,[2.5,97.5]).round(3)}; koşu başına net Aç {(D.ka-D.ha).mean():+.1f} Sabit96 {(D.ks-D.hs).mean():+.1f}"]
print('\n'.join(o))
