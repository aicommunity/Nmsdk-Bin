# Пост-тюнинг в модуле-учителе (PostTune)

**English:** [`POST_TRAIN_TUNING.md`](POST_TRAIN_TUNING.md)  
**Связано:** [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) §4.7 · [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md) · [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md)

После синхронизации длин и нормализации амплитуд учитель может сам выполнить рецепт **tip-resistance + silent mid FixedLTZ**, без обязательного Python `apply_tiprmin` / silent probe.

**По умолчанию этап включён** (`EnablePostTrainTuning=true` в `ADefault`). Старые XML без свойства при cold retrain получают PostTune.

## Фазы

| | `NNeuronTimeLearner` | `NNeuronTimeLearnerBranch` |
|--|--|--|
| 0 | Sync | Sync |
| 1 | Normalize | Normalize |
| 2 | Done | Done |
| 3 | **PostTune** | CalibrateLtz (legacy, только если tuning **OFF**) |
| 4 | — | **PostTune** |

Порядок: Sync → Normalize → (PostTune **или** legacy CalibrateLtz) → Done.

При `EnablePostTrainTuning=1` Branch **не** вызывает `ScaleTipResistancesForParallelActivation` и **не** входит в `kPhaseCalibrateLtz`.

## Свойства (оба класса)

| Свойство | Default | Смысл |
|----------|---------|--------|
| `EnablePostTrainTuning` | `true` | Мастер-флаг |
| `PostTrainTipResistanceMode` | `1` (CanonRmin) | 0 Off · 1 CanonRmin · 2 FlatLastR · 3 KeepDone · 4 SearchSynthetic |
| `EnablePostTrainMidThreshold` | `true` | Silent-mid FixedLTZ |
| `PostTrainMidMetric` | `0` Auto | TL→LTZ peak; Branch→soma peak |
| `TipResistanceCanonFloor` | `2e7` | Пол / первые tips CanonRmin |
| `TipResistanceCanonLast` | `8.6e7` | Последний tip / FlatLastR |
| `PostTrainSilentThreshold` | `1.0` | Порог на время зондов |
| `PostTrainSyntheticFoilCount` | `8` | Макс. чужих паттернов |
| `PostTrainTipSearchIters` | `12` | Лимит для mode=4 |
| `PostTrainTuneComplete` | `false` | Служебно: PostTune закончен |

## Режимы tip-resistance

| Mode | Действие |
|------|----------|
| 0 Off | TipR не трогать; mid по текущему |
| 1 CanonRmin | `[floor]×(N−1)+[last]`; `ResistanceMin≥floor`; Exc sync |
| 2 FlatLastR | `[last]×N` (AsymRm span25) |
| 3 KeepDone | snapshot с конца Normalize |
| 4 SearchSynthetic | старт CanonRmin; coordinate descent; gap≤0 → KeepDone |

Сводка mode→span: [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) §4.7.

## Алгоритм синтетики

Вход: ISI-вектор цели длины N (`NumInputDendrite`), значения ≥0.

1. Добавить **цель** без изменений.
2. Кандидаты чужих (детерминированный порядок): циклический сдвиг k=1..N−1; swap соседних; все ISI ×0.5 и ×2.0; для каждого i: ISI[i]=0.
3. Отбросить: сумма ISI==0; полное совпадение с целью; дубликаты.
4. Обрезать до `PostTrainSyntheticFoilCount`.
5. Прогон: один burst на паттерн при `PostTrainSilentThreshold`, все tips unmuted, длины зафиксированы.

**Mid:** `0.5*(tgt + max_foil_below)` иначе `tgt*0.99`; gap = tgt − foil_ref.

Код: `Libraries/Nmsdk-PulseLib/Core/NNeuronPostTrainTune.{h,cpp}`.

## Скрипты

- `scripts/repro_cold_lib.py` → `post_train_hygiene`: при PostTune ON и TipR уже канон/flat — **skip** Python tiprmin (`--force-python-hygiene` в harness для отладки).
- `SelectivityBranch/scripts/phase8_tiprmin_gate.py` → `--skip-tipr-mid`: overlay/links/gate без TipR@Rmin и silent mid.

## Регресс

Клон с явным `EnablePostTrainTuning=0` сохраняет прежний путь Branch CalibrateLtz (байт-в-байт относительно pin до PostTune).  
Примеры: `SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune_off`.
