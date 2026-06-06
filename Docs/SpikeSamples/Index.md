## Индекс документации SpikeSamples

### Все тематические документы

- [`ActivitySwitcher.md`](ActivitySwitcher.md) — блок последовательного переключения активности
- [`Classification.md`](Classification.md) — классификация с временным кодированием
- [`CognitiveMap.md`](CognitiveMap.md) — алгоритм формирования когнитивной карты
- [`CSNM-Models.md`](CSNM-Models.md) — компартментная спайковая модель нейрона (CSNM)
- [`HowToDocumentConfigs.md`](HowToDocumentConfigs.md) — рекомендации по оформлению README конфигураций
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — модель преобразования импульсных потоков
- [`IncrementalLearning.md`](IncrementalLearning.md) — инкрементальное обучение
- [`MuscleControlStructures.md`](MuscleControlStructures.md) — структуры управления мышечным сокращением
- [`NeuronReactions.md`](NeuronReactions.md) — реакции одиночных нейронов
- [`StructuralAdaptation.md`](StructuralAdaptation.md) — структурная адаптация нейрона

Навигационные документы: [`Overview.md`](Overview.md), [`Index.md`](Index.md).

### Тематические разделы

- **Реакции одиночных нейронов**
  - Обзор: [`NeuronReactions.md`](NeuronReactions.md)
  - Примеры конфигураций:
    - `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
    - `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
    - `SpikeSamples/NM-Neurons/NM-PN-03/04/05/06-Neuron-*`
    - `SpikeSamples/NM-Neurons/NM-PN-07/08-LtmNeuron-*`
    - `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`
    - `SpikeSamples/NM-Neurons/LIF-Neuron`

- **Модель преобразования импульсных потоков**
  - Обзор: [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md)
  - Примеры конфигураций:
    - те же PN‑нейроны (`SpikeSamples/NM-Neurons/*`)
    - `SpikeSamples/Memory/MEM-OneNeuron3`
    - `SpikeSamples/Memory/MEM-SimpleMemory2`
    - `SpikeSamples/STDP/STDP-Simple-01`

- **Кабельные и компартментные нейроны**
  - Обзор: [`CSNM-Models.md`](CSNM-Models.md), см. также [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md)
  - Примеры конфигураций:
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuron*`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti*`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronParametersTest`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM*`

- **Афферентные нейроны и рецепторы**
  - Обзор: части `NeuronReactions.md` и `ImpulseProcessingModel.md`
  - Примеры конфигураций:
    - `SpikeSamples/NM-AfferentNeurons/NM-AN-00-AfferentModelComparation`
    - `SpikeSamples/NM-AfferentNeurons/NM-AN-01-NSAfferentNeuron`
    - `SpikeSamples/NM-AfferentNeurons/NM-AN-02-NSimpleAfferentNeuron`
    - `SpikeSamples/NeuralElements/NReceptor`

- **Память и ассоциативные схемы**
  - Обзор: связывается с работами [1], [2] о преобразовании импульсных потоков и реакциях нейронов.
  - Примеры конфигураций:
    - `SpikeSamples/Memory/MEM-OneNeuron3`
    - `SpikeSamples/Memory/MEM-SimpleMemory2`
    - `SpikeSamples/Memory/SpikeAssociationPlus`
    - `SpikeSamples/Memory/SpikeConditionalReflex`

- **STDP и структурное обучение**
  - Обзор: [`StructuralAdaptation.md`](StructuralAdaptation.md)
  - Примеры конфигураций:
    - `SpikeSamples/STDP/STDP-Simple-01`
    - `SpikeSamples/StructTrain/SpikeTrainer`
    - `SpikeSamples/StructTrain/SpikeAnsTrainer`
    - `SpikeSamples/StructTrain/XOR`

- **Структурная адаптация**
  - Обзор: [`StructuralAdaptation.md`](StructuralAdaptation.md)
  - Метод автоматического подбора структуры нейрона (размер сомы, длина дендритов, количество синапсов)
  - Примеры конфигураций:
    - `SpikeSamples/StructTrain/SpikeTrainer`
    - `SpikeSamples/StructTrain/SpikeAnsTrainer`
    - `SpikeSamples/StructTrain/XOR`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM*`

- **Инкрементальное обучение**
  - Обзор: [`IncrementalLearning.md`](IncrementalLearning.md)
  - Стратегия обучения на новых образцах без переобучения на всех данных
  - Примеры конфигураций:
    - `SpikeSamples/Classifier/SpikeIrisClassifier`
    - `SpikeSamples/StructTrain/SpikeTrainer`
    - `SpikeSamples/StructTrain/SpikeAnsTrainer`

- **Классификация**
  - Обзор: [`Classification.md`](Classification.md)
  - Применение сегментной спайковой модели для задач классификации
  - Временное кодирование числовой информации
  - Примеры конфигураций:
    - `SpikeSamples/Classifier/SpikeIrisClassifier`
    - Конфигурации со структурной адаптацией

- **CSNM модели (Компартментная спайковая модель нейрона)**
  - Обзор: [`CSNM-Models.md`](CSNM-Models.md)
  - Кабельная теория и интеграция кабельного уравнения
  - Пространственные параметры (длина сегмента ~200 мкм, диаметр ~20 мкм)
  - Компоненты: `NSynapseCable`, `NPulseChannelCable`, `NPulseMembraneCable`, `NPulseLTZoneCable`, `NPulseNeuronCable`, `NPulseNeuronCableMulti`
  - Примеры конфигураций:
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM_Nd`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM_Nsyn`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_Lengths`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_Diameters`

- **Структуры управления движением и мышечным сокращением**
  - Обзор: [`MuscleControlStructures.md`](MuscleControlStructures.md)
  - Примеры конфигураций:
    - `SpikeSamples/MC0-RCN/*`
    - `SpikeSamples/MC1-PCN/*`
    - `SpikeSamples/EyeRetina/EyeRetina`
    - `SpikeSamples/EyeRetina/EyeRetinaMuscle`

- **ActivitySwitcher (переключение активности)**
  - Обзор: [`ActivitySwitcher.md`](ActivitySwitcher.md)
  - Блок последовательного переключения активности между узлами графа на базе нейронов CSNM
  - Связан с [`CognitiveMap.md`](CognitiveMap.md) и конфигурациями управления движением (`SpikeSamples/MC1-PCN/*`)

- **Когнитивная карта**
  - Обзор: [`CognitiveMap.md`](CognitiveMap.md)
  - Алгоритм построения графа ситуаций при исследовании среды роботом
  - Использует блоки ActivitySwitcher и SignalManager
  - См. также [`ActivitySwitcher.md`](ActivitySwitcher.md)

- **Оформление документации конфигураций**
  - Руководство: [`HowToDocumentConfigs.md`](HowToDocumentConfigs.md)
  - Рекомендации по структуре и содержанию `README.md` в `Bin/Configs/SpikeSamples/...`

### Навигация по конфигурациям

Для каждой текущей конфигурации под `Bin/Configs/SpikeSamples/...` создан локальный `README.md` с:

- биологической мотивацией;
- структурой модели (с mermaid‑диаграммами);
- описанием экспериментов и ожидаемых результатов;
- статусом валидации (на основе `Reports/SpikeSamples-Validation-Report.md`);
- ссылками на rtf/txt‑описания и статьи.

Рекомендуемый путь навигации:

1. Начать с [`Overview.md`](Overview.md) для общего контекста коллекции.
2. Перейти в интересующий тематический документ (например, [`NeuronReactions.md`](NeuronReactions.md)).
3. Выбрать конкретную конфигурацию и открыть её `README.md` в `Bin/Configs/SpikeSamples/...`.

## Литература

1. Бахшиев А.В., Романов С.П. Воспроизведение реакций естественных нейронов как результат моделирования структурно-функциональных свойств мембраны и организации синаптического аппарата // Нейрокомпьютеры: разработка, применение, №7, 2012. – с.25-35. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=20:2012-07-19-04-53-55&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=17997711)

2. Бахшиев А.В., Романов С.П. Математическое моделирование процессов преобразования импульсных потоков в естественном нейроне // Нейрокомпьютеры: разработка, применение, №3, 2009. – с.71-80. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

