# SelectivityAsymRm — test gate on 16 Done EXP (2026-09-08)

First systematic 8-trial selectivity after train Done. Stuck Pack C gen (50/100) excluded.

## Command

```bash
python3 scripts/done_fingerprint.py --write done_fingerprint_pre_selectivity16.json
MAX_JOBS=3 TEST_T=20 SKIP_TRAIN=1 ALLOW_PARTIAL_TRAIN=1 \
  PILOT_EXPS='<16 Done>' bash scripts/run_asymrm.sh
python3 scripts/done_fingerprint.py --diff done_fingerprint_pre_selectivity16.json
```

`ALLOW_PARTIAL_TRAIN=1` needed because some Done EXP lack `LastAbsDt` in StatisticLog (`verify_train_done --require-sync-ok` false-fails); Need=0 + calibrated FixedLTZ unchanged. Fingerprint: **16 Done OK**.

## Gate

`target_hit ∧ ¬fire_all ∧ Acc≥4/8` (`evaluate_selectivity_csv.py`).

## Results (`grid_summary.csv`)

| EXP | Acc | mode | gate | target_hit | FixedLTZ | L |
|-----|-----|------|------|------------|----------|---|
| span25 packA gen | **6/8** | selective (eval) / partial_FA (summary) | **1** | 1 | 0.087 | 6 5 4 1 |
| span25 packA preinh | 1/8 | fire_all | 0 | 1 | 0.052 | 6 5 4 1 |
| span25 packB gen | 1/8 | fire_all | 0 | 1 | 0.100 | 6 5 4 1 |
| span25 packB preinh | 1/8 | fire_all | 0 | 1 | 0.058 | 6 5 4 1 |
| span25 packC gen | 1/8 | fire_all | 0 | 1 | 0.086 | 6 5 4 1 |
| span25 packC preinh | 1/8 | fire_all | 0 | 1 | 0.037 | 6 5 4 1 |
| span50 packA gen | 1/8 | fire_all | 0 | 1 | 0.100 | 11 9 7 1 |
| span50 packA preinh | 1/8 | fire_all | 0 | 1 | 0.068 | 11 9 6 1 |
| span50 packB gen | 1/8 | fire_all | 0 | 1 | 0.090 | 11 9 7 1 |
| span50 packB preinh | 7/8 | **silent** | 0 | 0 | 0.057 | 11 9 6 1 |
| span50 packC preinh | 1/8 | fire_all | 0 | 1 | 0.035 | 11 9 6 1 |
| span100 packA gen | 1/8 | fire_all | 0 | 1 | 0.100 | 21 17 11 1 |
| span100 packA preinh | 1/8 | fire_all | 0 | 1 | 0.054 | 21 17 11 1 |
| span100 packB gen | 1/8 | fire_all | 0 | 1 | 0.100 | 20 17 10 1 |
| span100 packB preinh | 1/8 | fire_all | 0 | 1 | 0.077 | 20 17 10 1 |
| span100 packC preinh | 1/8 | fire_all | 0 | 1 | 0.100 | 20 17 10 1 |

**Summary:** gate PASS **1/16** (`EXP_span25ms_packA_gen`, target fires, Acc 6/8, fa=2).  
Most others: fire_all despite calibrated FixedLTZ. One silent (span50 packB preinh). Valid negatives — no manual FixedLTZ tweak in this wave.

Eval line for PASS:

```text
EXP_span25ms_packA_gen ok=1 n=8 acc=6 target_hit=1 fire_all=0 mode=selective fires=10001100 matches=11110011 fa=2
```

## Pack C gen (stuck) — tip-reset amp FAIL

After H1 tip reset + short amp: both still Need=1 / cold FixedLTZ; no test gate. Details: `PACKC_GEN_DIAGNOSIS.md`, `finish_packC_gen_tip_reset_amp_stall.json`.

## Dspan pilot (копии pack A gen, 2026-09-08/09)

Оригиналы `EXP_span{50,100}ms_packA_gen` не трогались. Fingerprint 16 Done: **OK**.

| EXP | D | Train | Test gate | Acc | mode | target_hit |
|-----|---|-------|-----------|-----|------|------------|
| `EXP_span50ms_packA_gen_Dspan` | 0.002 | **Need=1** (amp pathology, abort) | — | — | — | — |
| `EXP_span100ms_packA_gen_Dspan` | 0.004 | **Done** FixedLTZ≈0.091 L=`20 17 10 1` | **FAIL** | 1/8 | fire_all | 1 |

Eval:

```text
EXP_span100ms_packA_gen_Dspan ok=0 n=8 acc=1 target_hit=1 fire_all=1 mode=fire_all fires=11111111 matches=10000000 fa=7
```

**Вывод:** D∝span на 100 мс даёт cold→Done, но селективность как у baseline packA gen 100 (`fire_all`). На 50 мс cold+D=0.002 ушёл в патологический `amp_dt` (~1e25…1e72) — Done не достигнут. Рычаг D∝span **не** закрывает fire_all на длинном span.
