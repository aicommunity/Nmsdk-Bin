# Cold Train investigation (soft vs strip)

## Goal

Stable from-scratch cold → TipR@Rmin + mid with `ok_audit=1`, `acc≥8`, r1≡r2
(`REPRO_OK_QUALITY`). Exact fires/L vs gold optional (`REPRO_OK_EXACT`).

Do **not** overwrite gold PASS dirs.

## Audit freeze

| Item | Value |
|------|-------|
| PulseLib pin | `780ffc7` (same as gold Branch 13.09 / FastSpan 15.09) |
| Gold FS | `SelectivityFastSpan/EXP_span25ms_fast_C1e9` L=`6 5 4 1` fires=`10000000` |
| Gold Branch | `SelectivityBranch/EXP_br_span25_packA_gen_C1e9` L=`13 11 7 1` fires=`10000000` |
| Prior strip harness | `_repro` r1≡r2 but `REPRO_FAIL` (FS L=7 FA; Branch 1 FA, Need=1) |

### Soft-cold vs strip-cold

| | soft (historical) | strip (prior harness) |
|--|-------------------|------------------------|
| Model | fat cable kept; links → tip `_1` | delete `Dendrite*_k` k>1 |
| TipR / L / Rmin | cold `8.6e7×4`, L=`1 1 1 1`, Rmin=`2e7` | same |
| AutoCalibrate | **0** | was 1; now **0** for A/B |
| Stop | **Need=0** | was SIGTERM on L≠cold |

PulseLib L-policy commits already in gold binary: `281c98a`, `6f12f04`, `35984a2`.

## Definitions

- `soft-cold` — `soft_cold_reset_train` (setup_fastspan / PHASE8 seed style)
- `strip-cold` — `strip_cold_reset_train`
- `REPRO_OK_QUALITY` — r1≡r2 ∧ ok_audit=1 ∧ acc≥8
- `REPRO_OK_EXACT` — QUALITY ∧ L==gold ∧ fires==gold

## A/B matrix

| ID | Family | cold | path |
|----|--------|------|------|
| A1 | FastSpan25 | soft | `_repro/_invest/A1_fs_soft_r1` |
| A2 | FastSpan25 | strip | `_repro/_invest/A2_fs_strip_r1` |
| B1 | Branch25 | soft | `_repro/_invest/B1_br_soft_r1` |
| B2 | Branch25 | strip | `_repro/_invest/B2_br_strip_r1` |

See [`COMPARE.md`](COMPARE.md) for live rows.

## CLI

```bash
ROOT=Bin/Configs/SpikeSamples/StructTrain
python3 "$ROOT/scripts/repro_cold_harness.py" invest --job A1
python3 "$ROOT/scripts/repro_cold_harness.py" prepare --all --cold soft
python3 "$ROOT/scripts/repro_cold_harness.py" run --all --cold soft
python3 "$ROOT/scripts/repro_cold_harness.py" compare
```

## Checkpoints (Bin commits)

C0 audit+API → C1 Need0/gate → C2.A1…B2 → C3 diagnose? → C4 soft canon.

## Root cause

_(filled after A/B)_
