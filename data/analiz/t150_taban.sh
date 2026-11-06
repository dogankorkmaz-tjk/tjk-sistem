#!/bin/bash
# T150 (ön kayıt: hipotez_defteri 2026-11-06 04:10). Repo kökünden: bash data/analiz/t150_taban.sh  (arka planda: nohup setsid ... > /tmp/t150.log 2>&1 &)
set -e
python3 data/analiz/jason_d_uret.py
python3 data/analiz/arsiv_mp_uret.py
python3 data/analiz/jason_wf.py
TESTBAS=2025-10 TESTSON=2026-10 VAR=MJ NOLP=1 NOCACHE=1 python3 data/analiz/entegre_v3_elo2.py
python3 data/analiz/t150_rapor.py
