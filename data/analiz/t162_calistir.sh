#!/bin/bash
# T162: MJT9S piyasasız + piyasalı (taban MJT9 ve MJ çıktıları T152'den)
cd /home/claude/tjk-sistem
for N in 1 0; do
  echo "=== MJT9S NOLP=$N $(date +%H:%M)"; TESTBAS=2025-10 TESTSON=2026-10 VAR=MJT9S NOLP=$N python3 data/analiz/entegre_v3_elo2.py 2>&1 | grep -v Warning | tail -4
done
echo "HEPSİ BİTTİ $(date +%H:%M)"
