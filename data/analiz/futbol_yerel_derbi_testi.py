import pandas as pd,numpy as np
X=pd.read_pickle('X.pkl')
d=pd.read_pickle('fd.pkl').sort_values('Date').reset_index(drop=True)
d=d.dropna(subset=['HC','AC','HY','AY','HF','AF','HS','AS','HST','AST']).reset_index(drop=True)
X=X.dropna(subset=[c for c in X.columns if c!='ref'])
H=d.HomeTeam.reindex(X.idx.values).values;A=d.AwayTeam.reindex(X.idx.values).values
sehir={'Istanbul':['Galatasaray','Fenerbahce','Besiktas','Buyuksehyr','Kasimpasa','Karagumruk','Istanbulspor','Pendikspor','Umraniyespor','Eyupspor'],
 'Ankara':['Ankaragucu','Genclerbirligi'],'Izmir':['Goztep','Altay'],'Kocaeli':['Kocaelispor'],'Adana':['Ad. Demirspor'],
 'Trabzon':['Trabzonspor'],'Samsun':['Samsunspor']}
tc={t:c for c,l in sehir.items() for t in l}
X['yerel']=[1. if (h in tc and a in tc and tc[h]==tc[a]) else 0. for h,a in zip(H,A)]
X['trab_sam']=[1. if {h,a}=={'Trabzonspor','Samsunspor'} else 0. for h,a in zip(H,A)]
T=X[X.lig=='T1']
for c in ('yerel','trab_sam'):
    a=T[T[c]==1];b=T[T[c]==0];print(c,len(a),'kart %.2f (diğer %.2f) faul %.1f (%.1f) korner %.1f (%.1f)'%(a.kart.mean(),b.kart.mean(),a.faul.mean(),b.faul.mean(),a.kor.mean(),b.kor.mean()))
# büyük 4 dışı yerel
B4={'Galatasaray','Fenerbahce','Besiktas'}
m=[(1. if (X.yerel.iloc[i]==1 and not(H[i] in B4 and A[i] in B4)) else 0.) for i in range(len(X))]
X['yerel_kucuk']=m;T=X[X.lig=='T1'];a=T[T.yerel_kucuk==1];b=T[(T.yerel==0)];print('yerel (G-F-B üçlüsü hariç)',len(a),'kart %.2f (diğer %.2f)'%(a.kart.mean(),b.kart.mean()))
print(sorted(set([(h,a) for h,a,y in zip(H,A,X.yerel) if y==1 and h not in B4]))[:12])
