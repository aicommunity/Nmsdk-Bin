## RU

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

---

## EN

## SpikeSamples Documentation Index

### All topical documents

- [`ActivitySwitcher.md`](ActivitySwitcher.md) — sequential activity switching block
- [`Classification.md`](Classification.md) — classification with temporal coding
- [`CognitiveMap.md`](CognitiveMap.md) — cognitive map formation algorithm
- [`CSNM-Models.md`](CSNM-Models.md) — compartmental spiking neuron model (CSNM)
- [`HowToDocumentConfigs.md`](HowToDocumentConfigs.md) — guidelines for formatting configuration README files
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — impulse stream processing model
- [`IncrementalLearning.md`](IncrementalLearning.md) — incremental learning
- [`MuscleControlStructures.md`](MuscleControlStructures.md) — muscle contraction control structures
- [`NeuronReactions.md`](NeuronReactions.md) — single-neuron responses
- [`StructuralAdaptation.md`](StructuralAdaptation.md) — neuronal structural adaptation

Navigation documents: [`Overview.md`](Overview.md), [`Index.md`](Index.md).

### Topical sections

- **Single-neuron responses**
  - Overview: [`NeuronReactions.md`](NeuronReactions.md)
  - Example configurations:
    - `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
    - `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
    - `SpikeSamples/NM-Neurons/NM-PN-03/04/05/06-Neuron-*`
    - `SpikeSamples/NM-Neurons/NM-PN-07/08-LtmNeuron-*`
    - `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`
    - `SpikeSamples/NM-Neurons/LIF-Neuron`

- **Impulse stream processing model**
  - Overview: [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md)
  - Example configurations:
    - the same PN neurons (`SpikeSamples/NM-Neurons/*`)
    - `SpikeSamples/Memory/MEM-OneNeuron3`
    - `SpikeSamples/Memory/MEM-SimpleMemory2`
    - `SpikeSamples/STDP/STDP-Simple-01`

- **Cable and compartmental neurons**
  - Overview: [`CSNM-Models.md`](CSNM-Models.md), see also [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md)
  - Example configurations:
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuron*`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti*`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronParametersTest`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM*`

- **Afferent neurons and receptors**
  - Overview: parts of `NeuronReactions.md` and `ImpulseProcessingModel.md`
  - Example configurations:
    - `SpikeSamples/NM-AfferentNeurons/NM-AN-00-AfferentModelComparation`
    - `SpikeSamples/NM-AfferentNeurons/NM-AN-01-NSAfferentNeuron`
    - `SpikeSamples/NM-AfferentNeurons/NM-AN-02-NSimpleAfferentNeuron`
    - `SpikeSamples/NeuralElements/NReceptor`

- **Memory and associative schemes**
  - Overview: linked to works [1], [2] on impulse stream processing and neuronal responses.
  - Example configurations:
    - `SpikeSamples/Memory/MEM-OneNeuron3`
    - `SpikeSamples/Memory/MEM-SimpleMemory2`
    - `SpikeSamples/Memory/SpikeAssociationPlus`
    - `SpikeSamples/Memory/SpikeConditionalReflex`

- **STDP and structural learning**
  - Overview: [`StructuralAdaptation.md`](StructuralAdaptation.md)
  - Example configurations:
    - `SpikeSamples/STDP/STDP-Simple-01`
    - `SpikeSamples/StructTrain/SpikeTrainer`
    - `SpikeSamples/StructTrain/SpikeAnsTrainer`
    - `SpikeSamples/StructTrain/XOR`

- **Structural adaptation**
  - Overview: [`StructuralAdaptation.md`](StructuralAdaptation.md)
  - Method for automatic selection of neuronal structure (soma size, dendrite length, number of synapses)
  - Example configurations:
    - `SpikeSamples/StructTrain/SpikeTrainer`
    - `SpikeSamples/StructTrain/SpikeAnsTrainer`
    - `SpikeSamples/StructTrain/XOR`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM*`

- **Incremental learning**
  - Overview: [`IncrementalLearning.md`](IncrementalLearning.md)
  - Strategy for training on new samples without retraining on all data
  - Example configurations:
    - `SpikeSamples/Classifier/SpikeIrisClassifier`
    - `SpikeSamples/StructTrain/SpikeTrainer`
    - `SpikeSamples/StructTrain/SpikeAnsTrainer`

- **Classification**
  - Overview: [`Classification.md`](Classification.md)
  - Application of the segmental spiking model to classification tasks
  - Temporal coding of numerical information
  - Example configurations:
    - `SpikeSamples/Classifier/SpikeIrisClassifier`
    - Configurations with structural adaptation

- **CSNM models (Compartmental Spiking Neuron Model)**
  - Overview: [`CSNM-Models.md`](CSNM-Models.md)
  - Cable theory and integration of the cable equation
  - Spatial parameters (segment length ~200 µm, diameter ~20 µm)
  - Components: `NSynapseCable`, `NPulseChannelCable`, `NPulseMembraneCable`, `NPulseLTZoneCable`, `NPulseNeuronCable`, `NPulseNeuronCableMulti`
  - Example configurations:
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM_Nd`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM_Nsyn`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_Lengths`
    - `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_Diameters`

- **Movement control and muscle contraction structures**
  - Overview: [`MuscleControlStructures.md`](MuscleControlStructures.md)
  - Example configurations:
    - `SpikeSamples/MC0-RCN/*`
    - `SpikeSamples/MC1-PCN/*`
    - `SpikeSamples/EyeRetina/EyeRetina`
    - `SpikeSamples/EyeRetina/EyeRetinaMuscle`

- **ActivitySwitcher (activity switching)**
  - Overview: [`ActivitySwitcher.md`](ActivitySwitcher.md)
  - Sequential activity switching block between graph nodes based on CSNM neurons
  - Related to [`CognitiveMap.md`](CognitiveMap.md) and movement control configurations (`SpikeSamples/MC1-PCN/*`)

- **Cognitive map**
  - Overview: [`CognitiveMap.md`](CognitiveMap.md)
  - Algorithm for building a situation graph during robot environment exploration
  - Uses ActivitySwitcher and SignalManager blocks
  - See also [`ActivitySwitcher.md`](ActivitySwitcher.md)

- **Configuration documentation formatting**
  - Guide: [`HowToDocumentConfigs.md`](HowToDocumentConfigs.md)
  - Recommendations for structure and content of `README.md` in `Bin/Configs/SpikeSamples/...`

### Configuration navigation

For each current configuration under `Bin/Configs/SpikeSamples/...`, a local `README.md` has been created with:

- biological motivation;
- model structure (with mermaid diagrams);
- experiment descriptions and expected results;
- validation status (based on `Reports/SpikeSamples-Validation-Report.md`);
- links to rtf/txt descriptions and articles.

Recommended navigation path:

1. Start with [`Overview.md`](Overview.md) for general context of the collection.
2. Go to the topical document of interest (e.g., [`NeuronReactions.md`](NeuronReactions.md)).
3. Select a specific configuration and open its `README.md` in `Bin/Configs/SpikeSamples/...`.

## Literature

1. Bakhshiev A. V., Romanov S. P. Reproducing natural neuron responses as a result of modeling structural-functional properties of the membrane and synaptic apparatus organization // Neurocomputers: Development, Application, No. 7, 2012. – pp. 25-35. [online](https://neuromodeler.ru/index.php?option=com_content&view=article&id=20:2012-07-19-04-53-55&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=17997711)

2. Bakhshiev A. V., Romanov S. P. Mathematical modeling of impulse stream processing in a natural neuron // Neurocomputers: Development, Application, No. 3, 2009. – pp. 71-80. [online](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

