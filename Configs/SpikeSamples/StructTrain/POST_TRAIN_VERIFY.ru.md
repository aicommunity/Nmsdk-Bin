# Проверка C++ PostTune — план экспериментов

Статус кода/доков/клонов: **готово**.  
Статус cold+gate vs gold: **V1–V3 PASS** (см. [`_repro/POSTTUNE_VERIFY_RESULT.md`](_repro/POSTTUNE_VERIFY_RESULT.md)).

Критерии: TipR vector, FixedLTZ (±5% к gold mid), fires/acc, `IsNeedToTrain=0`. На Train **без** Python `apply_tiprmin`; mid — C++ на Test (inference), не Python silent.

## Матрица

| # | Клон | TipR mode | Ожидание | Статус |
|---|------|-----------|----------|--------|
| V1 | `SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune` | 1 CanonRmin | TipR `2e7×3+8.6e7`; mid≈gold Test `0.0718` (±5%); fires 8/8; Need→0 | **PASS** fires `10000000` mid≈0.07180 |
| V2 | `…/EXP_br_span25_packA_gen_C1e9_posttune_off` | OFF → CalibrateLtz | Need→0; путь ScaleTipR (TipR ≠ канон допустим); gate с Python tiprmin OK | **PASS** fires `10000000` mid≈0.0163 |
| V3 | `SelectivityAsymRm/EXP_span25ms_packA_gen_posttune` | 2 FlatLastR | TipR `8.6e7×4`; mid≈gold `0.03759`; 8/8 | **PASS** mid≈0.037589 fires `10000000` |
| V4 | AsymRm span50 CanonRmin (опц.) | 1 | 8/8 Test; cold mid T2 — не блокер | P2 |
| V5 | Branch100 KeepDone/Search (опц.) | 3/4 | 8/8 | P2 |
| V6 | Phase6 tiprmin CanonRmin (опц.) | 1 | 7/8 | P2 |

## Протокол одного прогона (V1–V3)

1. Пересобрать `NeuroModelerConsole` с pin PostTune (символ `EnablePostTrainTuning`).
2. Soft-cold Train (`repro_cold_lib.soft_cold_reset_train`).
3. Train: `NeuroModelerConsole -c Train/Project.ini -s -t <T> -x -S` до `IsNeedToTrain=0`  
   - Branch25: `-t 320`  
   - AsymRm25: `-t 160` (как FastSpan family floor; при Need=1 — удлинить)
4. Снять с Train **до** Python hygiene: `TipSynapseResistance`, `FixedLTZThreshold`, `ResistanceMin`, `IsNeedToTrain`, `PostTrainTuneComplete`, `TrainingPhase`.
5. Gate:
   - V1/V3: `phase8` / `phase9` с `--skip-tipr-mid` (overlay + C++ inference mid two-pass).
   - V2: обычный tiprmin+mid (legacy) **или** `--force-python-hygiene`.
6. Сравнить с gold Test: TipR, thr (±5%), fires mask, `acc_legacy`, last-pulse.

## Артефакты

- Логи: `<clone>/Train/run_posttune_verify.log`, `Test/run_gate.log`
- Сводка: [`_repro/POSTTUNE_VERIFY_RESULT.md`](_repro/POSTTUNE_VERIFY_RESULT.md)
- Оркестратор: [`scripts/posttune_verify.py`](scripts/posttune_verify.py)

## Вне scope этой проверки

Pack B/C matrix, InitSoma overlay, FastSpan plateau Need, полный PHASE12 wave.
