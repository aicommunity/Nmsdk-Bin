# SelectivityLtzCalibrate — журнал

## 2026-08-23

- Создана кампания `SelectivityLtzCalibrate/` по плану глубокого анализа.
- `ANALYSIS_structural_learning.md` — полный текст плана §1–§14.
- RegressionFull480: setup + run (EXP_baseline_gen, EXP_baseline_preinh25).
- FastSpanLtzCal: setup 6 EXP (span 25/50/100 × gen/preinh).
- BranchFastSpan: setup 2 EXP (span 25/100, TimeNeuronTimeLearnerBranch + D002C25e11).
- C++: `MatchMode` в `NPatternResponseAnalyzer`; `PatternRecognition()` в classic/Branch learner.

## 2026-08-23 (debt fix)

- **Sync pipeline:** `merge_train_model.py` + in-place `inject_analyzer.py` — test Model не перезаписывается train Model.
- **Cold train:** `patch_ltz_calibrate_train.py` (UseFixedLTZ=0, gap_fraction 0.85); regression setup — fresh `TimeNeuronTimeLearner/Model_00.xml` + `ResetToUntrainedState=1`.
- **Smoke sync:** `smoke_sync_regression.sh` — golden EXP00 5/8, EXP04 6/8 после sync.
- **Branch sync parity:** `copy_config_branch.sh` + `inject_analyzer_branch.py` in-place.
- **Data hygiene:** `.gitignore` для runtime; источник весов — `Train/Parameters_00.xml`.

## 2026-08-23 — уточнение gate §14 (cold baseline не нужен)

**Решение:** cold retrain RegressionFull480 (Bio `NSPNeuronGen` / full480, `L=1`, batch `-t 160`) **не является gate** и **не обязан** воспроизводить golden `L=49`, acc 5/8–6/8. С новыми параметрами синапса/дендрита (D002, fast span) baseline на full480 **может не сходиться** — это ожидаемо, не долг.

**Gate вместо §14 cold train:**

| Проверка | Зачем | Статус |
|----------|-------|--------|
| `smoke_sync_regression.sh` | sync Train→Test не ломает golden checkpoint | ✅ |
| `run_regression_warm.sh` | golden Parameters → sync → test (5/8, 6/8) | ✅ |

**Снято с долгов:**

- cold batch train stall `L≈97` на RegressionFull480;
- «доказать, что AutoCalibrate на Bio full480 воспроизводит golden» через cold retrain;
- блокировка Tier 0 / C++ diff из‑за несходимости cold baseline.

## 2026-08-23 — sprint close (protocol lock + grid)

### Pilot span100 gen

| TRAIN_T | L | FixedLTZ | Done |
|---------|---|----------|------|
| 160 | 23 19 13 1 | 0.0115 | FAIL |
| 320 | 23 19 12 1 | 0.0115 | FAIL |
| 480 | 23 19 12 1 | 0.0115 | FAIL |

### FastSpanLtzCal grid (classic)

6/6 fire_all, FixedLTZ=0.0115 — train not Done. P1-soft закрыт документированием + A1 sweep.

### BranchFastSpan

- span100: Done, FixedLTZ=0.10, test 1/8 fire_all
- span25: Done, FixedLTZ=0.029, test **4/8** partial

### Tier 0b

Classic C++ port **skipped** — train не Done. Branch path достигает Done+CalibrateLtz.

### Обновлённые долги

| ID | Статус |
|----|--------|
| P0 sync + warm gate | ✅ |
| verify_train_done + setup | ✅ |
| Tier 0 classic acc | 🔴 → backlog B1 (offline dual-thr / FP diagnostics; MatchMode=1 = ISI oracle, не gate) |
| Classic train Done | 🔴 → исследование stall / GUI |
| Branch readout | 🟡 span25 4/8 |
| A1 sweep | ✅ |

## 2026-08-28 — AsymRmLtzCal protocol repair (выполнен)

- Parity setup + `reset_asymrm_ltzcal_cold.sh` + TRAIN_T 80→160→320 continue на 6 EXP.
- **1/6 Done:** `EXP_span25ms_packA_gen` — FixedLTZ=0.0885, test **6/8 gate PASS** (selective, не fire_all).
- 5/6 stall (span100/50 + span25 preinh); §4 two-phase fallback — без эффекта.
- Детали: `AsymRmLtzCal/JOURNAL.md`, `PROTOCOL_REPAIR.md`.

## 2026-08-27 — AsymRmLtzCal + Branch fallback

- `AsymRmLtzCal/`: classic TimeLearner, Pack A, GTS=10000, AutoCalibrate — **6/6 train stall** (L↑, FixedLTZ=0.0115). См. `AsymRmLtzCal/REPORT.md`.
- `AsymRmLtzCalBranch/`: Branch + Pack A — **6/6 stall** (GTS 10000/2000, TRAIN_T 160/480). Контроль BranchFastSpan D002 span25: Done, FixedLTZ≈0.029.
- Offline sweep AsymRm baseline: span100 preinh acc **5/8** при thr≈0.0205 (target_hit=1, fp=3) — подтверждает gap при калибровке thr.

- Classic D002 train stall (EndOfLearning / sync margins на fast span).
- B1 offline dual-thr / FP diagnostics (`MatchMode=1` не operational gate); B3 двухпорог LTZ; C1–C4; Tier D.
- A1 automation: apply best thr from sweep to test patch.
- RegressionFull480 cold — optional research only.
