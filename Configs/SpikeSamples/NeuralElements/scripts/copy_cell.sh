#!/usr/bin/env bash
# Clone template/ into cells/<id>/
set -euo pipefail
SRC="${1:?template dir}"
DST="${2:?dest cell dir}"
mkdir -p "$DST"
for f in project.ini Parameters_00.xml Model_00.xml Interface.xml History.xml; do
  if [[ -f "$SRC/$f" ]]; then
    cp -a "$SRC/$f" "$DST/$f"
  fi
done
# project.ini may be named Project.ini in some suites
if [[ -f "$SRC/Project.ini" && ! -f "$DST/project.ini" ]]; then
  cp -a "$SRC/Project.ini" "$DST/project.ini"
fi
echo "Copied $SRC -> $DST"
