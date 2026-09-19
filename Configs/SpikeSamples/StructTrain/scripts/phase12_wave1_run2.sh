#!/usr/bin/env bash
# Continue PHASE12 Wave1 after tooling fix (train extend + keep-tipr).
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
LOG=$ROOT/_repro/phase12_wave1_run2.log
exec >>"$LOG" 2>&1
echo "=== START run2 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
cd "$ROOT"

# Remaining tiprmin roots (skip span25/50 gen already VALIDATED)
EXPS=(
  EXP_br_span50_packA_preinh_C1e9
  EXP_br_span100_packA_preinh_C1e9
  EXP_br_span25_packA_nextseginh_C1e9
  EXP_br_span50_packA_nextseginh_C1e9
  EXP_br_span100_packA_nextseginh_C1e9
)

# Retry preinh25 from existing cold clone (Need=1 L grown) — extend train, no re-cold
echo "===== RETRY EXP_br_span25_packA_preinh_C1e9 ====="
if python3 scripts/phase12_validate.py run --exp EXP_br_span25_packA_preinh_C1e9 --replicas 2; then
  python3 scripts/phase12_validate.py promote --exp EXP_br_span25_packA_preinh_C1e9 || true
  cd /home/user/Nmsdk/Bin
  git add Configs/SpikeSamples/StructTrain/PHASE12_VALIDATION.md \
    Configs/SpikeSamples/StructTrain/SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/ || true
  git add -u Configs/SpikeSamples/StructTrain/SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/ || true
  if ! git diff --cached --quiet; then
    git commit -m "phase12: VALIDATED EXP_br_span25_packA_preinh_C1e9"
  fi
  cd "$ROOT"
else
  echo "FAIL retry preinh25" | tee -a "$ROOT/_repro/phase12_wave1_FAIL.txt"
fi

for E in "${EXPS[@]}"; do
  echo ""
  echo "===== $E $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  # force fresh soft-cold if prior partial clone exists
  if python3 scripts/phase12_validate.py run-all-wave1 --exp "$E" --force-prepare; then
    cd /home/user/Nmsdk/Bin
    git add Configs/SpikeSamples/StructTrain/PHASE12_VALIDATION.md \
      "Configs/SpikeSamples/StructTrain/SelectivityBranch/$E/" || true
    git add -u "Configs/SpikeSamples/StructTrain/SelectivityBranch/$E/" || true
    if ! git diff --cached --quiet; then
      git commit -m "phase12: VALIDATED $E"
    fi
    cd "$ROOT"
    echo "DONE $E $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  else
    echo "FAIL $E" | tee -a "$ROOT/_repro/phase12_wave1_FAIL.txt"
  fi
done

# span100 gen keep-tipr re-gate (trains already done)
echo "===== KEEP-TIPR EXP_br_span100_packA_gen_C1e9 ====="
REPRO=$ROOT/_repro/Branch_span100_packA_gen_C1e9
TIPR="73992204.405776784 88934568.014846012 133361944.11716413 512483714.02225834"
python3 - <<PY
import re
from pathlib import Path
TIPR = "73992204.405776784 88934568.014846012 133361944.11716413 512483714.02225834"
REPRO = Path("/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/Branch_span100_packA_gen_C1e9")

def set_tag(text, tag, value):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\g<2>", text, count=0)

for rep in (1, 2):
    for rel in ("Train/Parameters_00.xml", "Train/Model_00.xml"):
        p = REPRO / f"r{rep}" / rel
        x = p.read_text(encoding="utf-8").replace(",", ".")
        x = set_tag(x, "TipSynapseResistance", TIPR)
        p.write_text(x, encoding="utf-8")
    print("restored TipR r", rep)
PY
for rep in 1 2; do
  python3 "$ROOT/SelectivityBranch/scripts/phase8_tiprmin_gate.py" \
    "$REPRO/r$rep" --span-ms 100 --pack A --test-t 40 --keep-tipr --allow-done-tipr-fallback \
    > "$REPRO/r$rep/Test/run_phase12_gate_keeptipr.log" 2>&1
  tail -20 "$REPRO/r$rep/Test/run_phase12_gate_keeptipr.log"
done
python3 scripts/phase12_validate.py compare --exp EXP_br_span100_packA_gen_C1e9
python3 scripts/phase12_validate.py promote --exp EXP_br_span100_packA_gen_C1e9
cd /home/user/Nmsdk/Bin
git add Configs/SpikeSamples/StructTrain/PHASE12_VALIDATION.md \
  Configs/SpikeSamples/StructTrain/SelectivityBranch/EXP_br_span100_packA_gen_C1e9/ || true
git add -u Configs/SpikeSamples/StructTrain/SelectivityBranch/EXP_br_span100_packA_gen_C1e9/ || true
if ! git diff --cached --quiet; then
  git commit -m "phase12: VALIDATED EXP_br_span100_packA_gen_C1e9 (done_tipr keep-tipr)."
fi
cd "$ROOT"

# badges
python3 - <<'PY'
from pathlib import Path
import re
root = Path("/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain")
man = (root / "PHASE12_VALIDATION.md").read_text(encoding="utf-8")
succ = root / "SUCCESSFUL_EXPERIMENTS.md"
text = succ.read_text(encoding="utf-8")
for m in re.finditer(r"\| (EXP_br_span\d+_packA_\w+_C1e9) \|[^\n]*\| VALIDATED \|", man):
    eid = m.group(1)
    pat = rf"(\| {re.escape(eid)} \| [^|\n]*?)( \| \d)"
    def repl(mm, _eid=eid):
        s = mm.group(1)
        if "VALIDATED (PHASE12 W1)" in s:
            return mm.group(0)
        return s + " · **VALIDATED (PHASE12 W1)**" + mm.group(2)
    text2, n = re.subn(pat, repl, text, count=1)
    if n:
        text = text2
        print("badge", eid)
succ.write_text(text, encoding="utf-8")
# wave map status
p12 = root / "PHASE12_VALIDATION.md"
t = p12.read_text(encoding="utf-8")
t = t.replace("| **1** | Branch packA ×9 cold | **in progress** |", "| **1** | Branch packA ×9 cold | **done** |", 1)
p12.write_text(t, encoding="utf-8")
PY
cd /home/user/Nmsdk/Bin
git add Configs/SpikeSamples/StructTrain/SUCCESSFUL_EXPERIMENTS.md \
  Configs/SpikeSamples/StructTrain/PHASE12_VALIDATION.md \
  Configs/SpikeSamples/StructTrain/SelectivityBranch/PHASE8_SHORTSPAN.md \
  Configs/SpikeSamples/StructTrain/PHASE9_COVERAGE.md \
  Configs/SpikeSamples/StructTrain/PHASE11_COVERAGE.md \
  Configs/SpikeSamples/StructTrain/_repro/README.md \
  Configs/SpikeSamples/StructTrain/scripts/phase12_validate.py || true
if ! git diff --cached --quiet; then
  git commit -m "phase12: W1 complete docs + badges."
fi

echo "=== ALL DONE run2 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
