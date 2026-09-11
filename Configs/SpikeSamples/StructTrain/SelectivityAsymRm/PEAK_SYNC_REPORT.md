# PEAK_SYNC_REPORT — SelectivityAsymRm

## EXP_span25ms_packA_gen

- **verdict:** `PEAK_PREFERS_L_ACTUAL`
- **IsNeedToTrain:** 0
- **all_non_ref_sync_ok:** True
- **GTS:** 20000
- **L:** actual=`7 6 4 1` formula_cold=`6 5 3 1` formula_post=`7 6 4 1` sync_peak=`7 6 4 1`
- **EstDelay:** cold=0.005 post=0.004166666666666667

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 7 | 6 | 7 | True | 0.001 | invalid | FORMULA_OFF |
| 1 | 6 | 5 | 6 | True | 0.0002 | invalid | FORMULA_OFF |
| 2 | 4 | 3 | 4 | True | 0.0005 | invalid | FORMULA_OFF |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## Summary

| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |
|-----|---------|-------------|----------|------------------|
| EXP_span25ms_packA_gen | PEAK_PREFERS_L_ACTUAL | True | 7 6 4 1 | 6 5 3 1 |
