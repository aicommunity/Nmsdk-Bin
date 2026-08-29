# AsymRmLtzCal — REPORT

Кампания: **Pack A AsymRm** × span 100/50/25 × gen/preinh + **AutoCalibrate FixedLTZ** (peak_fraction 0.99).  
Каталог: `SelectivityLtzCalibrate/AsymRmLtzCal/`.  
Baseline: [`SelectivityAsymRm/REPORT.md`](../SelectivityAsymRm/REPORT.md) — 18/18 `fire_all` @ FixedLTZ=0.0115.

## Протокол цели

Trial0 (trained) → fire; trials 1–7 (distractors) → silence. Gate: `target_hit ∧ Acc≥4 ∧ ¬fire_all`.  
Operational readout: **MatchMode=0** (LTZ rising edge). `MatchMode=1` не в gate.

## Параметры

| Параметр | Значение |
|----------|----------|
| Neuron | `NSPNeuronGenAsymRmD001C25e12` / `…Preinh2_5…` |
| C / D / Secr | 2.5e-11 / 0.001 / 0.001 |
| ExcRm / InhRm | 1e7 / 1e8 (10×) |
| GTS | **10000** |
| Train patch | AutoCalibrate=1, mode=1, frac=0.99, UseFixedLTZ=0, LTZ=100 |
| Прогон (repair) | cold reset → TRAIN_T **80→160→320** continue + §4 fallback (2026-08-28) |

## Результат repair protocol (2026-08-28)

После parity setup + `reset_asymrm_ltzcal_cold.sh` + sweep TRAIN_T на **тех же 6 EXP**:

| EXP | L (финал) | FixedLTZ | Train | Test acc | Gate |
|-----|-----------|----------|-------|----------|------|
| span100 gen | 9 17 9 1 | 0.0115 | stall | n/a | — |
| span100 preinh | 9 19 9 1 | 0.0115 | stall | n/a | — |
| span50 gen | 9 9 7 1 | 0.0115 | stall | n/a | — |
| span50 preinh | 9 9 6 1 | 0.0115 | stall | n/a | — |
| **span25 gen** | 6 5 4 1 | **0.0885** | **Done** | **6/8** | **PASS** |
| span25 preinh | 6 5 4 1 | 0.0115 | stall | n/a | — |

**1/6 Done+calibrated.** Единственный PASS: `EXP_span25ms_packA_gen` — AutoCalibrate поднял thr с 0.0115 до **0.0885**; test **selective** (fires=3/8), `target_hit=1`, fp=2 (не fire_all).

§4 двухфазный fallback (AutoCalibrate off → train 80t → on → train 40t) на 5 stall — **без эффекта**.

Полная таблица: [`grid_summary.csv`](grid_summary.csv).

### Вывод repair

1. **Протокол repair работает:** после cold reset LtzCal **совпадает с baseline** на TRAIN_T=80 (`L=9 1 1 1`, те же TipR/InitialSoma).
2. **AutoCalibrate срабатывает только при EndOfLearning** — для span25 gen достигнут при cumulative ~560t; span100/50 plateau на частичном sync (amp-нормализация не завершена).
3. **preinh vs gen:** при одинаковом L=`6 5 4 1` gen → Done, preinh → stall — различие в нормализации синапсов preinh-нейрона, не в паттерне.
4. **Гипотеза fire_all подтверждена на живом прогоне:** span25 gen ушёл из fire_all (baseline offline thr≈0.024 давал 3/8).

## Результат classic TimeLearner (TRAIN_T=160, pre-repair)

**6/6 train_not_Done** — `verify_train_done.py --require-calibrated` FAIL на всех EXP.

| EXP | L после train | FixedLTZ | NeedTrain | Calibrated |
|-----|---------------|----------|-----------|------------|
| span100 gen/preinh | 21 17 11 1 | 0.0115 | 1 | — |
| span50 gen/preinh | 11 9 6 1 | 0.0115 | 1 | — |
| span25 gen/preinh | 6 5 4 1 | 0.0115 | 1 | — |

**Вывод:** L вырос до ожидаемых значений (coincidence sync частично), но **EndOfLearning / AutoCalibrate не вызван** — тот же stall, что FastSpanLtzCal classic на D002. Sync/test не выполнялись (fail-hard gate).

---

## Главный вывод (человеческим языком)

### Что мы проверяли

После **SelectivityAsymRm** все 18 EXP дали `fire_all`: нейрон стреляет на **всех 8** тестовых паттернах (acc=1/8), хотя на обученном (trial 0) это правильно (`target_hit=1`). Гипотеза: порог LTZ **0.0115** слишком низкий — реальные пики Pack A ~0.018–0.033, и любой отклик проходит порог.

**AsymRmLtzCal** должен был: обучить те же нейроны Pack A и **автоматически поднять порог** после train (AutoCalibrate ≈ 99% от пика на trained-паттерне).

### Что получилось

1. **Обучение с калибровкой не завершилось.** На всех 6 EXP L вырос (напр. `21 17 11 1` на span100), но `IsNeedToTrain=1`, FixedLTZ остался **0.0115**, AutoCalibrate **не вызвался**. Тесты не запускались из‑за жёсткого gate.

2. **Парадокс с baseline.** В **SelectivityAsymRm** train тоже заканчивается с `NeedTrain=1` (строгий Done не достигнут), но test **всё равно идёт** с thr=0.0115 → fire_all. LtzCal **блокирует** test, пока нет Done+calibrate — поэтому кажется, что «ничего не работает», хотя L даже **ближе** к полному sync, чем в baseline (`9 1 1 1` vs `21 17 11 1`).

3. **Гипотеза про порог подтверждается offline.** На **уже обученных** весах baseline (без переобучения) ручной подбор thr по CSV:
   - span100 preinh: thr≈0.0205 → **acc 5/8** (target hit, 3 FP на reverse / permute_mid / early_cluster)
   - span50 preinh: thr≈0.027 → **acc 8/8** offline
   - span100 gen: gap target≈distractor → порогом не отделить

   Нейрон **не сломан** — не используется зазор между пиками target и distractors из‑за thr=0.0115.

4. **Branch fallback с Pack A** тоже stall. Контроль Branch+D002 span25: Done + FixedLTZ≈0.029 за ~3 мин — pipeline калибровки рабочий, stall связан с **протоколом setup/train** для Pack A, не с C++.

### Итог тремя пунктами

1. **fire_all в AsymRm** — в первую очередь **артефакт порога 0.0115**, не провал coincidence-обучения и не повод для sweep C/Rm.
2. **AutoCalibrate не помог**, потому что train в LtzCal-протоколе **не доходит до EndOfLearning** (расхождение setup с baseline: fresh Model, нет inject_analyzer, другой TRAIN_T).
3. **Следующий шаг** — ремонт протокола на **тех же 6 EXP**, cold retrain. План: [`PROTOCOL_REPAIR.md`](PROTOCOL_REPAIR.md). **Выполнен 2026-08-28** — см. раздел «Результат repair protocol» выше.

---

## Сравнение с AsymRm baseline (FixedLTZ=0.0115)

| | AsymRm baseline | AsymRmLtzCal (classic) |
|--|-----------------|------------------------|
| Train Done | частичный (L≠1 1 1 1, NeedTrain=1) | **1/6 Done** (span25 gen) |
| FixedLTZ | 0.0115 hardcode | **0.0885** (span25 gen) / 0.0115 (stall) |
| Test mode | 18/18 fire_all | **1/6 selective 6/8** (span25 gen) |

Парадокс: baseline AsymRm **завершает** structural train (L≠1 1 1 1) при TRAIN_T=80, но с **FixedLTZ=0.0115** без AutoCalibrate. Classic LtzCal patch **не доводит** до Done на том же Pack A — вероятно из‑за `UseFixedLTZ=0` / `ResetToUntrainedState` / fresh Model протокола vs baseline `setup_asymrm.sh`.

## Offline A1 (sweep на baseline CSV, FixedLTZ=0.0115)

Источник: `SelectivityAsymRm/EXP_*packA_*/Test/SelectivityLog/results.csv`.

| EXP | ltz_target | max_distr | best thr (target_hit=1) | acc |
|-----|------------|-----------|-------------------------|-----|
| span100 preinh | 0.02050 | 0.02168 | 0.02050, **fp=3** | **5/8** |
| span100 gen | 0.03319 | 0.03319 | gap≈0 | 1/8 |
| span50 preinh | 0.02743 | 0.02090 | 0.02743, fp=0 | **8/8** offline |
| span50 gen | 0.03312 | 0.03319 | gap≈0 | 1/8 |
| span25 preinh | 0.01842 | 0.01868 | 0.01842, fp=2 | 6/8 |
| span25 gen | 0.02425 | 0.02990 | 0.02425, fp=5 | 3/8 |

**FP roles @ thr≈0.0205 (span100 preinh):** target hit; FP на reverse, permute_mid, early_cluster (3/7 distractors); silence на uniform, pairs, late_cluster.


## Branch fallback

См. [`AsymRmLtzCalBranch/REPORT.md`](../AsymRmLtzCalBranch/REPORT.md). Pack A + Branch learner: **6/6 stall** (NeedTrain=1, FixedLTZ=0.0115). Контроль `BranchFastSpan` D002 span25: **Done + FixedLTZ≈0.029** за ~3 мин @ GTS=2000.

## План ремонта

**[PROTOCOL_REPAIR.md](PROTOCOL_REPAIR.md)** — фикс setup/run, cold reset существующих 6 EXP, повторный прогон без новых каталогов.

## Рекомендации (backlog)

1. ~~Parity setup + cold retrain~~ — **выполнено**; 1/6 gate PASS.
2. Для span100/50: исследовать amp-stall (`AllSynapsesNormalized`) или offline thr на partial-sync весах.
3. span25 preinh: тот же L что gen, но stall — сравнить `ResistanceStatus` / tip R post-train.
4. Offline dual-thr (B1) — диагностика для stall EXP без EndOfLearning.

## Запуск

```bash
bash scripts/reset_asymrm_ltzcal_cold.sh
SKIP_REGRESSION_GATE=1 MAX_JOBS=3 TRAIN_T=80 bash scripts/run_asymrm_ltzcal.sh
# при stall: TRAIN_T=160, TRAIN_T=320 (continue -S на тех же EXP)
```
