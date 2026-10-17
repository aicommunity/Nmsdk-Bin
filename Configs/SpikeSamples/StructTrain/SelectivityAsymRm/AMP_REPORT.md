# AMP_REPORT — SelectivityAsymRm pilot vs LtzCal Done

Дата: 2026-08-30. Источник: `analyze_train_stall.py`, `analyze_peak_sync.py`, StatisticLog latest.

## Executive summary

| EXP | L | NeedTrain | Primary blocker | all_sync_ok | L_formula | Verdict peak-sync |
|-----|---|-----------|-----------------|-------------|-----------|-------------------|
| span25 gen (pilot) | 6 5 4 1 | 1 | LENGTH_STALL | **no** | 6 5 3 1 | PEAK_SHAPE_SUSPECT |
| span25 preinh (pilot) | 6 5 4 1 | 1 | LENGTH_STALL | **no** | 6 5 3 1 | PEAK_SHAPE_SUSPECT |
| span100 preinh (pilot) | 9 17 12 1 | 1 | LENGTH_STALL | **no** | 9 8 5 1* | PEAK_SHAPE_SUSPECT |
| **span25 gen (LtzCal Done)** | 6 5 4 1 | **0** | — | **yes** | 6 5 3 1 | **PEAK_PREFERS_L_ACTUAL** |

\* span100 `L_formula_post` (20 17 11) — артефакт post-estimate; не использовать как цель.

**Ключевой вывод:** L=`6 5 4 1` — рабочая cable-цель (LtzCal Done при `all_sync_ok=yes`). Formula `L_target=6 5 3 1` off-by-one на dend2 — **не ошибка обучения**. Pilot stall: dend1 `last_abs_dt > SyncTolerance` + dend2 AMP@Rmin (gen) / RMAX (preinh).

## Per-dendrite: pilot span25 gen vs LtzCal Done

| dend | metric | Pilot | LtzCal Done |
|:----:|--------|-------|-------------|
| 0 | sync_ok | yes | yes |
| 0 | TipR | 7.29e8 | 4.67e7 |
| 0 | blocker | AMP_OSCILLATION | AMP_OSCILLATION |
| 1 | last_abs_dt | **1.78e-3** | **2.0e-4** |
| 1 | sync_ok | **no** | **yes** |
| 1 | blocker | **LENGTH_STALL** | AMP_OSCILLATION |
| 2 | TipR | **1e6 (Rmin)** | **8.37e8** |
| 2 | sync_ok | yes | yes |
| 2 | blocker | **AMP_AT_RMIN** | AMP_OSCILLATION |
| 2 | L vs formula | 4 vs 3 | 4 vs 3 |

## Per-dendrite: span25 preinh

| dend | sync_ok | TipR | blocker |
|:----:|:-------:|:----:|:-------:|
| 0 | yes | 2.06e10 | AMP_OSCILLATION |
| 1 | **no** | 6.29e7 | LENGTH_STALL |
| 2 | yes | **1e11 (Rmax)** | AMP_OSCILLATION |

## Decision tree (интервенции)

```
PEAK_PREFERS_L_ACTUAL (LtzCal) → gate Done = sync_ok, не L_formula
Pilot dend1 LENGTH_STALL → length-phase continue (LENGTH_STEPS +1280)
Pilot dend2 AMP@Rmin при partial sync → amp-continue только после all sync_ok
preinh dend2 @ RMAX → sweep ResistanceAdjustGain (не Rmin path)
span100 → length-only budget до amp phase
```

## Протокол (реализовано в run_asymrm.sh)

1. **Phase length:** `LENGTH_STEPS=80 160 320 640 1280`
2. **Phase amp:** при `all_dendrites_sync_ok` → `patch_continue_train` + `AMP_TRAIN_STEPS=320 640 1280`
3. **Verify:** `--require-calibrated --require-sync-ok --peak-sync peak_sync_report.json`
4. **GTS default:** 20000

## Setup parity (span25 gen)

| Параметр | Pilot AsymRm | LtzCal Done |
|----------|--------------|-------------|
| GTS | 20000 | 10000 |
| AutoCalibrate | 1 | 1 |
| SyncTolerance | 0.001042 | 0.001042 |
| PeakMeasureMargin | 0.002 | 0.002 |
| cold_patch | asymrm_ltzcal_common | same family |

A/B тест GTS=10000 на span25 gen — опционально при fail пилота @ GTS=20000.

## C++ fallback (фаза E)

**Статус: не требуется** на текущем этапе. LtzCal Done доказывает достижимость `EndOfLearning` без C++ diff. Pilot fail — протокольный (partial sync + premature amp), не INFEASIBLE cable.

## Следующие шаги

1. Cold retrain 3 pilot EXP с новым 3-phase протоколом
2. При fail span25 gen → `sweep_asymrm_amp.sh` (baseline + gain/margin)
3. Gate масштабирования: ≥2/3 pilot Done
