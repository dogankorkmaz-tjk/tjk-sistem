#!/bin/bash
# T152 (ön kayıt: hipotez_defteri 2026-11-06 12:00). Repo kökünden, arka planda. Taban MJ N/P önbellekleri T151'den.
cd "$(dirname "$0")/../.."
for V in MJOV MJT9 MJSY; do for N in 1 0; do
  echo "=== $V NOLP=$N $(date +%H:%M)"; TESTBAS=2025-10 TESTSON=2026-10 VAR=$V NOLP=$N NOCACHE=1 python3 data/analiz/entegre_v3_elo2.py 2>&1 | grep -v Warning | tail -2
done; done
python3 data/analiz/t152_rapor.py
