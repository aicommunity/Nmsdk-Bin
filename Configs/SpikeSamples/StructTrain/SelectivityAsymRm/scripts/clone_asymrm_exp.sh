#!/usr/bin/env bash
# Clone SelectivityAsymRm EXP Train+Test into a new EXP_* directory.
# Never writes the source. Refuses if destination already exists.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  echo "Usage: $0 <SRC_EXP> <DST_EXP>" >&2
  echo "  SRC_EXP / DST_EXP: names like EXP_span50ms_packA_gen" >&2
  exit 2
}

[[ $# -eq 2 ]] || usage
SRC_NAME="$1"
DST_NAME="$2"

[[ "$SRC_NAME" == EXP_* ]] || { echo "SRC must be EXP_*: $SRC_NAME" >&2; exit 1; }
[[ "$DST_NAME" == EXP_* ]] || { echo "DST must be EXP_*: $DST_NAME" >&2; exit 1; }

SRC="$ROOT/$SRC_NAME"
DST="$ROOT/$DST_NAME"

[[ -d "$SRC/Train" && -d "$SRC/Test" ]] || {
  echo "SRC incomplete (need Train+Test): $SRC" >&2
  exit 1
}
[[ -e "$DST" ]] && {
  echo "Refuse overwrite: $DST already exists" >&2
  exit 1
}

mkdir -p "$DST/Train" "$DST/Test"
rsync -a --exclude EventsLog --exclude StatisticLog --exclude History.xml \
  "$SRC/Train/" "$DST/Train/"
rsync -a --exclude EventsLog --exclude StatisticLog --exclude History.xml \
  "$SRC/Test/" "$DST/Test/"

set_project_name() {
  local ini="$1" name="$2"
  [[ -f "$ini" ]] || return 0
  sed -i "s|<ProjectName>[^<]*</ProjectName>|<ProjectName>${name}</ProjectName>|" "$ini"
}
set_project_name "$DST/Train/Project.ini" "$DST_NAME"
set_project_name "$DST/Test/Project.ini" "${DST_NAME}_Test"

PILOT_META="$ROOT/grid_cells_pilot.tsv"
if [[ -f "$ROOT/grid_cells.tsv" ]]; then
  # Copy meta row from main grid if present; else leave pilot file alone for caller.
  hdr=$(head -1 "$ROOT/grid_cells.tsv")
  row=$(awk -F'\t' -v e="$SRC_NAME" 'NR>1 && $1==e {print; exit}' "$ROOT/grid_cells.tsv" || true)
  if [[ -n "$row" ]]; then
    [[ -f "$PILOT_META" ]] || echo "$hdr" >"$PILOT_META"
    new_row=$(printf '%s\n' "$row" | awk -F'\t' -v d="$DST_NAME" 'BEGIN{OFS="\t"} {$1=d; print}')
    if ! awk -F'\t' -v d="$DST_NAME" 'NR>1 && $1==d {found=1} END{exit !found}' "$PILOT_META"; then
      echo "$new_row" >>"$PILOT_META"
      echo "Appended $DST_NAME to grid_cells_pilot.tsv"
    else
      echo "grid_cells_pilot.tsv already has $DST_NAME"
    fi
  else
    echo "WARN: no META row for $SRC_NAME in grid_cells.tsv — add $DST_NAME to grid_cells_pilot.tsv manually" >&2
  fi
fi

echo "Cloned $SRC_NAME → $DST_NAME (source untouched)"
