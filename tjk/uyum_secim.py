"""T131: uyum skoru (dondurulmuş) + AGF sırası → seçim kaydı. Kural: AGF sırası >=3 ∧ uyum sırası <=2. Kullanım: python3 tjk/uyum_secim.py [YYYY-MM-DD]
Yazar: data/t131_kayit/<gun>_secim.csv ve docs/data/uyum_secim.json. Sonuç görülmeden kural değişmez."""
import sys,json,os,glob,datetime,pandas as pd,numpy as np
gun=sys.argv[1] if len(sys.argv)>1 else json.load(open('docs/data/bugun.json'))['tarih']
U=pd.read_csv(f'data/t131_kayit/{gun}_uyum.csv')
f=f'data/agf_zaman/{gun}.csv.gz'
if not os.path.exists(f): print('AGF yok',f); sys.exit(1)
A=pd.read_csv(f); A=A.sort_values('saat').groupby(['hipodrom','kosu','no'],as_index=False).tail(1)       # son anlık görüntü
M=U.merge(A[['hipodrom','kosu','no','agf','saat']],on=['hipodrom','kosu','no'],how='left')
M['rkA']=M.groupby(['hipodrom','kosu']).agf.rank(ascending=False,method='first')
M['secim']=(M.rkA>=3)&(M.rkU<=2)
M.to_csv(f'data/t131_kayit/{gun}_secim.csv',index=False)
saat={}
try:
    for h in json.load(open('docs/data/bugun.json'))['hipodromlar']:
        for k in h['kosular']: saat[(h['ad'].lower().replace('ı','i').replace('ü','u').replace('ş','s').replace('ğ','g').replace('ö','o').replace('ç','c').replace('i̇','i'),k['kosu'])]=k['saat']
except Exception: pass
out={'gun':gun,'olusturma':datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),'kural':'AGF sırası >=3 ve uyum sırası <=2 (T131, deneysel, bahis önerisi değil)','kosular':[]}
for (h,k),g in M.groupby(['hipodrom','kosu']):
    s=g[g.secim].sort_values('rkU')
    out['kosular'].append({'hipodrom':h,'kosu':int(k),'saat':saat.get((h,int(k))),'agf_saat':g.saat.dropna().iloc[0] if g.saat.notna().any() else None,
        'secimler':[{'no':int(r.no),'at':r.at,'uyum_sirasi':int(r.rkU),'agf_sirasi':int(r.rkA),'agf':float(r.agf),'U':round(float(r.U),3)} for r in s.itertuples()]})
json.dump(out,open('docs/data/uyum_secim.json','w'),ensure_ascii=False,indent=1)
print(gun,'seçim sayısı',int(M.secim.sum()),'koşu',M.groupby(['hipodrom','kosu']).ngroups)
