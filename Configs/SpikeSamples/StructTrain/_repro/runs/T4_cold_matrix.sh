#!/usr/bin/env bash
# D4 cold matrix: 6 posttune_verify cases (T2-style logging).
set -uo pipefail
ROOT=/home/user/Nmsdk
cd "$ROOT"
LOGDIR="$ROOT/Bin/Configs/SpikeSamples/StructTrain/_repro"
UTC=$(date -u +%Y%m%dT%H%M%SZ)
BATCH_LOG="$LOGDIR/T4_cold_matrix_${UTC}.log"
RCS="$LOGDIR/T4_case_rcs_${UTC}.txt"
SUMMARY_JSON="$ROOT/Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/D4_matrix_summary.json"
echo "T4 cold matrix start $UTC" | tee "$BATCH_LOG"
echo "console=$(sha256sum Bin/Platform/Linux/NeuroModelerConsole | awk '{print $1}')" | tee -a "$BATCH_LOG"
declare -a RESULTS=()
run_case() {
  local name="$1"; shift
  local label="$1"; shift
  echo "=== CASE $label ($name) START $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$BATCH_LOG"
  set +e
  python3 -B Bin/Configs/SpikeSamples/StructTrain/scripts/posttune_verify.py --case "$name" "$@" 2>&1 | tee -a "$BATCH_LOG"
  local rc=${PIPESTATUS[0]}
  set -e
  echo "$label $name rc=$rc" | tee -a "$RCS" | tee -a "$BATCH_LOG"
  echo "=== CASE $label END rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$BATCH_LOG"
  RESULTS+=("$label:$name:$rc")
  return 0
}
# Order: shorter cases first; br100_search last (train_t=2400).
run_case br25_off br25_off_cold
run_case asym25 asym25_cold
run_case asym50 asym50_cold_d2
run_case br100_keep br100_keep_cold
run_case phase6_480 phase6_480_cold
run_case br100_search br100_search_cold
echo "T4 batch done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BATCH_LOG"
export T4_ROOT="$ROOT" T4_RCS="$RCS" T4_UTC="$UTC" T4_SUMMARY_JSON="$SUMMARY_JSON"
python3 - <<'PY'
import json, re, os
from pathlib import Path
root = Path(os.environ["T4_ROOT"])
rcs = Path(os.environ["T4_RCS"])
utc = os.environ["T4_UTC"]
rows = []
for line in rcs.read_text().splitlines():
    m = re.match(r"(\S+) (\S+) rc=(\-?\d+)", line.strip())
    if m:
        rows.append({"label": m.group(1), "case": m.group(2), "rc": int(m.group(3))})
out = {
  "batch": "T4_cold_matrix",
  "utc": utc,
  "cases": rows,
  "pass_count": sum(1 for r in rows if r["rc"] == 0),
  "n": len(rows),
  "seven_pass_claim": False,
  "phase6_expect_fires_harness": "10000010",
  "phase6_strict_fires": "10000000",
  "note": "Do not claim 7/7 PASS unless all six rc=0 and br25_on gold also green.",
}
path = Path(os.environ["T4_SUMMARY_JSON"])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2) + "\n")
print("wrote", path)
md = root / "Bin/Configs/SpikeSamples/StructTrain/_repro/POSTTUNE_VERIFY_RESULT.md"
block = ["", f"## T4 cold matrix {utc}", ""]
for r in rows:
    block.append(f"- `{r['case']}` ({r['label']}): rc={r['rc']}")
block.append("")
block.append("- phase6 harness expect_fires=`10000010`; strict reference=`10000000`")
block.append(f"- summary: `{path}`")
block.append("")
md.write_text(md.read_text(encoding="utf-8") + "\n".join(block) + "\n", encoding="utf-8")
PY
