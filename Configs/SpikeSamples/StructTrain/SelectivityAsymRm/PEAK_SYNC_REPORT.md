# PEAK_SYNC_REPORT — SelectivityAsymRm

## EXP_span100ms_packA_preinh

- **verdict:** `PEAK_SHAPE_SUSPECT`
- **IsNeedToTrain:** 1
- **all_non_ref_sync_ok:** False
- **GTS:** 20000
- **L:** actual=`9 17 12 1` formula_cold=`21 18 11 1` formula_post=`20 17 11 1` sync_peak=`20 17 11 1`
- **EstDelay:** cold=0.005 post=0.00520833125

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 9 | 21 | 20 | False | 0.0612 | invalid | PEAK_SHAPE_SUSPECT |
| 1 | 17 | 18 | 17 | True | 0.0013 | invalid | PEAK_SHAPE_SUSPECT |
| 2 | 12 | 11 | 11 | True | 0.00155 | invalid | PEAK_SHAPE_SUSPECT |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## EXP_span25ms_packA_gen

- **verdict:** `PEAK_SHAPE_SUSPECT`
- **IsNeedToTrain:** 1
- **all_non_ref_sync_ok:** False
- **GTS:** 20000
- **L:** actual=`6 5 3 1` formula_cold=`6 5 3 1` formula_post=`6 5 3 1` sync_peak=`6 5 3 1`
- **EstDelay:** cold=0.005 post=0.0052083325

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 6 | 6 | 6 | True | 0.0002 | invalid | PEAK_SHAPE_SUSPECT |
| 1 | 5 | 5 | 5 | True | 0.001033 | invalid | PEAK_SHAPE_SUSPECT |
| 2 | 3 | 3 | 3 | False | 0.0027 | invalid | PEAK_SHAPE_SUSPECT |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## EXP_span25ms_packA_preinh

- **verdict:** `PEAK_SHAPE_SUSPECT`
- **IsNeedToTrain:** 1
- **all_non_ref_sync_ok:** False
- **GTS:** 20000
- **L:** actual=`6 5 4 1` formula_cold=`6 5 3 1` formula_post=`6 5 3 1` sync_peak=`6 5 3 1`
- **EstDelay:** cold=0.005 post=0.005

| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |
|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|
| 0 | 6 | 6 | 6 | True | 0.00075 | invalid | PEAK_SHAPE_SUSPECT |
| 1 | 5 | 5 | 5 | False | 0.002033 | invalid | PEAK_SHAPE_SUSPECT |
| 2 | 4 | 3 | 3 | True | 0.00025 | invalid | PEAK_SHAPE_SUSPECT |
| 3 | 1 | 1 | 1 | False | 1.501 | invalid | SYNC_OK |

## Summary

| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |
|-----|---------|-------------|----------|------------------|
| EXP_span100ms_packA_preinh | PEAK_SHAPE_SUSPECT | False | 9 17 12 1 | 21 18 11 1 |
| EXP_span25ms_packA_gen | PEAK_SHAPE_SUSPECT | False | 6 5 3 1 | 6 5 3 1 |
| EXP_span25ms_packA_preinh | PEAK_SHAPE_SUSPECT | False | 6 5 4 1 | 6 5 3 1 |
