## Обзор конфигураций SpikeSamples

### Назначение папки `SpikeSamples`

Папка `Bin/Configs/SpikeSamples` содержит **витрину эталонных конфигураций** для спайковых моделей нейронов и нейронных сетей в NMSDK.
Каждая конфигурация иллюстрирует одну или несколько биологически мотивированных идей, описанных в публикациях по Neuro Modeler ([список работ](https://neuromodeler.ru/index.php?option=com_content&view=article&id=44&Itemid=677&lang=ru)).

Основные тематические блоки:

- **Реакции одиночных нейронов**: зависимость паттернов разрядов от структуры мембраны, размера сомы и параметров модели
  (см. также [`NeuronReactions.md`](NeuronReactions.md)).
- **Модель преобразования импульсных потоков**: спайковая передача, синапсы, ионные механизмы, пресинаптическое торможение
  (см. [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md)).
- **Структуры управления движением и мышечным сокращением**: мотонейроны, клетки Реншоу, афферентные входы, простейшие моторные контуры
  (см. [`MuscleControlStructures.md`](MuscleControlStructures.md)).
- **Кабельные и компартментные нейроны**: многокомпартментные модели, сегментные нейроны, CSNM‑подход с кабельным уравнением
  (см. также [`CSNM-Models.md`](CSNM-Models.md)).
- **Память и обучение**: простейшие ассоциативные и условнорефлекторные схемы, STDP, структурное обучение.
- **Структурная адаптация**: автоматический подбор структуры нейрона (размер сомы, длина дендритов, количество синапсов) для распознавания паттернов
  (см. [`StructuralAdaptation.md`](StructuralAdaptation.md)).
- **Инкрементальное обучение**: обучение на новых образцах без переобучения на всех данных
  (см. [`IncrementalLearning.md`](IncrementalLearning.md)).
- **Классификация**: применение сегментной спайковой модели для задач классификации с временным кодированием
  (см. [`Classification.md`](Classification.md)).

### Краткая карта конфигураций SpikeSamples

Ниже приведены группы конфигураций с указанием основных идей (подробные описания находятся в `README.md` внутри соответствующих папок).

- **Одиночные импульсные нейроны (`SpikeSamples/NM-Neurons/…`)**
  - `NM-PN-01-Neuron-1M1St1In1`, `NM-PN-02-Neuron-1M1St3In3`, `NM-PN-03/04/05/06`
    — исследование влияния структуры сомы и дендритов на форму ответа нейрона.
  - `NM-PN-07/08-LtmNeuron-*`
    — нейроны с длительной мембранной памятью и изменёнными параметрами обратной связи.
  - `NM-PN-NeuronSizeActivity`
    — сопоставление активности нейронов разных размеров (малая/крупная сома).
  - `LIF-Neuron`
    — упрощённая LIF‑версия импульсного нейрона для сравнения с детализированной моделью.

- **Афферентные нейроны (`SpikeSamples/NM-AfferentNeurons/…`)**
  - `NM-AN-00-AfferentModelComparation`, `NM-AN-01-NSAfferentNeuron`, `NM-AN-02-NSimpleAfferentNeuron`
    — преобразование сенсорного (аналогового) сигнала в импульсный поток, частотные характеристики афферентов.

- **Кабельная модель нейрона (`SpikeSamples/NM-Neurons/CableModel/…`)**
  - `CableNeuron`, `CableNeuronClassic`, `CableNeuronMulti*`, `CableNeuronParametersTest`
    — компартментные нейроны с пространственным распространением потенциала, влияние длины/диаметра ионов.
  - Конфигурации `CableNeuronMulti_*_CSNM*`
    — примеры, связанные с компартментной спайковой моделью CSNM и сегментными нейронами.

- **Память и ассоциации (`SpikeSamples/Memory/…`)**
  - `MEM-OneNeuron3`, `MEM-SimpleMemory2`
    — хранение и воспроизведение простых паттернов активности в одиночном нейроне/малой сети.
  - `SpikeAssociationPlus`, `SpikeConditionalReflex`
    — ассоциативная и условнорефлекторная память на спайковых сетях.

- **STDP и структурное обучение (`SpikeSamples/STDP`, `SpikeSamples/StructTrain/…`)**
  - `STDP/STDP-Simple-01`
    — демонстрация правила спайк‑зависимого изменения веса (STDP).
  - `StructTrain/SpikeTrainer`, `StructTrain/SpikeAnsTrainer`, `StructTrain/XOR`
    — структурное обучение (изменение топологии и количества синапсов/каналов) с использованием метода структурной адаптации
    (см. [`StructuralAdaptation.md`](StructuralAdaptation.md)).

- **Нейронные элементы и рецепторы (`SpikeSamples/NeuralElements/…`)**
  - `NeuralElements/NReceptor`
    — модель рецепторного элемента, связывающего сенсорный вход с афферентным нейроном.

- **Управление движением и зрительно‑двигательные контуры (`SpikeSamples/MC1-PCN`, `SpikeSamples/EyeRetina`, `SpikeSamples/MC0-RCN`)**
  - `MC1-PCN/*`
    — позиционное управление (MultiPositionControl, MotionControl) с использованием спайковых сетей и PulseLib.
  - `EyeRetina/EyeRetina`, `EyeRetina/EyeRetinaMuscle`
    — зрительные входы и управление мышцей/двигателем на основе нейроморфного анализа изображения.
  - `MC0-RCN/*`
    — рефлекторные контуры (Ring/Reflex Control Networks) с мотонейронами и реншовскими клетками.

### Связь с валидацией конфигураций

Для всех конфигураций SpikeSamples поддерживается автоматическая валидация через
`Scripts/generate_detailed_validation_report.py --subdir SpikeSamples`.
Итоги собраны в отчёте `Reports/SpikeSamples-Validation-Report.md`:

- большинство конфигураций имеют статус **VALID**;
- небольшое число конфигураций отмечено как **INVALID** или **TIMEOUT** — такие случаи подробно разбираются в общих отчётах по валидации.

В каждом `README.md` для конфигураций SpikeSamples предусмотрен блок **«Статус валидации»**, который синхронно отражает данные из отчёта.

### Как читать документацию SpikeSamples

- Для **каждой конкретной конфигурации** смотрите локальный `README.md` в её папке (структура модели, эксперимент, результаты, ссылки на статьи и rtf‑описания).
- Для **серий экспериментов** и связи с публикациями используйте тематические документы:
  - [`NeuronReactions.md`](NeuronReactions.md) — реакции одиночных нейронов;
  - [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — модель преобразования импульсных потоков;
  - [`MuscleControlStructures.md`](MuscleControlStructures.md) — контуры управления мышечным сокращением.
- Для быстрого обзора всей коллекции и кросс‑ссылок используйте индекс [`Index.md`](Index.md) (см. ниже).

## Обзор конфигураций `SpikeSamples`

### Назначение раздела

Каталог `Bin/Configs/SpikeSamples` содержит **эталонные примеры спайковых конфигураций**, использующих компоненты `Nmsdk-PulseLib` и связанные библиотеки. Эти конфигурации иллюстрируют модели, описанные в работах [список публикаций](https://neuromodeler.ru/index.php?option=com_content&view=article&id=44&Itemid=677&lang=ru) по моделированию спайковых нейронов, преобразованию импульсных потоков и управлению движением мышц.

Этот документ даёт карту основных тематических групп примеров и ссылается на локальные `README.md` в подпапках `SpikeSamples`, а также на тематические обзоры в `Bin/Docs/SpikeSamples/*.md`.

### Тематические группы конфигураций

- **NM-Neurons** — одиночные импульсные нейроны и кабельные модели:
  - `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
  - `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
  - `SpikeSamples/NM-Neurons/NM-PN-03-Neuron-4M4D3St3In`
  - `SpikeSamples/NM-Neurons/NM-PN-04-Neuron-3M1St3In3`
  - `SpikeSamples/NM-Neurons/NM-PN-05-Neuron-4M1D3St3In`
  - `SpikeSamples/NM-Neurons/NM-PN-06-Neuron-1M4D3St3In`
  - `SpikeSamples/NM-Neurons/NM-PN-07-LtmNeuron-1M1St3In3`
  - `SpikeSamples/NM-Neurons/NM-PN-08-LtmNeuron-3M1St3In3`
  - `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`
  - `SpikeSamples/NM-Neurons/LIF-Neuron`
  - `SpikeSamples/NM-Neurons/CableModel/*` — компартментные (кабельные) нейроны, в т.ч. CSNM‑варианты.

- **NM-AfferentNeurons** — афферентные (сенсорные) спайковые нейроны:
  - `SpikeSamples/NM-AfferentNeurons/NM-AN-00-AfferentModelComparation`
  - `SpikeSamples/NM-AfferentNeurons/NM-AN-01-NSAfferentNeuron`
  - `SpikeSamples/NM-AfferentNeurons/NM-AN-02-NSimpleAfferentNeuron`

- **Memory** — спайковая память и ассоциативные структуры:
  - `SpikeSamples/Memory/MEM-OneNeuron3`
  - `SpikeSamples/Memory/MEM-SimpleMemory2`
  - `SpikeSamples/Memory/SpikeAssociationPlus`
  - `SpikeSamples/Memory/SpikeConditionalReflex`

- **StructTrain** — структурное обучение и тренировка:
  - `SpikeSamples/StructTrain/SpikeTrainer` — базовое структурное обучение
  - `SpikeSamples/StructTrain/SpikeAnsTrainer` — структурное обучение с ответами
  - `SpikeSamples/StructTrain/XOR` — применение для задачи XOR
  - См. [`StructuralAdaptation.md`](StructuralAdaptation.md)

- **Classifier** — классификация с использованием спайковых моделей:
  - `SpikeSamples/Classifier/SpikeIrisClassifier` — классификация цветков ириса с инкрементальным обучением
  - См. [`Classification.md`](Classification.md), [`IncrementalLearning.md`](IncrementalLearning.md)

- **MC1-PCN (Motion Control)** — конфигурации для управления движением:
  - `SpikeSamples/MC1-PCN/MotionControl_Test`
  - `SpikeSamples/MC1-PCN/NewPositionControl_Test`
  - `SpikeSamples/MC1-PCN/MultiPositionControl_SimpleTest`
  - `SpikeSamples/MC1-PCN/MultiPositionControl_SoloModeTest`
  - `SpikeSamples/MC1-PCN/MultiPositionControl_TaskTest`
  - `SpikeSamples/MC1-PCN/MultiPositionControl_RememberStateTest`
  - `SpikeSamples/MC1-PCN/MultiPC_TwoLevelsTask`

- **EyeRetina** — зрительные структуры:
  - `SpikeSamples/EyeRetina/EyeRetina`
  - `SpikeSamples/EyeRetina/EyeRetinaMuscle`

- **NeuralElements** — элементарные спайковые элементы:
  - `SpikeSamples/NeuralElements/NReceptor`

- **STDP / Plasticity**:
  - `SpikeSamples/STDP/STDP-Simple-01`

### Статус валидации SpikeSamples

Отдельный отчет по валидации конфигураций `SpikeSamples` формируется скриптом `Scripts/generate_detailed_validation_report.py` и сохраняется в `Reports/SpikeSamples-Validation-Report.md`.

Краткая сводка (из последнего отчета):

- **Источник данных:** `Reports/ConfigValidation-Results.jsonl`
- **Фильтр:** `path` начинается с `SpikeSamples/`
- **Подробная таблица статусов:** см. `Reports/SpikeSamples-Validation-Report.md`

Каждый локальный `README.md` в подпапках `SpikeSamples` содержит поле «Статус валидации», синхронизированное с этим отчетом.

### Тематические обзоры

Для более глубокого понимания моделируемых сущностей и экспериментов используются следующие документы:

- [`NeuronReactions.md`](NeuronReactions.md) — по мотивам работы [1] ([онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=20:2012-07-19-04-53-55&catid=67&lang=ru&Itemid=676)).
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — по работе [2] ([онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676)).
- [`MuscleControlStructures.md`](MuscleControlStructures.md) — по работе [3] ([онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=29:1&catid=67&lang=ru&Itemid=676)).
- [`CSNM-Models.md`](CSNM-Models.md) — компартментная спайковая модель нейрона (CSNM) с кабельным уравнением, пространственные параметры, компоненты кабельной модели.
- [`StructuralAdaptation.md`](StructuralAdaptation.md) — метод структурной адаптации компартментной спайковой модели нейрона, автоматический подбор структуры для распознавания паттернов.
- [`IncrementalLearning.md`](IncrementalLearning.md) — стратегия инкрементального обучения на компартментной спайковой модели нейрона, обучение на новых образцах без переобучения.
- [`Classification.md`](Classification.md) — применение сегментной спайковой модели нейрона со структурной адаптацией для решения задач классификации, временное кодирование, результаты на Iris и MNIST.
- [`ActivitySwitcher.md`](ActivitySwitcher.md) — блок последовательного переключения активности для запоминания и воспроизведения последовательности ситуаций.
- [`CognitiveMap.md`](CognitiveMap.md) — алгоритм формирования когнитивной карты и исследования среды роботом.
- [`HowToDocumentConfigs.md`](HowToDocumentConfigs.md) — рекомендации по оформлению `README.md` для конфигураций SpikeSamples.

Каждый из этих файлов связывает теоретическое описание из статей с конкретными конфигурациями в `SpikeSamples`, указывая:

- какие биологические прототипы моделируются;
- какие конфигурации (`Bin/Configs/SpikeSamples/...`) соответствуют рисункам и схемам из статей;
- какие параметры в конфигурациях критичны для воспроизведения описанных реакций.

### Связь с компонентной документацией

Все конфигурации `SpikeSamples` построены на компонентах PulseLib и базовых библиотек Rdk. Для детального описания элементарных блоков см.:

- `Docs/Libraries/Nmsdk-PulseLib.md`
- `Libraries/Nmsdk-PulseLib/Docs/Components/NPulseMembrane.md`
- `Libraries/Nmsdk-PulseLib/Docs/Components/NPulseMembraneCommon.md`
- `Libraries/Nmsdk-PulseLib/Docs/Components/NPulseChannel.md`
- `Libraries/Nmsdk-PulseLib/Docs/Components/NPulseSynapse.md`
- `Libraries/Nmsdk-PulseLib/Docs/Components/NSPMinNeuron.md`

В `README.md` отдельных конфигураций будут приведены ссылки на конкретные компонентные описания, которые используются в данной конфигурации.

## Литература

1. Бахшиев А.В., Романов С.П. Воспроизведение реакций естественных нейронов как результат моделирования структурно-функциональных свойств мембраны и организации синаптического аппарата // Нейрокомпьютеры: разработка, применение, №7, 2012. – с.25-35. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=20:2012-07-19-04-53-55&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=17997711)

2. Бахшиев А.В., Романов С.П. Математическое моделирование процессов преобразования импульсных потоков в естественном нейроне // Нейрокомпьютеры: разработка, применение, №3, 2009. – с.71-80. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

3. Бахшиев А.В., Романов С.П. Моделирование нейронных структур управления мышечным сокращением. Схемы нейронных сетей. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=29:1&catid=67&lang=ru&Itemid=676)

