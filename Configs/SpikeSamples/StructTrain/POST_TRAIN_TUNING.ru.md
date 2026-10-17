# Пост-тюнинг в модуле-учителе (PostTune)

[English](POST_TRAIN_TUNING.md) · [Повторный аудит](../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md) · [Историческая карта рецептов](RELIABILITY_MAP.ru.md)

Сверено с PulseLib d4149190 / Bin 9733281, 2026-09-24. Исправления после исходного аудита существенны, но полного закрытия A08–A10/A16 нет.

## Фазы и свойства

| Значение фазы | NNeuronTimeLearner | NNeuronTimeLearnerBranch |
|---|---|---|
| 0 | Joint sync + normalize | Joint sync + normalize, обратный порядок |
| 1 | Не назначается | Не назначается |
| 2 | Done | Done |
| 3 | PostTune | Legacy CalibrateLtz при PostTune OFF |
| 4 | — | PostTune |

Done допускает best-effort остановку. Need=0 не доказывает выполнение всех sync/amp допусков или избирательность.

| Свойство | Default / смысл |
|---|---|
| EnablePostTrainTuning | true; старые XML без свойства наследуют PostTune |
| PostTrainTipResistanceMode | 1; 0 Off, 1 CanonRmin, 2 FlatLastR, 3 KeepDone, 4 SearchSynthetic |
| EnablePostTrainMidThreshold | true |
| PostTrainMidMetric | 0 Auto: TL LTZ, Branch shared soma; 1 LTZ, 2 Soma |
| TipResistanceCanonFloor / TipResistanceCanonLast | 2e7 / 8.6e7 |
| PostTrainSilentThreshold | 1.0 |
| PostTrainSyntheticFoilCount / PostTrainTipSearchIters | 8 / 12 |
| PostTrainTuneComplete | false; завершение процедуры, не quality PASS |
| PostTuneResult | 0 None, 1 Success, 2 NonSeparable, 3 SetupFailure, 4 Timeout, 5 InvalidMetrics |
| AutoScaleIterationGap | true |

Off не меняет tips; Canon задаёт floor первым N−1 и last последнему; Flat задаёт last всем; Keep использует веса после joint train. Search начинает с канона, ищет допустимый лучший gap и имеет fallback snapshot; Branch перед поиском использует ScaleTipR. BestTips получают новый free-run в обоих учителях. Ошибка setup финального Search free-run имеет отдельный статус; после rejected-best/fallback метрики очищаются/инвалидируются, чтобы не приписывать их snapshot.

## Mid: текущий контракт и ограничения

Inference при silent FixedLTZ>=.9 проигрывает текущую Test Matrix с выключенным Analyzer, калибрует mid, затем сбрасывает dataset/analyzer и оценивает ту же Matrix. Sample 0 считается target независимо от MatrixClasses. Это принятая особенность A07; независимый held-out не требуется этой процедурой.

При допустимом landscape mid располагается между target и максимальным foil. ComputeMidThreshold сохраняет формулу midpoint с max_foil_below (либо .99*target), но gap теперь считается относительно **глобального** максимума foil. Helper проверяет конечность. Finalize обоих учителей оставляет silent на плохом landscape. Branch Search Train с включённым mid сохраняет silent, предполагая отдельную Test-калибровку. TL Search при хорошем landscape может сохранить mid, вычисленный в Train; это не свежая Test-калибровка.

Остаются воспроизводимые ограничения:

- Free-run нули не различают измеренную тишину и непосещённый sample. NaN live-сигнала теряется при сравнении с текущим максимумом. Timeout/partial trace может дать mid=.25 при [.5,0]; TL даже сообщает Success, Branch сообщает Timeout, но применяет mid.
- PostTuneResult не сбрасывается на новом attempt: возможно сочетание старого Success с новым nonseparable/silent результатом. Result/Complete без проверки измерений недостаточны для приёмки.
- Branch explicit LTZ всё ещё загрязняется soma accumulator в ACalculate. TL Soma iteration измеряет сумму в конце итерации, а free-run — максимум суммы во времени.
- Same-Matrix является контрактом; неполное наблюдение Analyzer и старые Test flags являются отдельными ошибками измерения/provenance.

## Тайминг и воспроизводимость

[Тайминг](docs/TIMING_AND_GAP.ru.md): gap=span+settle+slack, dataset delay=settle+slack. AutoScale=1 игнорирует XML floor; AutoScale=0 берёт max(configured,physical). PostTune=0 сам по себе не воспроизводит прежний pin.

[Сводка разработчика](_repro/POSTTUNE_VERIFY_RESULT.md) сообщает 2/7 cold PASS. Полные run-bundles и соответствующий Linux Console отсутствуют в доступной checkout; независимо эта сводка не принята. Текущий verifier уже проверяет gate rc, некоторые SHA/ожидания и собственный snapshot, но сохраняет stale Test mid и допускает некоторые незавершённые Train/Search. [Требования к проверке](POST_TRAIN_VERIFY.ru.md).

soft_cold теперь сбрасывает FixedLTZ=1. Это полезная правка, но не доказательство полной новой инициализации fat Model. Значение Search reverted означает возврат к собственному snapshot; успешный fallback не доказывает улучшение поиска.

Замеры 85/90 секунд wall означают отношение около 1.06; 6× относится к gap 1.5/.25, а не доказанному ускорению всей программы. A12 отложен при достаточно малом шаге.
