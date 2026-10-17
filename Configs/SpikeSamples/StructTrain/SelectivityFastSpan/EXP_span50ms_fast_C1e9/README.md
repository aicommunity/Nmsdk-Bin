# EXP_span50ms_fast_C1e9

PHASE10.2 from `EXP_span50ms_fast` → `NSPNeuronGenAsymRmD001C1e9` + cold Train + TipR@Rmin + silent mid.

| Field | Value |
|-------|-------|
| Neuron | `NSPNeuronGenAsymRmD001C1e9` |
| TipR | `20000000 20000000 20000000 86000000` |
| ResistanceMin | `20000000` |
| GTS | `20000` |
| FixedLTZThreshold | `0.0236098` |
| Gate | acc5 partial_FA fires=`11110000` |

Parent `EXP_span50ms_fast` not overwritten.

## PHASE11 R2.3

1. Thr re-mid only: still acc5 partial_FA (gap tiny, target not separable).
2. Cold retrain (`TipR 8.6e7×4`, L=`1 1 1 1`, `-t 320 -S`) → L=`11 10 7 1`, TipR@Rmin; silent ltz showed **amp inversion** (target not max) → gate acc2 `ok_audit=0`.
3. Restored PHASE10 Train/Test XML+CSV (keep better `ok_audit=1` partial). Cold attempt archived as StatisticLog pack `archives/statisticlog_20260915T103702Z/`. Sibling `EXP_span50ms_fast_preinh_C1e9` remains 8/8.
