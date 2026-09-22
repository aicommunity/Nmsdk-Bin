# Пост-тюнинг в модуле-учителе (PostTune)

[English](POST_TRAIN_TUNING.md) · [Аудит текущей реализации](AUDIT_2026-09-22.md) · [Историческая карта рецептов](RELIABILITY_MAP.ru.md)

Сверено с PulseLib 9a6cee0b / Bin 2d1d0214 и объединённой рабочей документацией; пересмотр 2026-09-23. Учитель выполняет tip-resistance + silent-mid FixedLTZ. `EnablePostTrainTuning=true` по умолчанию; старые XML без свойства наследуют PostTune.

## Фазы

| Значение | NNeuronTimeLearner | NNeuronTimeLearnerBranch |
|----------|-------------------|-------------------------|
| 0 | Joint sync + normalize | Joint sync + normalize, обратный порядок |
| 1 | Не назначается | Не назначается |
| 2 | Done | Done |
| 3 | PostTune | Legacy CalibrateLtz при PostTune OFF |
| 4 | — | PostTune |

При включённом PostTune Branch пропускает обычный переход через legacy CalibrateLtz. SearchSynthetic вызывает ScaleTipR для snapshot отката. Done допускает best-effort завершение, а не только точное совпадение пиков и амплитуд.

## Свойства и режимы

| Свойство | Default | Смысл |
|----------|---------|-------|
| EnablePostTrainTuning | true | Включение этапа |
| PostTrainTipResistanceMode | 1 | 0 Off; 1 CanonRmin; 2 FlatLastR; 3 KeepDone; 4 SearchSynthetic |
| EnablePostTrainMidThreshold | true | Калибровка порога |
| PostTrainMidMetric | 0 Auto | TL: LTZ; Branch: shared soma (SomaNeuronAmplitude row0 / CSV soma_amp_sum); режимы 1/2 требуют учёта ограничений ниже |
| TipResistanceCanonFloor / TipResistanceCanonLast | 2e7 / 8.6e7 | Сопротивления канона |
| PostTrainSilentThreshold | 1.0 | Порог silent-зондов |
| PostTrainSyntheticFoilCount | 8 | Максимум синтетических foils |
| PostTrainTipSearchIters | 12 | Число проходов поиска |
| PostTrainTuneComplete | false | Служебный признак завершения, не pass избирательности |
| AutoScaleIterationGap | true | gap=span+settle+slack; dataset delay=settle+slack |

[Формулы тайминга](docs/TIMING_AND_GAP.ru.md). При AutoScale=1 XML IterationGap не является нижним пределом.

Off сохраняет TipR; CanonRmin задаёт floor для первых N−1 tips и last для последнего, синхронизирует Exc; FlatLastR задаёт last всем tips; KeepDone использует состояние после joint train. Search начинает с канона, изменяет TipR, принимает BestTips только при LandscapeOk и улучшении gap, иначе возвращает snapshot.

## Mid и ограничения корректности

В Train плохой landscape может оставить FixedLTZ=1.0. В inference при FixedLTZ>=0.9 `MaybeStartInferenceMidProbes` играет текущую Test Matrix с выключенным Analyzer, вычисляет mid, записывает flag, сбрасывает dataset/analyzer и повторяет ту же Matrix.

Первые N строк Matrix считаются target; MatrixClasses не определяет выбор target. Калибровка на той же Test Matrix является принятой особенностью текущего алгоритма (A07), а не ошибкой. Полученная оценка описывает качество на калибровочном наборе; независимая оценка обобщения потребовала бы отдельного исследования. Перестановка sample 0 меняет калибруемую цель по этому контракту.

Формула mid: 0.5*(target+max_foil_below), иначе target*0.99. Helper по-прежнему исключает foils выше target. В **Branch 9a6cee0b** плохой finite landscape оставляет silent-порог и в Train, и в inference. В обычном **TimeLearner** guard остаётся только для Train. Проверки NaN/полноты метрик отсутствуют у обоих; Branch при target=0.5 и foil=NaN всё ещё сохраняет mid=0.495.

После выбора BestTips в Branch Search добавлен отдельный free-run. Если он отклоняет BestTips, возвращается KeepDone/ScaleTipR snapshot с search_reverted=1. При включённом расчёте mid Train Search оставляет silent-порог даже при хорошем landscape; PostTuneInferenceMidDone=true запрещает второй inference-mid в оставшемся окне этого процесса. Для Test-калибровки нужен новый процесс/reset.

Это частичное исправление A08–A09: нормальный Branch-путь больше не рассчитывает mid по последнему постороннему кандидату. Однако:
- сбой SetupPostTuneFreeRunProbes всё ещё приводит к Finalize на нулевых метриках и PostTrainTuneComplete=true;
- после free-run reject метрики в flag относятся к отклонённым BestTips, а tipr уже содержит snapshot; повторного измерения snapshot в Train нет;
- плохой inference-landscape оставляет silent-порог, но Complete/InferenceMidDone=true; это завершение процедуры, не успешная калибровка;
- обычный TimeLearner не получил повторный замер выбранных Tips;
- Branch mode=1 (LTZ) всё ещё игнорируется в free-run, а iteration-путь использует max(LTZ,soma). Коммит daf9c23 уточнил комментарии об Auto/Soma, не исправил выбор LTZ.

[Доказательства и обновлённый план](AUDIT_2026-09-22.md).

## Проверки и воспроизводимость

[План проверки](POST_TRAIN_VERIFY.ru.md) описывает желаемые критерии. Текущий `posttune_verify.py` не обеспечивает все эти критерии автоматически: expect_fires/expect_tipr не превращены в обязательный failure, а неуспех дочернего gate не исключает чтение старых результатов.

[Сохранённый результат](_repro/POSTTUNE_VERIFY_RESULT.md) содержит новый срез 16:47:46Z с одной строкой br100_search; старые br25_on/asym25 skip_train сохранены отдельно как срез 11:33:05Z. Он не подтверждает cold retrain всех вариантов или полный план V3–V6.

`--skip-tipr-mid` отключает внешний Python-рецепт в phase8/phase9; при silent-пороге возможны два запуска Test: mid, затем gate. `post_train_hygiene` пропускает tiprmin для уже canon/flat; force-python-hygiene меняет процедуру и должен фиксироваться в provenance.

`EnablePostTrainTuning=0` возвращает legacy ветку, но побайтовой эквивалентности старому pin не гарантирует: AutoScaleIterationGap и другие defaults изменились. Для регрессии фиксировать исходники, бинарник, XML, начальное состояние и все overrides.


## Тайминг и аварийный откат

AutoScaleIterationGap=0 возвращает max(configured, physical); изменение kMinSettle — отдельное изменение модели. Замеры 85/90 секунд wall соответствуют отношению примерно 1.06, а 6× относится только к gap 1.5/0.25. Они не доказывают шестикратное ускорение всей программы. [Исходные числа и ограничения](docs/TIMING_AND_GAP.ru.md).
