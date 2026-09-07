# Pilot / scale status (2026-09-05)

## Pack A Done (preserved)

| EXP | L | FixedLTZ | Source |
|-----|---|----------|--------|
| span25 gen/preinh | `6 5 4 1` | ≈0.087 / ≈0.052 | git restore after accidental cold reset |
| span50 gen/preinh | `11 9 7 1` / `11 9 6 1` | 0.100 / ≈0.068 | git restore |

## In progress (`scale_remaining.log`, MAX_JOBS=6)

Retrain after disk prune + accidental full-grid cold reset:

- Pack A span100 (floor → amp; L already `21 17 11 1`)
- Pack B/C span25 / span50 / span100

## Tooling

- `l_reference.json`: span100 `[20,17,10,1]`; Pack B/C via `pack_a_alias`
- `reset_asymrm_cold.sh` refuses empty `PILOT_EXPS` (safety)
- Disk: StatisticLogs pruned (~320 GB freed); see `SCALE_DEFERRED.md`

## Commands

```bash
# monitor
tail -f scale_remaining.log
python3 ../SelectivityLtzCalibrate/scripts/verify_train_done.py \
  --require-calibrated --require-sync-ok --L-reference l_reference.json \
  EXP_*/Train/Parameters_00.xml
```

Test selectivity (`fire_all`) remains out of scope for train Done.
