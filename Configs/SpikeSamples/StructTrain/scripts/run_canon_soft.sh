#!/usr/bin/env bash
# Soft-cold canon re-run: Branch r1→r2 → FastSpan r1→r2
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
BIN=/home/user/Nmsdk/Bin
LOG="$ROOT/_repro/run_canon_soft.log"
exec > >(tee -a "$LOG") 2>&1

commit_partial() {
  local msg="$1"
  cd "$BIN"
  git add Configs/SpikeSamples/StructTrain/_repro/REPRO_COLD_RESULT.md \
          Configs/SpikeSamples/StructTrain/_repro/REPRO_COLD_INVESTIGATION.md \
          Configs/SpikeSamples/StructTrain/PHASE11_COVERAGE.md \
          Configs/SpikeSamples/StructTrain/PHASE8_SHORTSPAN.md \
          Configs/SpikeSamples/StructTrain/SUCCESSFUL_EXPERIMENTS.md 2>/dev/null || true
  shopt -s nullglob
  local csvs=(Configs/SpikeSamples/StructTrain/_repro/*/r*/Test/SelectivityLog/results*.csv)
  ((${#csvs[@]})) && git add -f "${csvs[@]}"
  git diff --cached --quiet && return 0
  git commit -m "$(cat <<EOM
${msg}
EOM
)"
}

for fam in branch fastspan; do
  for rep in 1 2; do
    echo "===== CANON $fam r$rep $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
    python3 -u "$ROOT/scripts/repro_cold_harness.py" run --family "$fam" --rep "$rep" --cold soft
    if [[ "$fam" == branch && "$rep" == 2 ]]; then
      commit_partial "repro: cold harness C4.br soft canon r1-r2."
    fi
  done
done
python3 "$ROOT/scripts/repro_cold_harness.py" compare
commit_partial "repro: cold harness soft canon ≥gold."
echo "CANON DONE"
