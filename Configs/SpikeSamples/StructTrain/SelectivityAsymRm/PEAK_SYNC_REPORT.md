# PEAK_SYNC_REPORT — SelectivityAsymRm

## EXP_span100ms_packA_gen_Dspan

- **verdict:** `PEAK_PREFERS_L_ACTUAL`
- **IsNeedToTrain:** 0
- **all_non_ref_sync_ok:** True
- **GTS:** 20000
- **L:** actual=`20 17 10 1` formula_cold=`21 18 11 1` formula_post=`20 17 11 1` sync_peak=`20 17 11 1`
- **EstDelay:** cold=0.005 post=0.005263157894736842

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 20 | 21 | 20 | True | 0.0002 | invalid | FORMULA_OFF |
| 1 | 17 | 18 | 17 | True | 0.0015 | invalid | FORMULA_OFF |
| 2 | 10 | 11 | 11 | True | 0.0002 | invalid | FORMULA_OFF |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## Summary

| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |
|-----|---------|-------------|----------|------------------|
| EXP_span100ms_packA_gen_Dspan | PEAK_PREFERS_L_ACTUAL | True | 20 17 10 1 | 21 18 11 1 |
