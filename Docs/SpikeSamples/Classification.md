## RU

## Применение сегментной спайковой модели нейрона со структурной адаптацией для решения задач классификации

### Назначение метода

Сегментная спайковая модель нейрона со структурной адаптацией применяется для решения задач классификации, где требуется:
- Распознавание различных классов объектов
- Адаптация к новым классам без полного переобучения
- Эффективная обработка временных паттернов
- Работа в условиях ограниченных вычислительных ресурсов

### Анализ современного состояния спайковых нейронных сетей

#### Выводы из публикации

Согласно анализу, проведённому в работе [1]:
- Существует **крайне низкое количество работ** по исследованию сегментных моделей нейрона
- Большинство исследований фокусируется на точечных моделях (LIF, Izhikevich и др.)
- Сегментные модели открывают новые возможности для решения задач классификации

#### Обоснование выбора модели

В качестве модели нейрона для данной работы обоснован выбор **сегментной спайковой модели** по следующим причинам:
- Возможность структурного реконфигурирования
- Учёт пространственного распространения сигналов
- Способность обрабатывать сложные временные паттерны
- Биологическая реалистичность

### Основные концепции

#### Сегментная спайковая модель нейрона

Сегментная спайковая модель нейрона представляет собой модель, где:
- Нейрон разделён на сегменты (компартменты): сома и дендриты
- Каждый сегмент имеет свои параметры мембраны
- Сигналы распространяются между сегментами с учётом пространственных задержек
- Структура нейрона может изменяться в процессе обучения

#### Возможность структурного реконфигурирования

Основные особенности, позволяющие производить структурное реконфигурирование:
- **Динамическое изменение структуры:** размер сомы, длина дендритов, количество синапсов могут изменяться
- **Автоматический подбор параметров:** алгоритм автоматически выбирает оптимальную структуру для каждого паттерна
- **Сохранение функциональности:** изменения структуры не нарушают способность распознавать ранее обученные паттерны

#### Временное кодирование

В качестве кодирования числовой информации в паттерны импульсов выбирается **временное кодирование**:

- **Принцип:** числовое значение преобразуется в момент времени появления спайка
- **Преимущества:**
  - Эффективное использование временной информации
  - Естественное представление для спайковых нейронных сетей
  - Возможность обработки временных последовательностей

**Пример временного кодирования:**
- Большее значение → более ранний спайк
- Меньшее значение → более поздний спайк
- Нулевое значение → отсутствие спайка

#### Структурная адаптация модели ко входному паттерну импульсов

Способ структурной адаптации модели ко входному паттерну импульсов включает:

1. **Анализ входного паттерна:**
   - Определение размерности вектора паттерна
   - Анализ временного кодирования
   - Определение требуемой структуры нейрона

2. **Автоматический подбор параметров:**
   - **Размер сомы:** количество соматических участков мембраны
   - **Длина дендритов:** количество сегментов в каждом дендрите
   - **Количество синапсов:** число синапсов на каждом дендрите

3. **Обучение на паттерне:**
   - Предъявление паттерна нейрону
   - Мониторинг активности нейрона
   - Корректировка структуры при необходимости

#### Общая схема организации сегментных спайковых нейронов в сеть

Для решения задачи классификации сегментные спайковые нейроны организуются в сеть следующим образом:

```mermaid
flowchart TD
    Input[Входные данные] --> Encode[Временное кодирование]
    Encode --> Pattern[Паттерн спайков]
    Pattern --> Network[Сеть сегментных нейронов]
    Network --> Neuron1[Нейрон класса 1]
    Network --> Neuron2[Нейрон класса 2]
    Network --> Neuron3[Нейрон класса N]
    Neuron1 --> Decision[Принятие решения]
    Neuron2 --> Decision
    Neuron3 --> Decision
    Decision --> Output[Выходной класс]
```

**Архитектура сети:**
- Каждый нейрон обучается распознавать один класс
- Входной паттерн подаётся на все нейроны одновременно
- Нейрон, генерирующий спайк, определяет класс образца
- При обучении используется структурная адаптация для каждого нейрона

### Результаты экспериментов

#### Классификация на общедоступных наборах данных

##### Iris (UCI Machine Learning Repository)

**Описание набора данных:**
- 150 образцов цветков ириса
- 3 класса: Iris-setosa, Iris-versicolor, Iris-virginica
- 4 признака: длина и ширина чашелистика, длина и ширина лепестка

**Результаты:**
- Сопоставимость результатов с классическими методами машинного обучения
- Успешное применение сегментной спайковой модели со структурной адаптацией
- Возможность инкрементального обучения на новых классах

##### MNIST (handwritten digit database)

**Описание набора данных:**
- 70,000 изображений рукописных цифр (0-9)
- 60,000 образцов для обучения, 10,000 для тестирования
- Размер изображения: 28×28 пикселей

**Результаты:**
- Применение временного кодирования для преобразования изображений в паттерны спайков
- Использование структурной адаптации для обучения нейронов на различных классах
- Сопоставимость результатов с классическими методами

**Особенности:**
- Преобразование пространственной информации изображения во временные паттерны
- Использование сегментной структуры для обработки сложных паттернов
- Возможность обработки больших объёмов данных

#### Применение для определения состояния телеуправляемого необитаемого подводного аппарата

##### Задача определения расстояния до дна

**Описание эксперимента:**
- Определение расстояния телеуправляемого необитаемого подводного аппарата (АНПА) до дна
- Использование данных с датчиков давления
- Классификация различных расстояний до дна

**Методика:**
1. Сбор данных с датчиков давления при различных расстояниях до дна
2. Преобразование данных в паттерны спайков с временным кодированием
3. Обучение сети сегментных нейронов на различных классах расстояний
4. Тестирование на новых данных

**Результаты:**
- Показано соответствие полученных результатов реальному состоянию АНПА
- Успешная классификация различных расстояний до дна
- Возможность применения в реальных условиях

##### Задача определения характера движения

**Описание эксперимента:**
- Определение характера движения АНПА (подъём, спуск, горизонтальное движение и т.д.)
- Использование данных с различных датчиков
- Классификация различных режимов движения

**Методика:**
1. Сбор данных о движении АНПА в различных режимах
2. Преобразование данных в паттерны спайков
3. Обучение сети для распознавания различных режимов движения
4. Валидация на реальных данных

**Результаты:**
- Показано соответствие полученных результатов реальному состоянию АНПА
- Успешная классификация различных режимов движения
- Демонстрация применимости метода для практических задач

### Схемы организации сегментных спайковых нейронов в сеть

#### Архитектура сети для классификации

**Диаграмма классов архитектуры сети:**

```mermaid
classDiagram
    class InputLayer {
        +Входные данные
        +Временное кодирование
    }
    class SegmentNeuron {
        +Структурная адаптация
        +Распознавание паттерна
        +Генерация спайка
    }
    class OutputLayer {
        +Принятие решения
        +Определение класса
    }

    InputLayer --> SegmentNeuron : Паттерн спайков
    SegmentNeuron --> OutputLayer : Выходной спайк
```

#### Взаимодействие нейронов в сети

- **Параллельная обработка:** все нейроны получают входной паттерн одновременно
- **Конкуренция:** нейрон, генерирующий спайк первым или с наибольшей амплитудой, определяет класс
- **Независимое обучение:** каждый нейрон обучается независимо на своём классе
- **Структурная адаптация:** каждый нейрон адаптирует свою структуру под свой класс

#### Процесс принятия решения о классе

1. **Предъявление входного паттерна:**
   - Входные данные преобразуются в паттерн спайков с временным кодированием
   - Паттерн подаётся на все нейроны сети одновременно

2. **Генерация спайков:**
   - Каждый нейрон анализирует входной паттерн
   - Нейроны, обученные на похожих паттернах, генерируют спайки
   - Время генерации спайка зависит от степени соответствия паттерну

3. **Определение класса:**
   - Класс определяется нейроном, который генерирует спайк
   - При генерации спайков несколькими нейронами выбирается нейрон с наибольшей амплитудой или наименьшим временем генерации

### Описание экспериментов и результатов

#### Методика проведения экспериментов

**Общая схема эксперимента:**

1. **Подготовка данных:**
   - Нормализация признаков
   - Преобразование в паттерны спайков с временным кодированием
   - Разделение на обучающую и тестовую выборки

2. **Обучение сети:**
   - Создание нейронов для каждого класса
   - Обучение каждого нейрона на своём классе с использованием структурной адаптации
   - Проверка способности распознавать свой класс

3. **Тестирование:**
   - Предъявление тестовых образцов сети
   - Определение класса каждым нейроном
   - Вычисление метрик качества классификации

#### Метрики качества классификации

**Основные метрики:**
- **Точность (Accuracy):** доля правильно классифицированных образцов
- **Точность по классам (Precision):** для каждого класса отдельно
- **Полнота (Recall):** способность находить все образцы класса
- **F-мера (F1-score):** гармоническое среднее точности и полноты

**Результаты на Iris:**
- Сопоставимость с классическими методами (k-NN, SVM, нейронные сети)
- Высокая точность классификации всех трёх классов
- Успешное применение инкрементального обучения

**Результаты на MNIST:**
- Сопоставимость с классическими методами для небольших подмножеств данных
- Демонстрация возможности обработки изображений
- Потенциал для масштабирования на полный набор данных

#### Сравнение с другими методами

**Преимущества сегментной модели:**
- Возможность структурной адаптации
- Эффективная обработка временных паттернов
- Инкрементальное обучение без переобучения
- Биологическая реалистичность

**Ограничения:**
- Вычислительная сложность выше, чем у простых моделей
- Требуется больше времени на обучение
- Необходимость настройки параметров структурной адаптации

### Соответствующие конфигурации SpikeSamples

Следующие конфигурации демонстрируют применение для задач классификации:

- **`SpikeSamples/Classifier/SpikeIrisClassifier`** — классификация на Iris
  - Демонстрирует применение сегментной модели для классификации цветков ириса
  - Использует временное кодирование и структурную адаптацию
  - Показывает результаты инкрементального обучения

- **Конфигурации, демонстрирующие временное кодирование:**
  - Конфигурации, преобразующие числовые данные в паттерны спайков
  - Примеры различных способов временного кодирования

- **Конфигурации со структурной адаптацией:**
  - `SpikeSamples/StructTrain/SpikeTrainer` — базовое структурное обучение
  - `SpikeSamples/StructTrain/SpikeAnsTrainer` — структурное обучение с ответами
  - Демонстрируют процесс структурной адаптации для распознавания паттернов

### Перспективы применения

Согласно публикации [1], применение спайковых сегментных моделей нейрона с возможностью структурной адаптации перспективно для:

1. **Задач классификации:**
   - Распознавание образов
   - Классификация временных рядов
   - Обработка сенсорных данных

2. **Робототехники:**
   - Определение состояния роботов
   - Классификация режимов работы
   - Адаптация к изменяющимся условиям

3. **Нейроморфных систем:**
   - Энергоэффективная обработка информации
   - Реализация на специализированном оборудовании
   - Онлайн-обучение в реальном времени

4. **Биомедицинских приложений:**
   - Анализ биосигналов
   - Классификация состояний организма
   - Адаптивные системы мониторинга

### Дальнейшие перспективные продолжения исследований

Рассмотрены следующие направления для дальнейших исследований:

1. **Масштабирование на большие наборы данных:**
   - Применение к полным наборам данных (например, полный MNIST)
   - Оптимизация вычислительной сложности
   - Параллельная обработка

2. **Улучшение алгоритмов структурной адаптации:**
   - Более эффективные алгоритмы подбора структуры
   - Автоматическое определение оптимальных параметров
   - Ускорение процесса обучения

3. **Расширение на другие типы задач:**
   - Регрессия
   - Кластеризация
   - Обучение с подкреплением

4. **Интеграция с другими методами:**
   - Комбинация с STDP
   - Использование ансамблей нейронов
   - Гибридные архитектуры

### Связанные материалы

- [`StructuralAdaptation.md`](StructuralAdaptation.md) — метод структурной адаптации, используемый для классификации
- [`IncrementalLearning.md`](IncrementalLearning.md) — стратегия инкрементального обучения для классификации
- [`CSNM-Models.md`](CSNM-Models.md) — описание компартментной спайковой модели нейрона
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — модель преобразования импульсных потоков
- `Libraries/Nmsdk-PulseLib/Docs/Components/NSpikeClassifier.md` — документация компонента NSpikeClassifier
- `Libraries/Nmsdk-PulseLib/Docs/Components/NNeuronTrainer.md` — документация компонента NNeuronTrainer

## Литература

1. Korsakov, A. M., Astapova, L. A., Bakhshiev, A. V. Application of a compartmental spiking neuron model with structural adaptation for solving classification problems // Informatics and Automation, 2022, 21(3), 493-520. [DOI](https://doi.org/10.15622/ia.21.3.2)

2. UCI Machine Learning Repository: Iris Data Set. [онлайн](https://archive.ics.uci.edu/ml/datasets/iris)

3. MNIST handwritten digit database. [онлайн](http://yann.lecun.com/exdb/mnist/)

4. Astapova, L. A., Korsakov, A. M., Bakhshiev, A. V. [et al.] Compartmental spiking neuron model for pattern classification // Journal of Physics: Conference Series, Krasnoyarsk, Russia, 24 сентября – 03 2021 года. Vol. Volume 2094. – Krasnoyarsk, Russia: IOP Publishing Ltd, 2021. – P. 32032. [DOI](https://iopscience.iop.org/article/10.1088/1742-6596/2094/3/032032)

---

## EN

## Application of a segmental spiking neuron model with structural adaptation for solving classification problems

### Purpose of the method

The segmental spiking neuron model with structural adaptation is applied to solve classification problems where the following is required:
- Recognition of different object classes
- Adaptation to new classes without full retraining
- Efficient processing of temporal patterns
- Operation under limited computational resources

### Analysis of the current state of spiking neural networks

#### Conclusions from the publication

According to the analysis conducted in [1]:
- There is an **extremely small number of works** on studying segmental neuron models
- Most research focuses on point models (LIF, Izhikevich, etc.)
- Segmental models open new possibilities for solving classification problems

#### Rationale for model selection

The **segmental spiking model** is justified as the neuron model for this work for the following reasons:
- Capability for structural reconfiguration
- Accounting for spatial signal propagation
- Ability to process complex temporal patterns
- Biological realism

### Core concepts

#### Segmental spiking neuron model

The segmental spiking neuron model is a model where:
- The neuron is divided into segments (compartments): soma and dendrites
- Each segment has its own membrane parameters
- Signals propagate between segments with spatial delays taken into account
- The neuron structure can change during learning

#### Capability for structural reconfiguration

Main features enabling structural reconfiguration:
- **Dynamic structure change:** soma size, dendrite length, and number of synapses can change
- **Automatic parameter selection:** the algorithm automatically selects the optimal structure for each pattern
- **Preservation of functionality:** structural changes do not impair the ability to recognize previously learned patterns

#### Temporal coding

**Temporal coding** is chosen as the method for encoding numerical information into spike patterns:

- **Principle:** a numerical value is converted into the time of spike occurrence
- **Advantages:**
  - Efficient use of temporal information
  - Natural representation for spiking neural networks
  - Ability to process temporal sequences

**Example of temporal coding:**
- Larger value → earlier spike
- Smaller value → later spike
- Zero value → no spike

#### Structural adaptation of the model to an input spike pattern

The method of structural adaptation of the model to an input spike pattern includes:

1. **Input pattern analysis:**
   - Determining the dimension of the pattern vector
   - Analyzing temporal coding
   - Determining the required neuron structure

2. **Automatic parameter selection:**
   - **Soma size:** number of somatic membrane segments
   - **Dendrite length:** number of segments in each dendrite
   - **Number of synapses:** number of synapses on each dendrite

3. **Training on the pattern:**
   - Presenting the pattern to the neuron
   - Monitoring neuron activity
   - Adjusting structure when necessary

#### General scheme for organizing segmental spiking neurons into a network

To solve a classification problem, segmental spiking neurons are organized into a network as follows:

```mermaid
flowchart TD
    Input[Входные данные] --> Encode[Временное кодирование]
    Encode --> Pattern[Паттерн спайков]
    Pattern --> Network[Сеть сегментных нейронов]
    Network --> Neuron1[Нейрон класса 1]
    Network --> Neuron2[Нейрон класса 2]
    Network --> Neuron3[Нейрон класса N]
    Neuron1 --> Decision[Принятие решения]
    Neuron2 --> Decision
    Neuron3 --> Decision
    Decision --> Output[Выходной класс]
```

**Network architecture:**
- Each neuron is trained to recognize one class
- The input pattern is fed to all neurons simultaneously
- The neuron generating a spike determines the sample class
- Structural adaptation is used for each neuron during training

### Experimental results

#### Classification on publicly available datasets

##### Iris (UCI Machine Learning Repository)

**Dataset description:**
- 150 iris flower samples
- 3 classes: Iris-setosa, Iris-versicolor, Iris-virginica
- 4 features: sepal length and width, petal length and width

**Results:**
- Results comparable to classical machine learning methods
- Successful application of the segmental spiking model with structural adaptation
- Capability for incremental learning on new classes

##### MNIST (handwritten digit database)

**Dataset description:**
- 70,000 images of handwritten digits (0-9)
- 60,000 samples for training, 10,000 for testing
- Image size: 28×28 pixels

**Results:**
- Application of temporal coding to convert images into spike patterns
- Use of structural adaptation to train neurons on different classes
- Results comparable to classical methods

**Features:**
- Conversion of spatial image information into temporal patterns
- Use of segmental structure to process complex patterns
- Capability to process large volumes of data

#### Application for determining the state of a remotely operated unmanned underwater vehicle

##### Task of determining distance to the bottom

**Experiment description:**
- Determining the distance of a remotely operated unmanned underwater vehicle (ROV) to the bottom
- Using data from pressure sensors
- Classification of different distances to the bottom

**Methodology:**
1. Collecting data from pressure sensors at various distances to the bottom
2. Converting data into spike patterns with temporal coding
3. Training a network of segmental neurons on different distance classes
4. Testing on new data

**Results:**
- Demonstrated correspondence of obtained results to the actual ROV state
- Successful classification of different distances to the bottom
- Capability for application in real-world conditions

##### Task of determining the nature of motion

**Experiment description:**
- Determining the nature of ROV motion (ascent, descent, horizontal movement, etc.)
- Using data from various sensors
- Classification of different motion modes

**Methodology:**
1. Collecting data on ROV motion in various modes
2. Converting data into spike patterns
3. Training the network to recognize different motion modes
4. Validation on real data

**Results:**
- Demonstrated correspondence of obtained results to the actual ROV state
- Successful classification of different motion modes
- Demonstration of method applicability for practical tasks

### Schemes for organizing segmental spiking neurons into a network

#### Network architecture for classification

**Class diagram of the network architecture:**

```mermaid
classDiagram
    class InputLayer {
        +Входные данные
        +Временное кодирование
    }
    class SegmentNeuron {
        +Структурная адаптация
        +Распознавание паттерна
        +Генерация спайка
    }
    class OutputLayer {
        +Принятие решения
        +Определение класса
    }

    InputLayer --> SegmentNeuron : Паттерн спайков
    SegmentNeuron --> OutputLayer : Выходной спайк
```

#### Interaction of neurons in the network

- **Parallel processing:** all neurons receive the input pattern simultaneously
- **Competition:** the neuron generating a spike first or with the greatest amplitude determines the class
- **Independent learning:** each neuron is trained independently on its own class
- **Structural adaptation:** each neuron adapts its structure to its class

#### Class decision process

1. **Presenting the input pattern:**
   - Input data is converted into a spike pattern with temporal coding
   - The pattern is fed to all neurons in the network simultaneously

2. **Spike generation:**
   - Each neuron analyzes the input pattern
   - Neurons trained on similar patterns generate spikes
   - Spike generation time depends on the degree of pattern match

3. **Class determination:**
   - The class is determined by the neuron that generates a spike
   - When multiple neurons generate spikes, the neuron with the greatest amplitude or earliest generation time is selected

### Description of experiments and results

#### Experimental methodology

**General experiment scheme:**

1. **Data preparation:**
   - Feature normalization
   - Conversion into spike patterns with temporal coding
   - Split into training and test sets

2. **Network training:**
   - Creating neurons for each class
   - Training each neuron on its class using structural adaptation
   - Verifying the ability to recognize its class

3. **Testing:**
   - Presenting test samples to the network
   - Class determination by each neuron
   - Computing classification quality metrics

#### Classification quality metrics

**Main metrics:**
- **Accuracy:** proportion of correctly classified samples
- **Precision:** for each class separately
- **Recall:** ability to find all samples of a class
- **F-measure (F1-score):** harmonic mean of precision and recall

**Results on Iris:**
- Comparable to classical methods (k-NN, SVM, neural networks)
- High classification accuracy for all three classes
- Successful application of incremental learning

**Results on MNIST:**
- Comparable to classical methods for small data subsets
- Demonstration of image processing capability
- Potential for scaling to the full dataset

#### Comparison with other methods

**Advantages of the segmental model:**
- Capability for structural adaptation
- Efficient processing of temporal patterns
- Incremental learning without retraining
- Biological realism

**Limitations:**
- Higher computational complexity than simple models
- More time required for training
- Need to tune structural adaptation parameters

### Corresponding SpikeSamples configurations

The following configurations demonstrate application for classification tasks:

- **`SpikeSamples/Classifier/SpikeIrisClassifier`** — classification on Iris
  - Demonstrates application of the segmental model for iris flower classification
  - Uses temporal coding and structural adaptation
  - Shows incremental learning results

- **Configurations demonstrating temporal coding:**
  - Configurations that convert numerical data into spike patterns
  - Examples of various temporal coding methods

- **Configurations with structural adaptation:**
  - `SpikeSamples/StructTrain/SpikeTrainer` — basic structural training
  - `SpikeSamples/StructTrain/SpikeAnsTrainer` — structural training with answers
  - Demonstrate the structural adaptation process for pattern recognition

### Application prospects

According to publication [1], application of spiking segmental neuron models with structural adaptation capability is promising for:

1. **Classification tasks:**
   - Pattern recognition
   - Time series classification
   - Sensor data processing

2. **Robotics:**
   - Robot state determination
   - Operating mode classification
   - Adaptation to changing conditions

3. **Neuromorphic systems:**
   - Energy-efficient information processing
   - Implementation on specialized hardware
   - Real-time online learning

4. **Biomedical applications:**
   - Biosignal analysis
   - Organism state classification
   - Adaptive monitoring systems

### Further promising research directions

The following directions for further research are considered:

1. **Scaling to large datasets:**
   - Application to full datasets (e.g., full MNIST)
   - Optimization of computational complexity
   - Parallel processing

2. **Improving structural adaptation algorithms:**
   - More efficient structure selection algorithms
   - Automatic determination of optimal parameters
   - Acceleration of the learning process

3. **Extension to other task types:**
   - Regression
   - Clustering
   - Reinforcement learning

4. **Integration with other methods:**
   - Combination with STDP
   - Use of neuron ensembles
   - Hybrid architectures

### Related materials

- [`StructuralAdaptation.md`](StructuralAdaptation.md) — structural adaptation method used for classification
- [`IncrementalLearning.md`](IncrementalLearning.md) — incremental learning strategy for classification
- [`CSNM-Models.md`](CSNM-Models.md) — description of the compartmental spiking neuron model
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — impulse stream conversion model
- `Libraries/Nmsdk-PulseLib/Docs/Components/NSpikeClassifier.md` — NSpikeClassifier component documentation
- `Libraries/Nmsdk-PulseLib/Docs/Components/NNeuronTrainer.md` — NNeuronTrainer component documentation

## References

1. Korsakov, A. M., Astapova, L. A., Bakhshiev, A. V. Application of a compartmental spiking neuron model with structural adaptation for solving classification problems // Informatics and Automation, 2022, 21(3), 493-520. [DOI](https://doi.org/10.15622/ia.21.3.2)

2. UCI Machine Learning Repository: Iris Data Set. [online](https://archive.ics.uci.edu/ml/datasets/iris)

3. MNIST handwritten digit database. [online](http://yann.lecun.com/exdb/mnist/)

4. Astapova, L. A., Korsakov, A. M., Bakhshiev, A. V. [et al.] Compartmental spiking neuron model for pattern classification // Journal of Physics: Conference Series, Krasnoyarsk, Russia, 24 сентября – 03 2021 года. Vol. Volume 2094. – Krasnoyarsk, Russia: IOP Publishing Ltd, 2021. – P. 32032. [DOI](https://iopscience.iop.org/article/10.1088/1742-6596/2094/3/032032)

