#!/usr/bin/env bash
# PHASE12 Wave5 tails closure orchestrator.
# Flags (optional, mutually usable):
#   --phase6-only --fs-only --asym-only --branch-fail-only --with-cpp-fs --ltzcal-only
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
LOG=$ROOT/_repro/phase12_wave5_run.log
mkdir -p "$ROOT/_repro"
export PYTHONUNBUFFERED=1

PHASE6_ONLY=0
FS_ONLY=0
ASYM_ONLY=0
BRANCH_ONLY=0
LTZCAL_ONLY=0
WITH_CPP_FS=0
for arg in "$@"; do
  case "$arg" in
    --phase6-only) PHASE6_ONLY=1 ;;
    --fs-only) FS_ONLY=1 ;;
    --asym-only) ASYM_ONLY=1 ;;
    --branch-fail-only) BRANCH_ONLY=1 ;;
    --ltzcal-only) LTZCAL_ONLY=1 ;;
    --with-cpp-fs) WITH_CPP_FS=1 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done
# default = all stages if no filter
ALL=1
if [[ $PHASE6_ONLY$FS_ONLY$ASYM_ONLY$BRANCH_ONLY$LTZCAL_ONLY = *1* ]]; then
  ALL=0
fi

exec >>"$LOG" 2>&1
echo "=== START wave5 $(date -u +%Y-%m-%dT%H:%M:%SZ) flags=$* ==="
cd "$ROOT"

python3 scripts/phase12_validate.py list-tails

run_phase6() {
  echo "===== W5.1: Phase6 soft-cold retry ====="
  python3 scripts/phase12_validate.py run-phase6-all --force-prepare
}

run_ltzcal25() {
  echo "===== W5.2: LtzCal span25 re-sync/re-gate ====="
  set +e
  python3 scripts/phase12_validate.py sync-ltzcal --exp EXP_span25ms_packA_gen
  python3 scripts/phase12_validate.py sync-ltzcal --exp EXP_span25ms_packA_preinh
  set -e
}

run_fs() {
  echo "===== W5.3/W5.4: FastSpan ====="
  if [[ "$WITH_CPP_FS" == "1" ]]; then
    echo "NOTE: --with-cpp-fs set; ensure PulseLib patch+rebuild already done"
  fi
  set +e
  python3 scripts/phase12_validate.py run-fs --exp EXP_span25ms_fast_C1e9 --force-prepare
  FS25_RC=$?
  set -e
  echo "FS25_RC=$FS25_RC"
  if python3 - <<'PY'
from pathlib import Path
import re
t = Path("PHASE12_VALIDATION.md").read_text(encoding="utf-8")
m = re.search(
    r"^\| EXP_span25ms_fast_C1e9 \| SelectivityFastSpan[^\n]*\| (VALIDATED) \|",
    t,
    re.M,
)
raise SystemExit(0 if m else 1)
PY
  then
    python3 scripts/phase12_validate.py run-fs-all --force-prepare --from EXP_span25ms_fast_preinh_C1e9
  else
    echo "FS25 not VALIDATED — siblings stay BLOCKED/ARTIFACT_KEEP (manual close in W5.4)"
  fi
}

run_asym() {
  echo "===== W5.5/W5.6: AsymRm midflat + clones (manual invest preferred) ====="
  echo "Use invest scripts / run-asym-packa for span50/100; clones via run-asym-clones"
  python3 scripts/phase12_validate.py run-asym-clones || true
}

run_branch() {
  echo "===== W5.7/W5.8: Branch FAIL backlog (prefer ARTIFACT_KEEP close) ====="
  echo "nextseg100 / br480: use dedicated invest; default ARTIFACT_KEEP via manifest edit"
}

[[ $ALL -eq 1 || $PHASE6_ONLY -eq 1 ]] && run_phase6
[[ $ALL -eq 1 || $LTZCAL_ONLY -eq 1 ]] && run_ltzcal25
[[ $ALL -eq 1 || $FS_ONLY -eq 1 ]] && run_fs
[[ $ALL -eq 1 || $ASYM_ONLY -eq 1 ]] && run_asym
[[ $ALL -eq 1 || $BRANCH_ONLY -eq 1 ]] && run_branch

echo "===== GATE rebuild ====="
python3 scripts/audit_structtrain.py --rebuild-gate || true

echo "=== ALL DONE wave5 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
