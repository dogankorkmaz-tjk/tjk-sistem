"""atyarisi arşivinden (tarih,hipodrom,kosu,no)->ekipman dizgesi. python3 data/analiz/ekip_tablo.py"""
import gzip,json,glob,pandas as pd
rows=[]
for f in sorted(glob.glob('/home/claude/tjk-sistem/data/atyarisi/20*.json.gz')):
    d=f[-18:-8]
    try: j=json.load(gzip.open(f,'rt'))
    except Exception: continue
    for hip,L in (j.get('program') or {}).items():
        if not isinstance(L,list): continue
        for k in L:
            try: kn=int(k['number'])
            except Exception: continue
            for h in k.get('horses') or []:
                try: no=int(h.get('number'))
                except Exception: continue
                rows.append((d,hip,kn,no,str(h.get('equipment') or '').strip()))
T=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','no','ekip'])
T.to_pickle('/tmp/claude-0/ekip.pkl');print(len(T),T.tarih.min(),T.tarih.max(),(T.ekip!='').mean());print(T.ekip.value_counts().head(8).to_dict())
