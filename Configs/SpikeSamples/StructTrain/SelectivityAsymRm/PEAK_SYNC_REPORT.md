# PEAK_SYNC_REPORT — SelectivityAsymRm

## EXP_span25ms_packA_preinh

- **verdict:** `PEAK_SHAPE_SUSPECT`
- **IsNeedToTrain:** 1
- **all_non_ref_sync_ok:** True
- **GTS:** 20000
- **L:** actual=`6 5 4 1` formula_cold=`6 5 3 1` formula_post=`6 5 3 1` sync_peak=`6 5 3 1`
- **EstDelay:** cold=0.005 post=0.005

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 6 | 6 | 6 | True | 0.00075 | invalid | PEAK_SHAPE_SUSPECT |
| 1 | 5 | 5 | 5 | True | 5e-05 | invalid | PEAK_SHAPE_SUSPECT |
| 2 | 4 | 3 | 3 | True | 0.0003 | invalid | PEAK_SHAPE_SUSPECT |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## Summary

| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |
|-----|---------|-------------|----------|------------------|
| EXP_span25ms_packA_preinh | PEAK_SHAPE_SUSPECT | True | 6 5 4 1 | 6 5 3 1 |
