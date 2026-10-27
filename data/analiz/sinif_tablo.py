"""atyarisi arşivinden (tarih,hipodrom,kosu)->birincilik ikramiyesi, tip. python3 data/analiz/sinif_tablo.py"""
import gzip,json,glob,pandas as pd
rows=[]
for f in sorted(glob.glob('/home/claude/tjk-sistem/data/atyarisi/20*.json.gz')):
    d=f[-18:-8]
    try: j=json.load(gzip.open(f,'rt'))
    except Exception: continue
    for hip,L in (j.get('program') or {}).items():
        if not isinstance(L,list): continue
        for k in L:
            try: kn=int(k['number']); pr=k.get('prizes'); p1=float(pr[0]) if pr else None
            except Exception: continue
            rows.append((d,hip,kn,p1,k.get('typeDescription',''),str(k.get('distance') or '')))
T=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','prize1','tip','mes']).drop_duplicates(['tarih','hipodrom','kosu'])
T.to_pickle('/tmp/claude-0/sinifp.pkl');print(len(T),T.prize1.notna().mean(),T.prize1.describe().round(0).to_dict())
T['ay']=T.tarih.str[:7];print(T.groupby('ay').prize1.median().round(0).iloc[::4].to_dict())
