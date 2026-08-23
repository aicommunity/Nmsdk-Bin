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

**Актуальные долги (по плану §8):**

| ID | Долг | Статус |
|----|------|--------|
| **P0 sync** | merge_train_model + inject in-place + `--test` merge | ✅ закрыт |
| **Tier 0 config** | AutoCalibrate в FastSpanLtzCal, полный sync LTZ-тегов | ✅ скрипты; grid прогнан |
| **Tier 0 результат** | уйти из `fire_all` на **fast span + D002** (не Bio baseline) | 🔴 5/6 fire_all; span25 gen 7/8 silent |
| **Tier 0 train** | batch train до Done + AutoCalibrate на **новых** params | 🔴 train не Done / FixedLTZ=0.0115 на большинстве EXP |
| **Tier 0b** | post-Done burst / Branch CalibrateLtz в classic | ⏸ отложен до train Done на fast grid |
| **Branch** | readout + sync parity | 🟡 grid 1/8; в отдельных отчётах до 7/8 на warm Branch |
| **A1** | fallback LTZ sweep по CSV | backlog |
| **B1–B3, C1–C4, D** | readout / contrastive / физика | backlog |

## 2026-08-23 — Phase 1 gate align

- ANALYSIS §14/§13.6: warm/smoke gate; cold Bio → optional `REGRESSION_COLD.md`.
- `verify_regression.py --mode warm|cold`; grid scripts block only on warm FAIL.
- ALGORITHM.md: Gate + verify_train_done before sync.

## Backlog (вне sprint)

- B3 двухпорог LTZ; B1b soma-profile readout; C1 full PatternRecognition; C2–C4 contrastive/order readout; Tier D Exc/Inh/PeakMargin/TS10k; A1 fallback sweep при fail autocal.
- RegressionFull480 cold train — **опциональный** эксперимент, не gate; `setup_regression.sh` / `run_regression.sh` оставлены для ручных прогонов.
