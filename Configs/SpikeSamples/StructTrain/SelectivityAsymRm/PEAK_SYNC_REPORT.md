# PEAK_SYNC_REPORT — SelectivityAsymRm

## EXP_span50ms_packA_gen

- **verdict:** `PEAK_PREFERS_L_ACTUAL`
- **IsNeedToTrain:** 0
- **all_non_ref_sync_ok:** True
- **GTS:** 20000
- **L:** actual=`25 23 15 1` formula_cold=`11 9 6 1` formula_post=`27 23 14 1` sync_peak=`27 23 14 1`
- **EstDelay:** cold=0.005 post=0.001893940909090909

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 25 | 11 | 27 | True | 0.002 | invalid | FORMULA_OFF |
| 1 | 23 | 9 | 23 | True | 0.0004 | invalid | FORMULA_OFF |
| 2 | 15 | 6 | 14 | True | 0.0001 | invalid | FORMULA_OFF |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## Summary

| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |
|-----|---------|-------------|----------|------------------|
| EXP_span50ms_packA_gen | PEAK_PREFERS_L_ACTUAL | True | 25 23 15 1 | 11 9 6 1 |
