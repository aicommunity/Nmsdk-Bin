# SYNC_TOL_REPORT — SelectivityAsymRm

## EXP_span25ms_packA_gen

- **overall_class:** `L_FORMULA_OFF`
- **SyncTolerance:** 0.00104167 s
- **EstDelayPerSeg:** 0.0052083325
- **all_non_ref_sync_ok:** False
- **L:** actual=`6 5 3 1` target=`6 5 3 1` ref=`6 5 4 1`

| dend | L | L_tgt | L_ref | needed | delay_len | residual | last_abs_dt | dt/tol | tol_min_L | class |
|:----:|:-:|:-----:|:-----:|:------:|:---------:|:--------:|:-----------:|:------:|:---------:|:-----:|
| 0 | 6 | 6 | 6 | 0.025 | 0.02604 | -0.001042 | 0.0002 | 0.19× | 6 | `SYNC_OK` |
| 1 | 5 | 5 | 5 | 0.02083 | 0.02083 | 0 | 0.001033 | 0.99× | 5 | `SYNC_OK` |
| 2 | 3 | 3 | 4 | 0.0125 | 0.01042 | 0.002083 | 0.0027 | 2.59× | — | `L_FORMULA_OFF` |
| 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1.501 | 1440.96× | — | `SYNC_OK` |

## EXP_span25ms_packA_preinh

- **overall_class:** `MISALIGNED`
- **SyncTolerance:** 0.00104167 s
- **EstDelayPerSeg:** 0.005
- **all_non_ref_sync_ok:** False
- **L:** actual=`6 5 4 1` target=`6 5 3 1` ref=`6 5 4 1`

| dend | L | L_tgt | L_ref | needed | delay_len | residual | last_abs_dt | dt/tol | tol_min_L | class |
|:----:|:-:|:-----:|:-----:|:------:|:---------:|:--------:|:-----------:|:------:|:---------:|:-----:|
| 0 | 6 | 6 | 6 | 0.025 | 0.025 | 0 | 0.00075 | 0.72× | 6 | `SYNC_OK` |
| 1 | 5 | 5 | 5 | 0.02083 | 0.02 | 0.0008333 | 0.002033 | 1.95× | 5 | `MISALIGNED` |
| 2 | 4 | 3 | 4 | 0.0125 | 0.015 | -0.0025 | 0.00025 | 0.24× | — | `SYNC_OK` |
| 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1.501 | 1440.96× | — | `SYNC_OK` |

## EXP_span100ms_packA_preinh

- **overall_class:** `LENGTH_UNDER`
- **SyncTolerance:** 0.00416667 s
- **EstDelayPerSeg:** 0.00520833125
- **all_non_ref_sync_ok:** False
- **L:** actual=`9 17 12 1` target=`20 17 11 1`

| dend | L | L_tgt | L_ref | needed | delay_len | residual | last_abs_dt | dt/tol | tol_min_L | class |
|:----:|:-:|:-----:|:-----:|:------:|:---------:|:--------:|:-----------:|:------:|:---------:|:-----:|
| 0 | 9 | 20 | — | 0.1 | 0.04167 | 0.05833 | 0.0612 | 14.69× | 20 | `LENGTH_UNDER` |
| 1 | 17 | 17 | — | 0.08333 | 0.08333 | 0 | 0.0013 | 0.31× | 17 | `SYNC_OK` |
| 2 | 12 | 11 | — | 0.05 | 0.05729 | -0.007292 | 0.00155 | 0.37× | 10 | `SYNC_OK` |
| 3 | 1 | 1 | — | 0 | 0 | 0 | 1.501 | 360.24× | — | `SYNC_OK` |

## Summary

| EXP | overall_class | all_sync_ok | blocker dend | dt/tol max |
|-----|---------------|-------------|--------------|------------|
| EXP_span25ms_packA_gen | `L_FORMULA_OFF` | False | d2 | 2.59× |
| EXP_span25ms_packA_preinh | `MISALIGNED` | False | d1 | 1.95× |
| EXP_span100ms_packA_preinh | `LENGTH_UNDER` | False | d0 | 14.69× |
