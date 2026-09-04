# Span100 dend0 protocol (pilot v4 Done Unblock)

## Problem

`EXP_span100ms_packA_preinh` stalls at `L=[9, 17, 12, 1]` vs formula target `~[20, 17, 11, 1]`.
dend0 gap is ~14× SyncTolerance; blind `+5120` length steps waste ~50h wall.

## Protocol (in-place, no cold reset)

1. **Do not** cold-reset — keep current `9 17 12 1`.
2. Seed `InitialSomaPotential` from LtzCal (`scripts/seed_initial_from_ltzcal.py`) before amp.
3. Length schedule: `LENGTH_STEPS_SPAN100="80 160 320 640 1280 2560"` (default in `run_pilot_span100.sh`).
4. `LENGTH_MAX_STEP=2560` — never auto-run 5120.
5. `length_step_guard.py` aborts when plateau + hopeless UNDER.
6. Optional warm-start: raise dend0 toward LtzCal partial `9 17 9 1` / formula, but prefer continuing growth under guard.
7. After length settles (or abort), amp with `SEED_INITIAL=1`.
8. **Not a gate blocker** for span25 Pack A Done.

## Commands

```bash
export SKIP_COLD_RESET=1 SEED_INITIAL=1
bash scripts/run_pilot_span100.sh
# or continue amp only:
PILOT_EXPS=EXP_span100ms_packA_preinh AMP_ONLY=1 L_REFERENCE=ltzcal \
  SEED_INITIAL=1 bash scripts/run_asymrm.sh
```

## Success / stop

- Success: dend0 approaches target without LENGTH_UNDER plateau; then amp → Done.
- Stop: guard abort on plateau; document in `PILOT_SPAN100_REPORT.md`; leave for separate sweep.
