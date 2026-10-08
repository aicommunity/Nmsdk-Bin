#!/usr/bin/env bash
# SoftCold full49 15m status (rcs.d shards; no side effects on train).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RCS_DIR="${RCS_DIR:-$ROOT/_repro/rcs.d}"
LOG="${SOFTCOLD_FULL49_LOG:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/SOFTCOLD_full_matrix_20261007.log}"
OUT="${SOFTCOLD_FULL49_STATUS:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/softcold_full49_15m_status.txt}"
TS="$(date -u -Iseconds)"
done_n=0
pass=0
fail=0
if compgen -G "$RCS_DIR"/*.rc >/dev/null 2>&1; then
  done_n=$(ls -1 "$RCS_DIR"/*.rc 2>/dev/null | wc -l | tr -d ' ')
  pass=$(awk '$2==0{c++}END{print c+0}' "$RCS_DIR"/*.rc 2>/dev/null || echo 0)
  fail=$(awk '$2!=0 && NF>=2{c++}END{print c+0}' "$RCS_DIR"/*.rc 2>/dev/null || echo 0)
fi
active=""
while IFS= read -r line; do
  [[ "$line" == *python3\ -u\ scripts/posttune_verify.py* ]] || continue
  [[ "$line" == */bin/bash* ]] && continue
  c="${line#*--case }"
  c="${c%% *}"
  active="${active:+$active,}$c"
done < <(pgrep -af 'posttune_verify.py --case' 2>/dev/null || true)
[[ -n "$active" ]] || active="?"
parallel_alive=N
pgrep -f 'softcold_full_matrix_parallel.sh' >/dev/null 2>&1 && parallel_alive=Y
disk="$(df -BG --output=avail / | tail -1 | tr -dc '0-9')"
done_all=""
[[ -f "$LOG" ]] && grep -q 'SoftCold full matrix PARALLEL done' "$LOG" 2>/dev/null && done_all="DONE"
[[ -f "$LOG" ]] && grep -q 'ERROR: RCS incomplete' "$LOG" 2>/dev/null && done_all="ERROR"
line="$TS done=$done_n/49 pass=$pass fail=$fail active=$active parallel_alive=$parallel_alive disk=${disk}G matrix=$done_all"
echo "$line"
mkdir -p "$(dirname "$OUT")"
echo "$line" >>"$OUT"
[[ "$done_all" == "DONE" || "$done_all" == "ERROR" ]] && exit 0
exit 0
