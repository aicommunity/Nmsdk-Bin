# PEAK_SYNC_REPORT — SelectivityAsymRm

## EXP_span50ms_packA_gen

- **verdict:** `PEAK_PREFERS_L_ACTUAL`
- **IsNeedToTrain:** 0
- **all_non_ref_sync_ok:** True
- **GTS:** 20000
- **L:** actual=`11 9 7 1` formula_cold=`11 9 6 1` formula_post=`11 9 6 1` sync_peak=`11 9 6 1`
- **EstDelay:** cold=0.005 post=0.005000003

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 11 | 11 | 11 | True | 0.00175 | invalid | SYNC_OK |
| 1 | 9 | 9 | 9 | True | 0.0003 | invalid | SYNC_OK |
| 2 | 7 | 6 | 6 | True | 0.00115 | invalid | FORMULA_OFF |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## Summary

| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |
|-----|---------|-------------|----------|------------------|
| EXP_span50ms_packA_gen | PEAK_PREFERS_L_ACTUAL | True | 11 9 7 1 | 11 9 6 1 |
