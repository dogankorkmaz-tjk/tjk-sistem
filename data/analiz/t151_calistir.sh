#!/bin/bash
# T151 (ön kayıt: hipotez_defteri 2026-11-06 10:45). Repo kökünden, arka planda.
cd "$(dirname "$0")/../.."
for V in MJ MJDE MJDE1 MJDEE; do for N in 1 0; do
  echo "=== $V NOLP=$N $(date +%H:%M)"; TESTBAS=2025-10 TESTSON=2026-10 VAR=$V NOLP=$N NOCACHE=1 python3 data/analiz/entegre_v3_elo2.py 2>&1 | grep -v Warning | tail -3
done; done
python3 data/analiz/t151_rapor.py
# not: MJ NOLP=1 de aynı veriyle yeniden üretilir (T150 dosyası sabah 04:43 verisiyle)
