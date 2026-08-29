# План ремонта протокола обучения AsymRmLtzCal

Цель: добиться **Done + AutoCalibrate** на **существующих** 6 EXP в `AsymRmLtzCal/` (новые каталоги не создаём). После фикса — **cold retrain** с L=1 1 1 1.

---

## 1. Диагноз (почему baseline «работает», а LtzCal — нет)

| | SelectivityAsymRm (baseline) | AsymRmLtzCal (сломанный прогон) |
|--|------------------------------|----------------------------------|
| Train L (span100 preinh) | `9 1 1 1` (частичный sync) | `21 17 11 1` (ближе к полному) |
| `IsNeedToTrain` после train | **1** | **1** |
| `AutoCalibrate` | 0 | 1 |
| `FixedLTZ` после train | 0.0115 | 0.0115 (calibrate не вызван) |
| Test | **запускается** | **не запускался** (fail-hard gate) |
| Результат test | fire_all | n/a |

**Важно:** baseline **тоже не проходит** строгий `verify_train_done` (`NeedTrain=0`). Он просто **не проверяет** Done и идёт в test с legacy thr=0.0115.

LtzCal добавил `verify_train_done --require-calibrated` → при том же stall test блокируется. **AutoCalibrate в C++ вызывается только в `EndOfLearning()` при Done** — пока `NeedTrain=1`, порог не пересчитывается.

**Гипотеза stall LtzCal:** расхождение setup с baseline, а не «Pack A не обучается»:

| Отличие setup | baseline `setup_asymrm.sh` | LtzCal `setup_asymrm_ltzcal.sh` |
|---------------|---------------------------|--------------------------------|
| Model | `copy_config` rsync | **`USE_FRESH_MODEL=1`** — перезапись шаблоном |
| `inject_analyzer` на setup | **да** (Train+Test Model) | **нет** |
| `TrainingPhase` | не трогается | принудительно **0** |
| LTZ patch | нет (`AutoCalibrate=0`) | `patch_ltz_calibrate_train.py` |
| `TRAIN_T` run | **80** | **160** |

Offline sweep baseline доказывает: при **правильном thr** (не 0.0115) acc до 5/8–8/8 на тех же весах — **нейрон и обучение не мёртвые**, не срабатывает только автокалибровка.

---

## 2. Стратегия ремонта

**Принцип:** cold_patch Train = **как baseline AsymRm** + **только** теги AutoCalibrate (`patch_ltz_calibrate_train.py`). Всё остальное — parity.

**Не делаем:** новые EXP, новые кампании, C++ diff, MatchMode=1.

---

## 3. Шаги ремонта (скрипты)

### Шаг A — `setup_asymrm_ltzcal.sh`

1. **`USE_FRESH_MODEL=0`** по умолчанию (Model из `copy_config`, как baseline).
2. Убрать принудительный **`TrainingPhase=0`** из cold_patch (в baseline его нет).
3. Убрать дублирующий LTZ patch на **`Model_00.xml`** — только `Parameters_00.xml`.
4. Добавить **`inject_analyzer.py`** Train→Test Model на setup (как baseline).
5. Вынести общий **`cold_patch_pack_a`** → максимально скопировать `cold_patch` из `setup_asymrm.sh` (без лишних полей, которых нет в baseline cold).
6. После cold_patch — **только** `patch_ltz_calibrate_train.py` (+ `--preinh`).

### Шаг B — `reset_asymrm_ltzcal_cold.sh` (новый)

In-place сброс **существующих** 6 EXP без пересоздания каталогов:

```
для каждого EXP в AsymRmLtzCal/grid_cells.tsv:
  1. copy_config train → перезаписать Train из шаблона TimeNeuronTimeLearner
  2. cold_patch Pack A (как baseline)
  3. patch_ltz_calibrate_train.py
  4. patch_pattern_scale.py --span-ms (идемпотентно)
  5. Test: только обновить pattern span + neuron tags (не трогать будущие synced веса)
  6. inject_analyzer на Test Model
  7. удалить runtime: History.xml, StatisticLog/, SelectivityLog/, run_console.log
```

Опция `RESET_TEST=1` — также сбросить Test к cold (L=1 1 1 1) перед sync.

### Шаг C — `run_asymrm_ltzcal.sh`

1. **`TRAIN_T=80`** по умолчанию (как baseline AsymRm).
2. Sweep при stall: `TRAIN_T=160`, затем `320` — **на тех же EXP**, без новых конфигов.
3. Gate оставить strict (`verify_train_done --require-calibrated`).
4. При PASS: sync (`merge_train_weights` + `patch_ltz_calibrate_test.py`) + test.

### Шаг D — диагностика, если после A–C всё ещё stall

Сравнить post-train Parameters baseline vs LtzCal для одного EXP (span100 preinh):

- `TipSynapseResistance`, `InitialSomaPotential`
- `TrainingPhase`, `StructureBuildMode` в learner block
- `LastSyncedMaxLTZ` / `Calibrated*` (если есть)

Если L baseline (`9 1 1 1`) достигает test, а LtzCal (`21 17 11 1`) — нет Done: возможно **пере-sync мешает amp-нормализации** → попробовать **двухфазный** протокол (см. §4).

---

## 4. Fallback (только если шаги A–C не дали Done)

**Фаза 1 — baseline-parity train без AutoCalibrate:**

- Временно `AutoCalibrate=0` на Train.
- Cold + `TRAIN_T=80` → получить тот же L, что baseline.

**Фаза 2 — включить AutoCalibrate и продолжить:**

- `patch_ltz_calibrate_train.py` на уже обученные Parameters.
- `TRAIN_T=20..40` continue `-S` с `ResetToUntrainedState=0`, `StructureBuildMode=1`.
- Цель: довести до `EndOfLearning` + calibrate на тех же весах.

Выполняется **в тех же EXP**, через флаги run-скрипта (`PHASE2_LTZCAL=1`), без новых каталогов.

---

## 5. Повтор экспериментов (cold, существующие конфиги)

После merge фиксов A–C:

```bash
cd Bin/Configs/SpikeSamples/StructTrain/SelectivityLtzCalibrate

# 1. In-place cold reset существующих 6 EXP (без новых папок)
bash scripts/reset_asymrm_ltzcal_cold.sh

# 2. Прогон
SKIP_REGRESSION_GATE=1 MAX_JOBS=3 TRAIN_T=80 TEST_T=20 \
  bash scripts/run_asymrm_ltzcal.sh

# 3. При stall — увеличить время на тех же EXP
TRAIN_T=160 bash scripts/run_asymrm_ltzcal.sh   # только train wave, SKIP sync если нужно — см. run flags
TRAIN_T=320 bash scripts/run_asymrm_ltzcal.sh
```

**Критерий успеха:**

- 6/6: `verify_train_done.py --require-calibrated` PASS
- `FixedLTZ ≠ 0.0115`, `CalibratedFixedLTZ > 0`
- Test: уйти из fire_all хотя бы на span100 preinh (ориентир offline **5/8**)

**Критерий провала → §4 fallback**, затем обновить `JOURNAL.md`.

---

## 6. Branch (`AsymRmLtzCalBranch`)

Отдельный трек. После classic PASS — те же правки parity в `setup_asymrm_ltzcal_branch.sh` + `reset_*` + cold retrain. Pack A + Branch на GTS=10000 не давал Done; приоритет — **classic parity с baseline**.

---

## 7. Чеклист

- [x] A: `setup_asymrm_ltzcal.sh` parity с baseline
- [x] B: `reset_asymrm_ltzcal_cold.sh`
- [x] C: `run_asymrm_ltzcal.sh` TRAIN_T=80 default
- [x] Cold retrain 6 EXP (TRAIN_T=80→160→320; 1/6 Done; §4 fallback — fail)
- [x] REPORT/JOURNAL обновить финальными результатами
- [x] §4 двухфазный протокол на 5 stall EXP — без эффекта
