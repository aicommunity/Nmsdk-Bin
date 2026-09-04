# Scale deferred / notes (2026-09-04)

## Train Done gate (span25 Pack A)

`run_gate_scale.sh` reports **GATE OK** for:

- `EXP_span25ms_packA_gen` — Done, FixedLTZ≈0.0869
- `EXP_span25ms_packA_preinh` — Done, FixedLTZ≈0.0516

## Why Pack B/C scale did not auto-run earlier

1. `scale_asymrm.sh` previously used a broken `VERIFY` path (`$ROOT/../../SelectivityLtzCalibrate/...`), so Done count was wrongly **0/3**.
2. Default `PILOT_EXPS` included span100 (LENGTH_STALL), which is **not** a span25 gate blocker.
3. Amp sweep inside scale does **cold reset** of pilot — would destroy Done weights. Now `SKIP_SWEEP=1` by default.

## How to scale Pack B/C span25 (manual)

```bash
# Preserve Done pilot; only train remaining Pack A / B / C as needed:
SKIP_SWEEP=1 PILOT_EXPS="EXP_span25ms_packA_gen EXP_span25ms_packA_preinh" \
  bash scripts/scale_asymrm.sh

# Or selective Pack B/C only:
PILOT_EXPS="EXP_span25ms_packB_gen EXP_span25ms_packB_preinh ..." \
  L_REFERENCE=ltzcal SEED_INITIAL=1 ADAPTIVE_TRAIN=1 bash scripts/run_asymrm.sh
```

Test selectivity gate (fire_all / partial_FA) is separate from train Done and may need LTZ / pattern follow-up after scale.
