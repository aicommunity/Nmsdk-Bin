# SoftCold canon inventory

Дата: 2026-10-01. Источники: EXPERIMENTS.md + `posttune_verify.py` CASES.

- Уникальных Имён в реестре: **81**
- SoftCold `--case` ids: **49**
- С case (`yes`): **47**
- `not_applicable` (MatrixClone / pack B–C / Branch meta): **34**
- `MISSING`: **0**

| Имя (реестр) | SoftCold `--case` | Есть? | Last SoftCold | Working сейчас |
|--------------|-------------------|-------|---------------|----------------|
| `EXP00_baseline` | `pa00_baseline` | yes | GoldTest PASS | GoldTest |
| `EXP01_ltz_threshold_sweep` | `pa01_ltz_sweep` | yes | GoldTest PASS | GoldTest |
| `EXP01_preinh_050` | `psi01_050` | yes | GoldTest PASS | GoldTest |
| `EXP02_ltzone_average_mode` | `pa02_ltzone_avg` | yes | GoldTest PASS | GoldTest |
| `EXP06_ltzone_integration` | `pa06_ltzone_int` | yes | GoldTest PASS | GoldTest |
| `EXP14_preinh_260` | `psi14_260` | yes | GoldTest PASS | GoldTest |
| `EXP15_preinh_270` | `psi15_270` | yes | GoldTest PASS | GoldTest |
| `EXP21_span100ms_preinh250` | `psi21_100` | yes | GoldTest PASS | GoldTest |
| `EXP31_span200ms_preinh250` | `psi31_200` | yes | GoldTest PASS | GoldTest |
| `EXP32_span300ms_baseline` | `psi32_300` | yes | GoldTest PASS | GoldTest |
| `EXP33_span300ms_preinh250` | `psi33_300` | yes | GoldTest PASS | GoldTest |
| `EXP34_span400ms_baseline` | `psi34_400` | yes | GoldTest PASS | GoldTest |
| `EXP35_span400ms_preinh250` | `psi35_400` | yes | GoldTest PASS | GoldTest |
| `EXP_br480_nextseginh_tiprmin` | `br480_nextseg` | yes | SoftCold FAIL | GoldTest |
| `EXP_br480_preinh250_tiprmin` | `br480_preinh` | yes | SoftCold FAIL | GoldTest |
| `EXP_br480_tiprmin` | `br480_tiprmin` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span100_packA_gen_C1e9` | `br100_keep,br100_search` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span100_packA_nextseginh_C1e9` | `br100_nextseg` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span100_packA_preinh_C1e9` | `br100_preinh` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span100_packB_gen_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span100_packB_nextseginh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span100_packB_preinh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span100_packC_gen_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span100_packC_nextseginh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span100_packC_preinh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_packA_gen_C1e9` | `br25_off,br25_on` | yes | SoftCold+PostTuneOff FAIL | SkipTrainGold |
| `EXP_br_span25_packA_nextseginh_C1e9` | `br25_nextseg` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span25_packA_preinh_C1e9` | `br25_preinh` | yes | SoftCold FAIL (B_need1) | GoldTest |
| `EXP_br_span25_packB_gen_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_packB_nextseginh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_packB_preinh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_packC_gen_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_packC_nextseginh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_packC_preinh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span25_tiprmin` | `not_applicable` | na | GoldTest NOT_RETESTED | none |
| `EXP_br_span50_packA_gen_C1e9` | `br50_gen` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span50_packA_nextseginh_C1e9` | `br50_nextseg` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span50_packA_preinh_C1e9` | `br50_preinh` | yes | SoftCold FAIL | GoldTest |
| `EXP_br_span50_packB_gen_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span50_packB_nextseginh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span50_packB_preinh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span50_packC_gen_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span50_packC_nextseginh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_br_span50_packC_preinh_C1e9` | `not_applicable` | na | GoldTest PASS | MatrixClone |
| `EXP_span100ms_fast_C1e9` | `fs100_gen` | yes | GoldTest PASS | GoldTest |
| `EXP_span100ms_fast_preinh_C1e9` | `fs100_preinh` | yes | GoldTest PASS | GoldTest |
| `EXP_span100ms_packA_gen` | `asym100_gen,ltz100_gen` | yes | SoftCold FAIL (B_need1) | GoldTest |
| `EXP_span100ms_packA_preinh` | `asym100_preinh,ltz100_preinh` | yes | SoftCold FAIL (B_need1) | GoldTest |
| `EXP_span100ms_packB_gen` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span100ms_packB_preinh_C1e9` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span100ms_packC_gen` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span100ms_packC_preinh_C1e9` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span25ms_fast_C1e9` | `fs25_gen` | yes | GoldTest PASS | GoldTest |
| `EXP_span25ms_fast_preinh_C1e9` | `fs25_preinh` | yes | GoldTest PASS | GoldTest |
| `EXP_span25ms_packA_gen` | `asym25,ltz25_gen` | yes | SoftCold FAIL (A_nonseparable) | GoldTest |
| `EXP_span25ms_packA_preinh` | `asym25_preinh,ltz25_preinh` | yes | SoftCold FAIL (A_nonseparable) | GoldTest |
| `EXP_span25ms_packB_gen` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span25ms_packB_preinh_C1e9` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span25ms_packC_gen` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span25ms_packC_preinh_C1e9` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span50ms_fast_preinh_C1e9` | `fs50_preinh` | yes | GoldTest PASS | GoldTest |
| `EXP_span50ms_packA_gen` | `asym50,ltz50_gen` | yes | SoftCold FAIL (B_need1) | GoldTest |
| `EXP_span50ms_packA_preinh` | `asym50_preinh,ltz50_preinh` | yes | SoftCold FAIL (B_need1) | GoldTest |
| `EXP_span50ms_packB_gen` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span50ms_packB_preinh_C1e9` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span50ms_packC_gen` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `EXP_span50ms_packC_preinh_C1e9` | `not_applicable` | na | MatrixClone PASS | MatrixClone |
| `LtzCal/EXP_span100ms_packA_gen` | `asym100_gen,ltz100_gen` | yes | GoldTest PASS | GoldTest |
| `LtzCal/EXP_span100ms_packA_preinh` | `asym100_preinh,ltz100_preinh` | yes | GoldTest PASS | GoldTest |
| `LtzCal/EXP_span25ms_packA_gen` | `asym25,ltz25_gen` | yes | GoldTest PASS | GoldTest |
| `LtzCal/EXP_span25ms_packA_preinh` | `asym25_preinh,ltz25_preinh` | yes | GoldTest PASS | GoldTest |
| `LtzCal/EXP_span50ms_packA_gen` | `asym50,ltz50_gen` | yes | GoldTest PASS | GoldTest |
| `LtzCal/EXP_span50ms_packA_preinh` | `asym50_preinh,ltz50_preinh` | yes | GoldTest PASS | GoldTest |
| `Phase6/EXP_480_gen_thr_only` | `phase6_thr_only` | yes | GoldTest PASS | GoldTest |
| `Phase6/EXP_480_gen_tiprmin` | `phase6_480` | yes | SoftCold FAIL (A_nonseparable) | GoldTest |
| `Phase6/EXP_480_ltzcal_twin_gen` | `phase6_ltzcal_twin` | yes | GoldTest FAIL | none |
| `Phase6/EXP_480_preinh250_tiprmin` | `phase6_preinh250` | yes | GoldTest PASS | GoldTest |
| `TimeNeuronTimeLearner` | `tn_classic` | yes | GoldTest PASS | GoldTest |
| `TimeNeuronTimeLearnerBranch*` | `not_applicable` (SoftCold via `br*`) | na | GoldTest NOT_RETESTED | none |
| `…Branch_NextSegInh` | `not_applicable` | na | GoldTest NOT_RETESTED | none |
| `…Branch_PreInh250` | `not_applicable` | na | GoldTest NOT_RETESTED | none |

## Очередь SoftCold (manifest)

Всего: **49**

```
asym50_preinh
asym25_preinh
br25_on
phase6_thr_only
fs50_preinh
asym50
br25_off
asym25
fs25_gen
br50_gen
pa00_baseline
pa01_ltz_sweep
psi01_050
pa02_ltzone_avg
pa06_ltzone_int
psi14_260
psi15_270
psi21_100
psi31_200
psi32_300
psi33_300
psi34_400
psi35_400
br480_nextseg
br480_preinh
br480_tiprmin
br100_keep
br100_search
br100_nextseg
br100_preinh
br25_nextseg
br25_preinh
br50_nextseg
br50_preinh
fs100_gen
fs100_preinh
asym100_gen
ltz100_gen
asym100_preinh
ltz100_preinh
fs25_preinh
ltz25_gen
ltz25_preinh
ltz50_gen
ltz50_preinh
phase6_ltzcal_twin
phase6_preinh250
tn_classic
phase6_480
```

## Дыры MISSING

_нет_
