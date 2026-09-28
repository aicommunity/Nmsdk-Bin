# Аудит динамики структурных классификаторов

Все прогоны выполнены консолью Release `Bin/Platform/Win/NeuroModelerConsole.exe`; исходные конфиги не менялись. Окна 1–16 модельных секунд соответствуют коротким синтетическим probes; длинный Trainer replay выполнялся до 120 модельных секунд. В отдельных приложениях известна ошибка создания файла журнала после записи выходов: её код завершения не заменяет проверку XML и CSV.

## NNeuronTrainer и число спайков

- [`NNeuronTrainer_NSPNeuron_ClassifierTemplate_Synthetic_20260927`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_Synthetic_20260927/README.md) — Trainer режима 6 с точным сохранённым subtree `NSPNeuron` из синтетического `NSpikeClassifier`.
- Link-pruning-контроли на той же длине ветвей и физических параметрах: [`1`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_OneSynapseControl_20260927/README.md), [`4`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_FourSynapseControl_20260927/README.md), [`8`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_EightSynapseControl_20260927/README.md), [`12`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_TwelveSynapseControl_20260927/README.md), [`16`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_SixteenSynapseControl_20260927/README.md) и [`24`](NNeuronTrainer_NSPNeuron_ClassifierTemplate_TwentyFourSynapseControl_20260927/README.md) активных синапса на каждой из первых четырёх ветвей.
- Каждый проект записывает LTZone в `TrainerSpikeProbe/ltz.csv`; README клона указывает запуск и ограничение контроля. Отдельный `FreshBuild`-конфиг и одиночный ответ `NSPNeuronGen` лежат рядом под префиксом `NNeuronTrainer_*`.

### Свежая сборка стандартного шаблона `NSPNeuron`

- [`NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_20260927`](NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_20260927/README.md) обучает свежую трёхвходовую структуру на синтетическом TTFS-паттерне. После 80 модельных секунд `IsNeedToTrain=0`, но трасса LTZone не содержит фронтов.
- [`SourceTrace`](NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_SourceTrace_20260928/README.md) повторяет завершённую структуру и записывает источники, синапсы, сому и LTZone. Входные импульсы и выходы терминальных синапсов присутствуют; `Soma1.SumPotential` достигает `0.002554`, однако стандартный шаблон использует `NPLTZone` и при штатном пороге импульс не выдаёт.
- Диагностические пороговые копии: [`0.0025`](NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_Threshold0025_20260928/README.md) молчит (`LTZone.OutputPotential` достигает `0.002078`); [`0.0020`](NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_Threshold0020_20260928/README.md) даёт ровно один фронт LTZone на период входа `0.6667` с. Это изолированные проверки выходного детектора, не предлагаемые параметры модели.
- Точный сохранённый subtree классификатора (`NSPNeuron` + `NPulseLTZoneThreshold`) отличается от этого шаблона: после Trainer mode 6 он выдаёт четыре фронта за ответ. В том же обученном subtree контрольное отключение связей даёт один фронт при 12 активных синапсах на входную ветвь, но другие проверенные количества дают либо ноль, либо серию импульсов. Результат указывает на совместное влияние структуры/числа синапсов и варианта LTZone; универсального ограничения он не задаёт.
- Дополнительная серия на нескольких временных разносах и на том же точном типе нейрона проверила фактическую структуру и входные связи обоих алгоритмов. Результаты обучения и диапазон порогов, при котором остаётся один спайк, описаны в [аудите `NNeuronTrainer`/`NNeuronLearner` 2026-09-28](../ClassifierDynamicsAudit_20260928/README.md).

## Синтетические выходы `NSpikeClassifier` с латеральным торможением и без него

В первых клонах выходной трассы `DataFromFile=0`, хотя рядом был `input_data.txt`: запуск повторял один сохранённый паттерн, а старый `output_data.txt` был от прежнего прогона. Исправленные клоны [`On`](NSpikeClassifier_Synthetic_OutputsOn_20260927/README.md) и [`Off`](NSpikeClassifier_Synthetic_OutputsOff_20260927/README.md) используют `DataFromFile=1` и 8.01 модельной секунды, чтобы записать все четыре строки ответа. Рекордер снимает три LTZone по проверенным путям источников.

| Строка входа | Ожидаемый класс | `output_data.txt` On / Off | LTZone-фронты `[класс 1, 2, 3]` On | Off |
|---|---:|---:|---:|---:|
| Чистый прототип 1 | 1 | `110` / `110` | `[4,1,0]` | `[4,1,0]` |
| Чистый прототип 2 | 2 | `111` / `111` | `[1,4,1]` | `[1,4,1]` |
| Чистый прототип 3 | 3 | `111` / `111` | `[1,3,2]` | `[1,4,2]` |
| Midpoint 1–2 | неоднозначность допустима | `110` / `110` | `[1,3,0]` | `[3,3,0]` |

Все три чистых пробы остаются многобитовыми. Латеральное торможение уменьшило число лишних импульсов только для третьего прототипа (класс 2: четыре до трёх) и midpoint (класс 1: три до одного); двоичные ответы классов не изменились.

## Классификаторы и латеральное торможение

- [`NSpikeClassifier_Class1SingleSignalProbe_20260927`](NSpikeClassifier_Class1SingleSignalProbe_20260927/README.md) — прежняя широкая трасса с неподтверждённым порядком каналов; кроме того, сохранённый `DataFromFile=0` повторял один паттерн. Не использовать её для подсчёта трёх синтетических проб; точные per-class измерения находятся в исправленной паре `NSpikeClassifier_Synthetic_OutputsOn/Off_20260927` ниже.
- В `DetailedSignals_20260927` лежат парные `NClassifier_Single_Class{1,2}{On,Off}` и отдельные прямые probes потенциала сомы и тормозного канала.
- [`NClassifier_Direct_TargetInhInputCopy_20260927`](DetailedSignals_20260927/NClassifier_Direct_TargetInhInputCopy_20260927/README.md) и [`Off`](DetailedSignals_20260927/NClassifier_Direct_TargetInhInputCopyOff_20260927/README.md) записывают `InhSynapse1.OutInCopy`, прямую копию входа синапса. Включённая схема даёт фронты на 0.173, 0.2105 и 0.3065 с амплитудой 1; Off-контроль остаётся нулевым.
- [`NClassifier_Direct_TargetInhSynapseOutput_20260927`](DetailedSignals_20260927/NClassifier_Direct_TargetInhSynapseOutput_20260927/README.md) и [`Off`](DetailedSignals_20260927/NClassifier_Direct_TargetInhSynapseOutputOff_20260927/README.md) записывают сам выход синапса. On-пики около `8.72e-9` совпадают по времени с импульсами входа, Off равен нулю.

## Скрипты и интерпретация

`analyze_classifier_dynamics.py` и `analyze_detailed_dynamics.py` читают alias из первой части названия столбца и фактический источник из суффикса `[Model....Property]`. Скрипт отказывается строить сводку по многоканальной трассе без source-path заголовков. Трассы, записанные до этой версии заголовка, пригодны для анализа только если в них один сигнал или имеется отдельная однозначная проверка соединений.

Подробные выводы: [аудит `NNeuronTrainer` и `NNeuronLearner`](../../../../../../Libraries/Nmsdk-PulseLib/Docs/Analysis/NNeuronStructuralTrainingAudit.md) и [аудит классификаторов](../../../../../../Libraries/Nmsdk-PulseLib/Docs/Analysis/StructuralClassifiersAudit.md).
