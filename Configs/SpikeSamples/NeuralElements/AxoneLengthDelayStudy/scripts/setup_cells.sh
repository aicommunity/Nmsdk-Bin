#!/usr/bin/env bash
# Clone templates → cells, patch length, structural -S for chain/cad, ensure Watch.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NE_SCRIPTS="$(cd "$ROOT/../scripts" && pwd)"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-4}"
GRID="$ROOT/grid_cells.tsv"
PATCH="$NE_SCRIPTS/patch_param.py"
COPY="$NE_SCRIPTS/copy_cell.sh"
ENSURE="$ROOT/scripts/ensure_watch.py"

python3 "$ROOT/scripts/build_templates.py"

# Validate templates (warnings about missing README are OK)
for t in delay chain chain_and_delay; do
  out="$("$NM" --check-config "$ROOT/templates/$t/project.ini" 2>&1 || true)"
  echo "$out" | tail -5
  if echo "$out" | grep -q 'Configuration is INVALID'; then
    echo "template $t INVALID"
    exit 1
  fi
  python3 "$ENSURE" "$ROOT/templates/$t"
  echo "template $t VALID"
done

mkdir -p "$ROOT/cells"
# skip header
mapfile -t ROWS < <(tail -n +2 "$GRID")

title_for() {
  local cell="$1" model="$2" lp="$3" lv="$4"
  case "$lp" in
    DelayTime)
      python3 -c "print(f'AxoneLengthDelay: DelayTime={float(\"$lv\")*1000:g}ms')"
      ;;
    NumSegments)
      echo "AxoneLengthDelay: NumSegments=$lv"
      ;;
    NumNodes)
      echo "AxoneLengthDelay: NumNodes=$lv Internode=2ms"
      ;;
    *)
      echo "AxoneLengthDelay: $cell"
      ;;
  esac
}

for row in "${ROWS[@]}"; do
  [[ -z "$row" ]] && continue
  IFS=$'\t' read -r cell model class lp lv unit template <<<"$row"
  dst="$ROOT/cells/$cell"
  rm -rf "$dst"
  bash "$COPY" "$ROOT/templates/$template" "$dst"
  python3 "$PATCH" "$dst/Model_00.xml" --set "$lp" "$lv"
  python3 "$PATCH" "$dst/Parameters_00.xml" --set "$lp" "$lv"
  python3 - <<PY
import json
from pathlib import Path
meta = {
  "cell": "$cell",
  "model": "$model",
  "class": "$class",
  "length_param": "$lp",
  "length_value": "$lv",
  "length_unit": "$unit",
  "template": "$template",
}
Path("$dst/meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY
  title="$(title_for "$cell" "$model" "$lp" "$lv")"
  python3 "$ENSURE" "$dst" --title "$title"
  echo "cloned $cell"
done

# Structural expand (chain + cad only), parallel ≤4.
# For length==1: expand via 2 then back to 1 so Segment1 is persisted.
running=0
pids=()
dirs=()
fail=0
wait_one() {
  local pid="${pids[0]}"
  local d="${dirs[0]}"
  pids=("${pids[@]:1}")
  dirs=("${dirs[@]:1}")
  if wait "$pid"; then
    echo "STRUCT OK  $d"
  else
    echo "STRUCT FAIL $d"
    fail=$((fail + 1))
  fi
  running=$((running - 1))
}

struct_one() {
  local cell="$1" model="$2" lp="$3" lv="$4"
  local dst="$ROOT/cells/$cell"
  if [[ "$lv" == "1" ]]; then
    python3 "$PATCH" "$dst/Model_00.xml" --set "$lp" 2
    python3 "$PATCH" "$dst/Parameters_00.xml" --set "$lp" 2
    (cd "$dst" && "$NM" -c project.ini -s -t 0.05 -x -S >"setup_struct.log" 2>&1)
    python3 "$PATCH" "$dst/Model_00.xml" --set "$lp" 1
    python3 "$PATCH" "$dst/Parameters_00.xml" --set "$lp" 1
    (cd "$dst" && "$NM" -c project.ini -s -t 0.05 -x -S >>"setup_struct.log" 2>&1)
    # prune leftover Segment2/Delay1 if Shorten did not persist
    python3 - <<'PY' "$dst"
import re, sys
from pathlib import Path
cell = Path(sys.argv[1])
for fname in ["Model_00.xml", "Parameters_00.xml"]:
    p = cell / fname
    if not p.is_file():
        continue
    text = p.read_text(encoding="utf-8")
    text = re.sub(r'\n\t+<Segment2 Class="NAxoneSegment">.*?</Segment2>', '', text, count=1, flags=re.DOTALL)
    text = re.sub(r'\n\t+<Delay1 Class="NAxoneDelay">.*?</Delay1>', '', text, count=1, flags=re.DOTALL)
    def drop_link(m):
        b = m.group(0)
        return '' if ('Segment2' in b or 'Delay1' in b) else b
    if '<Links' in text:
        text = re.sub(r'\n\t\t\t<elem Type="ULink">.*?</elem>', drop_link, text, flags=re.DOTALL)
        elems = len(re.findall(r'<elem Type="ULink">', text))
        text = re.sub(r'<Links Type="ULinksList" Size="\d+">', f'<Links Type="ULinksList" Size="{elems}">', text, count=1)
    p.write_text(text, encoding="utf-8")
PY
  else
    (cd "$dst" && "$NM" -c project.ini -s -t 0.05 -x -S >"setup_struct.log" 2>&1)
  fi
}

for row in "${ROWS[@]}"; do
  [[ -z "$row" ]] && continue
  IFS=$'\t' read -r cell model class lp lv unit template <<<"$row"
  if [[ "$model" != "chain" && "$model" != "cad" ]]; then
    continue
  fi
  while (( running >= MAX_JOBS )); do wait_one; done
  echo "STRUCT START $cell"
  (
    struct_one "$cell" "$model" "$lp" "$lv"
  ) &
  pids+=($!)
  dirs+=("$cell")
  running=$((running + 1))
done
while (( running > 0 )); do wait_one; done
if (( fail > 0 )); then
  echo "structural save failures=$fail"
  exit 1
fi

# Restore Watch + verify segments/threshold + check-config
for row in "${ROWS[@]}"; do
  [[ -z "$row" ]] && continue
  IFS=$'\t' read -r cell model class lp lv unit template <<<"$row"
  dst="$ROOT/cells/$cell"
  title="$(title_for "$cell" "$model" "$lp" "$lv")"
  python3 "$ENSURE" "$dst" --title "$title"

  if [[ "$model" == "chain" ]]; then
    n="$lv"
    got=$(grep -c 'Class="NAxoneSegment"' "$dst/Model_00.xml" || true)
    echo "$cell segments=$got need=$n"
    # NumSegments=1 may keep empty Components (built at runtime), like AxoneChain1
    if (( n > 1 && got < n )); then
      echo "FAIL $cell: expected >=$n segments, got $got"
      exit 1
    fi
  fi
  if [[ "$model" == "cad" ]]; then
    n="$lv"
    got=$(grep -c 'Class="NAxoneSegment"' "$dst/Model_00.xml" || true)
    echo "$cell segments=$got need=$n"
    if (( n > 1 && got < n )); then
      echo "FAIL $cell: expected >=$n nodes/segments, got $got"
      exit 1
    fi
  fi

  # Force LTZone Threshold≈0.03 if needed (do not touch CalculationDurationThreshold)
  python3 - <<'PY' "$dst/Model_00.xml" "$dst/Parameters_00.xml"
import re, sys
from pathlib import Path

def fix(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    def repl_ltz(m):
        block = m.group(0)
        block2 = re.sub(
            r'(<Threshold Type="d"[^>]*>)[^<]*(</Threshold>)',
            r'\g<1>0.03\2',
            block,
        )
        return block2
    text2 = re.sub(r'<LTZone\b[^>]*>.*?</LTZone>', repl_ltz, text, flags=re.DOTALL)
    path.write_text(text2, encoding="utf-8")

for p in sys.argv[1:]:
    fix(Path(p))
PY

  out="$("$NM" --check-config "$dst/project.ini" 2>&1 || true)"
  echo "$out" | tail -3
  if echo "$out" | grep -q 'Configuration is INVALID'; then
    echo "FAIL $cell INVALID"
    exit 1
  fi
done

python3 - <<PY
import json
from pathlib import Path
root = Path("$ROOT")
meta = {
  "study": "AxoneLengthDelayStudy",
  "n_cells": len(list((root/"cells").glob("*/project.ini"))),
  "sim_t_default": 0.5,
  "max_jobs_default": 4,
}
(root/"meta.json").write_text(json.dumps(meta, indent=2)+"\n", encoding="utf-8")
print("setup done:", meta)
PY
