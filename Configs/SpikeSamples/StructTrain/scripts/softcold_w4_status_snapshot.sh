#!/usr/bin/env bash
# Compact W4 SoftCold status line for hourly monitor (no side effects on train).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RCS="$ROOT/_repro/SOFTCOLD_HEAD_rcs.txt"
LOG="${SOFTCOLD_W4_LOG:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/SOFTCOLD_full_matrix_w4.log}"
OUT="${SOFTCOLD_W4_STATUS:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/softcold_w4_hourly_status.txt}"
TS="$(date -u -Iseconds)"
done_n=0
pass=0
fail=0
if [[ -f "$RCS" ]]; then
  done_n=$(wc -l <"$RCS" | tr -d ' ')
  pass=$(awk '$2==0{c++}END{print c+0}' "$RCS")
  fail=$(awk '$2==1{c++}END{print c+0}' "$RCS")
fi
active_case="?"
while IFS= read -r _verify_line; do
  [[ "$_verify_line" == *python3\ -u\ scripts/posttune_verify.py* ]] || continue
  [[ "$_verify_line" == */bin/bash* ]] && continue
  active_case="${_verify_line#*--case }"
  active_case="${active_case%% *}"
  break
done < <(pgrep -af 'posttune_verify.py --case' 2>/dev/null || true)
unset _verify_line
train="running"
pgrep -f 'softcold_full_matrix.sh' >/dev/null || train="idle"
done_all=""
[[ -f "$LOG" ]] && grep -q 'DONE_ALL\|full matrix W4 done' "$LOG" 2>/dev/null && done_all="DONE"

line="$TS done=$done_n/49 pass=$pass fail=$fail train=$train case=${active_case:-?} matrix=$done_all"
echo "$line"
echo "$line" >>"$OUT"
