#!/usr/bin/env bash
# PHASE12 Wave3: FS unblock → FS×5 → AsymRm packA → B/C clones → LtzCal sync.
# Wave4 Phase6: pass --with-wave4
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
LOG=$ROOT/_repro/phase12_wave3_run.log
mkdir -p "$ROOT/_repro"
export PYTHONUNBUFFERED=1
exec >>"$LOG" 2>&1
echo "=== START wave3 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
cd "$ROOT"

python3 scripts/phase12_validate.py list-wave3

echo "===== W3a: FS25 unblock ====="
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
  echo "===== W3b: run-fs-all ====="
  python3 scripts/phase12_validate.py run-fs-all --force-prepare
else
  echo "FS25 not VALIDATED — skip FS×5 cold; continue AsymRm after FAIL_ROOTCAUSE attempt"
fi

echo "===== W3b: AsymRm packA cold ====="
python3 scripts/phase12_validate.py run-asym-packa-all --force-prepare

echo "===== W3b: AsymRm B/C clones ====="
python3 scripts/phase12_validate.py run-asym-clones

echo "===== W3c: LtzCal sync ====="
python3 scripts/phase12_validate.py sync-ltzcal-all

echo "===== GATE rebuild ====="
python3 scripts/audit_structtrain.py --rebuild-gate || true

if [[ "${1:-}" == "--with-wave4" ]]; then
  echo "===== W4: Phase6 ====="
  python3 scripts/phase12_validate.py run-phase6-all --force-prepare
fi

echo "=== ALL DONE wave3 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
