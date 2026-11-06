#!/bin/bash
# T154 (ön kayıt 2026-11-06 12:30): MJP piyasasız + piyasalı; taban MJ çıktıları T152'den
cd /home/claude/tjk-sistem
for N in 1 0; do
  echo "=== MJP NOLP=$N $(date +%H:%M)"; TESTBAS=2025-10 TESTSON=2026-10 VAR=MJP NOLP=$N python3 data/analiz/t154_harness.py 2>&1 | grep -v Warning | tail -3
done
echo "HEPSİ BİTTİ $(date +%H:%M)"
