#!/usr/bin/env bash
# Print checklist before committing a NeuralElements round (agent still commits).
set -euo pipefail
ROOT="${1:-.}"
echo "=== commit_round checklist: $ROOT ==="
echo "Include: configs, metrics*.csv, REPORT.md, JOURNAL*.md, Interface.xml"
echo "Exclude: EventsLog/, StatisticLog/, *.log (console), large dumps"
git -C "$ROOT" status -sb 2>/dev/null || git status -sb
