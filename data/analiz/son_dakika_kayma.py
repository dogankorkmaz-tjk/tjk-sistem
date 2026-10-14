"""Faz 3 (15 Ekim 2026, KEŞİF, betimleyici): bayi/yayın ekranındaki muhtemel ganyan (data/canli_oran) ile son ganyan farkı.
Soru: Jason'ın canlı ekrana göre 'değerli' gördüğü atlarda oran kapanışa kadar düşüyor mu (kayma)? Kullanım: python3 -I son_dakika_kayma.py <scratch>"""
import sys,glob,json,os,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/';P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
rows=[]
for f in sorted(glob.glob(R+'data/canli_oran/*.json')):
    try: j=json.load(open(f,encoding='utf-8'))
    except Exception: continue
    for no,o in (j.get('oranlar') or {}).items():
        rows.append((j['tarih'],j['hipodrom'],int(j['kosu']),int(no),float(o),j.get('saat',''),os.path.basename(f)))
C=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','no','canli','saat','dosya'])
C=C.sort_values('saat').groupby(['tarih','hipodrom','kosu','no']).last().reset_index()  # her koşunun en geç ekranı
d=C.merge(P,on=['tarih','hipodrom','kosu','no'],how='inner')
d=d[d.groupby(['tarih','hipodrom','kosu']).ganyan.transform(lambda s:s.round(2).duplicated(keep=False).sum()==0)]  # ekürsüz
d['kayma']=np.log(d.ganyan/d.canli)
d['deger']=d.p_Jason*d.canli>1.1
print('koşu',d.groupby(['tarih','hipodrom','kosu']).ngroups,'at',len(d))
for nm,m in [('tüm atlar',d.index==d.index),('Jason EV>1,1 (canlı oranla)',d.deger)]:
    x=d[m].kayma;print(f'{nm}: n {len(x)} son/canlı oran ort. log {x.mean():+.3f} (≈ x{np.exp(x.mean()):.2f}) ± {x.std()/np.sqrt(max(len(x),1)):.3f}')
