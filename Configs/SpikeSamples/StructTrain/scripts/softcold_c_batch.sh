#!/usr/bin/env bash
# SoftCold wave C1 then C2 via posttune_verify (clean workdir, no salvage).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG="${LOG:-$ROOT/_repro/SOFTCOLD_C_$(date -u +%Y%m%dT%H%M%SZ).log}"
RCS="${RCS:-$ROOT/_repro/SOFTCOLD_C_rcs.txt}"
: >"$RCS"
{
  echo "SoftCold C start $(date -u -Iseconds)"
  echo "SHA=$(sha256sum /home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole)"
  # C1
  C1=(
    br50_gen br25_preinh br50_preinh br100_preinh
    br25_nextseg br50_nextseg br100_nextseg
    br480_tiprmin br480_nextseg br480_preinh
    asym25_preinh asym50_preinh asym100_gen asym100_preinh
    phase6_thr_only phase6_preinh250 phase6_ltzcal_twin
    fs25_gen fs25_preinh fs50_preinh fs100_gen fs100_preinh
  )
  # C2
  C2=(
    ltz25_gen ltz25_preinh ltz50_gen ltz50_preinh ltz100_gen ltz100_preinh
    pa00_baseline pa01_ltz_sweep pa02_ltzone_avg pa06_ltzone_int tn_classic
    psi01_050 psi14_260 psi15_270 psi21_100 psi31_200 psi32_300 psi33_300 psi34_400 psi35_400
  )
  WAVE="${WAVE:-C1C2}"
  cases=()
  if [[ "$WAVE" == "C1" || "$WAVE" == "C1C2" ]]; then
    cases+=("${C1[@]}")
  fi
  if [[ "$WAVE" == "C2" || "$WAVE" == "C1C2" ]]; then
    cases+=("${C2[@]}")
  fi
  for case in "${cases[@]}"; do
    echo "==== CASE $case START $(date -u -Iseconds) ===="
    set +e
    python3 scripts/posttune_verify.py --case "$case"
    rc=$?
    set -e
    echo "==== CASE $case END rc=$rc $(date -u -Iseconds) ===="
    echo "$case $rc" >>"$RCS"
  done
  echo "SoftCold C done $(date -u -Iseconds)"
} 2>&1 | tee -a "$LOG"
echo "LOG=$LOG RCS=$RCS"
