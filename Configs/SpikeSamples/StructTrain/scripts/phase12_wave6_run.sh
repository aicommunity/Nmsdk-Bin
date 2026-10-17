#!/usr/bin/env bash
# PHASE12 Wave6 quality-tails orchestrator.
# Flags: --fs-only --asym-only --phase6-only --branch-only --with-cpp-fs
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
LOG=$ROOT/_repro/phase12_wave6_run.log
mkdir -p "$ROOT/_repro"
export PYTHONUNBUFFERED=1

FS_ONLY=0 ASYM_ONLY=0 PHASE6_ONLY=0 BRANCH_ONLY=0 WITH_CPP=0
for arg in "$@"; do
  case "$arg" in
    --fs-only) FS_ONLY=1 ;;
    --asym-only) ASYM_ONLY=1 ;;
    --phase6-only) PHASE6_ONLY=1 ;;
    --branch-only) BRANCH_ONLY=1 ;;
    --with-cpp-fs) WITH_CPP=1 ;;
    *) echo "unknown: $arg" >&2; exit 2 ;;
  esac
done
ALL=1
[[ $FS_ONLY$ASYM_ONLY$PHASE6_ONLY$BRANCH_ONLY = *1* ]] && ALL=0

exec >>"$LOG" 2>&1
echo "=== START wave6 $(date -u +%Y-%m-%dT%H:%M:%SZ) flags=$* ==="
cd "$ROOT"
python3 scripts/phase12_validate.py list-quality-tails

[[ $ALL -eq 1 || $FS_ONLY -eq 1 ]] && {
  echo "===== W6.1/2 FastSpan ====="
  [[ "$WITH_CPP" == "1" ]] && echo "NOTE: --with-cpp-fs — PulseLib patch must be built"
  set +e
  python3 scripts/phase12_validate.py run-fs --exp EXP_span25ms_fast_C1e9 --force-prepare
  set -e
  if python3 - <<'PY'
from pathlib import Path
import re
t = Path("PHASE12_VALIDATION.md").read_text(encoding="utf-8")
m = re.search(r"^\| EXP_span25ms_fast_C1e9 \| SelectivityFastSpan[^\n]*\| (VALIDATED) \|", t, re.M)
raise SystemExit(0 if m else 1)
PY
  then
    python3 scripts/phase12_validate.py run-fs-all --force-prepare --from EXP_span25ms_fast_preinh_C1e9
  else
    echo "FS25 not VALIDATED — siblings stay ARTIFACT_KEEP"
  fi
}

[[ $ALL -eq 1 || $ASYM_ONLY -eq 1 ]] && {
  echo "===== W6.3/4 AsymRm (manual invest preferred; clones if parents VAL) ====="
  python3 scripts/phase12_validate.py run-asym-clones || true
}

[[ $ALL -eq 1 || $PHASE6_ONLY -eq 1 ]] && {
  echo "===== W6.5 Phase6 ====="
  python3 scripts/phase12_validate.py run-phase6 --exp EXP_480_gen_tiprmin --force-prepare || true
}

[[ $ALL -eq 1 || $BRANCH_ONLY -eq 1 ]] && {
  echo "===== W6.6/7 Branch (invest scripts; no marathon) ====="
  echo "use _repro/_invest/nextseg100 and run-br480 with max_ext=1"
}

echo "===== GATE ====="
python3 scripts/audit_structtrain.py --rebuild-gate || true
echo "=== DONE wave6 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
