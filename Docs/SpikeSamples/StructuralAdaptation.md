## RU

## Метод структурной адаптации компартментной спайковой модели нейрона

### Назначение метода

Метод структурной адаптации позволяет автоматически подбирать параметры компартментной спайковой модели нейрона в зависимости от заданного входного паттерна. В отличие от традиционных методов обучения, где изменяются только синаптические веса, структурная адаптация изменяет саму топологию нейрона: размер сомы, длину дендритов и количество синапсов на каждом дендрите.

### Основные концепции

#### Задача обучения

Задача обучения состоит в формировании ответа на паттерн, представленный **вектором одиночных спайков с временным кодированием**, где каждый компонент вектора входит в отдельный дендрит нейрона.

Временное кодирование означает, что числовая информация преобразуется в последовательность импульсов, где момент времени появления импульса несёт информацию о значении. Например, большее значение может кодироваться более ранним временем появления спайка.

#### Автоматический подбор параметров нейрона

В зависимости от заданного паттерна алгоритм автоматически выбирает следующие параметры модели нейрона:

1. **Размер сомы** (количество соматических участков мембраны, N_s)
   - Влияет на способность нейрона интегрировать входные сигналы
   - Большая сома обеспечивает более стабильную интеграцию, но может снижать чувствительность

2. **Длина дендритов** (количество сегментов в каждом дендрите, N_d)
   - Определяет задержку распространения сигнала от синапса к соме
   - Более длинные дендриты позволяют лучше обрабатывать временные паттерны
   - Каждый дендрит может иметь свою длину

3. **Количество синапсов на каждом дендрите** (N_syn)
   - Определяет количество входных каналов для каждого дендрита
   - Влияет на способность нейрона различать различные паттерны

#### Признак распознавания паттерна

Признаком распознавания паттерна обученной моделью является **генерация выходного спайка** нейроном при предъявлении соответствующего входного паттерна.

#### Универсальное значение порога активации

Экспериментально было определено **универсальное значение порога активации нейрона**, которое не зависит от размера вектора, описывающего входной паттерн. Это важное свойство позволяет использовать один и тот же порог для различных задач классификации без необходимости его подстройки.

### Алгоритм структурной адаптации

Процесс структурной адаптации можно представить следующими этапами:

**Схема процесса структурной адаптации:**

```mermaid
flowchart TD
    Start[Начало обучения] --> Analyze[Анализ входного паттерна]
    Analyze --> Determine[Определение необходимой структуры]
    Determine --> Create[Автоматическое создание/модификация структуры]
    Create --> Train[Обучение на заданном паттерне]
    Train --> Check{Нейрон генерирует спайк?}
    Check -->|Нет| Adjust[Корректировка структуры]
    Adjust --> Create
    Check -->|Да| End[Обучение завершено]
```

#### Этап 1: Анализ входного паттерна

- Определение размерности вектора паттерна (количество компонентов)
- Анализ временного кодирования (времена появления спайков)
- Определение требуемого количества дендритов (равно количеству компонентов вектора)

#### Этап 2: Определение необходимой структуры

- Выбор начальной структуры нейрона:
  - Количество соматических участков (обычно начинается с минимального)
  - Количество дендритов (равно размерности входного паттерна)
  - Начальная длина каждого дендрита (обычно начинается с 1 сегмента)
  - Количество синапсов на каждом дендрите (обычно начинается с 1)

#### Этап 3: Автоматическое создание/модификация структуры

На этом этапе происходит:
- Создание структуры нейрона с заданными параметрами
- Подключение входных генераторов к соответствующим синапсам
- Настройка параметров мембраны, каналов и синапсов

#### Этап 4: Обучение на заданном паттерне

- Предъявление входного паттерна нейрону
- Мониторинг активности нейрона
- Измерение амплитуды мембранного потенциала
- Проверка генерации выходного спайка

#### Этап 5: Корректировка структуры (при необходимости)

Если нейрон не генерирует спайк или генерирует его некорректно:
- Увеличение длины дендритов (для улучшения временной обработки)
- Изменение размера сомы (для изменения порога активации)
- Добавление синапсов (для усиления входного сигнала)
- Повторное обучение с новой структурой

### Реализация в NMSDK

В NMSDK структурная адаптация реализована через компонент `NNeuronTrainer` (библиотека `Nmsdk-PulseLib`).

#### Основные параметры NNeuronTrainer

- `NumInputDendrite` — количество входных дендритов (соответствует размерности входного паттерна)
- `MaxDendriteLength` — максимальная длина дендритов
- `InputPattern` — матрица входных паттернов (временное кодирование)
- `LTZThreshold` — порог активации низкопороговой зоны
- `FixedLTZThreshold` — фиксированный порог активации
- `TrainingLTZThreshold` — порог активации во время обучения
- `SpikesFrequency` — частота генерации спайков
- `StructureBuildMode` — режим сборки структуры (1 — структурная адаптация)
- `CalculateMode` — режим расчёта (определяет алгоритм обучения)

#### Процесс структурной адаптации в NNeuronTrainer

Компонент `NNeuronTrainer` реализует структурную адаптацию следующим образом:

1. **Инициализация структуры:**
   - Создание нейрона с начальной структурой
   - Создание генераторов импульсов для каждого входного дендрита
   - Подключение генераторов к синапсам на дендритах

2. **Итеративное обучение:**
   - На каждой итерации измеряется амплитуда мембранного потенциала
   - Если амплитуда увеличивается при увеличении длины дендрита — дендрит продолжает расти
   - Если амплитуда не увеличивается — дендрит укорачивается или обучение переходит к следующему дендриту

3. **Синхронизация дендритов:**
   - Алгоритм стремится синхронизировать времена достижения максимальной амплитуды на разных дендритах
   - Это обеспечивает оптимальную временную обработку паттерна

4. **Завершение обучения:**
   - Обучение завершается, когда все дендриты синхронизированы и нейрон генерирует спайк при предъявлении паттерна

### Соответствующие конфигурации SpikeSamples

Следующие конфигурации демонстрируют структурную адаптацию:

- **`SpikeSamples/StructTrain/SpikeTrainer`** — базовое структурное обучение
  - Демонстрирует процесс структурной адаптации на простом паттерне
  - Использует компонент `NNeuronTrainer` для автоматической подстройки структуры

- **`SpikeSamples/StructTrain/SpikeAnsTrainer`** — структурное обучение с ответами
  - Расширенная версия с возможностью обучения на нескольких паттернах
  - Демонстрирует формирование ответов на различные входные паттерны

- **`SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM*`** — CSNM модели с возможностью структурной адаптации
  - Демонстрируют структурную адаптацию на компартментных моделях нейронов
  - Показывают влияние пространственных параметров на процесс адаптации

### Параметры, влияющие на структурную адаптацию

#### Максимальная длина дендритов (`MaxDendriteLength`)

- Ограничивает максимальное количество сегментов в каждом дендрите
- Влияет на максимальную задержку обработки сигнала
- Рекомендуемые значения: от 10 до 100 сегментов в зависимости от задачи

#### Максимальное количество синапсов

- Определяется структурой нейрона и параметрами мембраны
- Влияет на способность нейрона интегрировать множественные входы
- Обычно устанавливается равным количеству входных дендритов

#### Порог активации нейрона (`LTZThreshold`, `FixedLTZThreshold`)

- Универсальное значение порога, не зависящее от размера входного паттерна
- Критически важен для правильного распознавания паттернов
- Может быть фиксированным или адаптивным в зависимости от режима обучения

#### Параметры временного кодирования

- `SpikesFrequency` — частота генерации спайков входными генераторами
- `Delay` — задержка начала обучения относительно старта системы
- `InputPattern` — матрица временных задержек для каждого компонента паттерна

### Схема процесса структурной адаптации

**Диаграмма последовательности процесса структурной адаптации:**

```mermaid
sequenceDiagram
    participant Input as Входной паттерн
    participant Trainer as NNeuronTrainer
    participant Neuron as Нейрон
    participant Structure as Структура нейрона

    Input->>Trainer: Вектор спайков с временным кодированием
    Trainer->>Trainer: Анализ паттерна
    Trainer->>Structure: Определение начальной структуры
    Structure->>Neuron: Создание нейрона
    Trainer->>Neuron: Предъявление паттерна
    Neuron->>Trainer: Амплитуда потенциала
    Trainer->>Trainer: Проверка генерации спайка
    alt Спайк не генерируется
        Trainer->>Structure: Корректировка структуры
        Structure->>Neuron: Модификация нейрона
        Trainer->>Neuron: Повторное предъявление
    else Спайк генерируется
        Trainer->>Trainer: Обучение завершено
    end
```

### Влияние параметров на результат адаптации

#### Размер сомы

- **Малая сома** (1-2 участка):
  - Высокая чувствительность к входным сигналам
  - Быстрая генерация спайков
  - Может быть нестабильной при сложных паттернах

- **Большая сома** (3+ участков):
  - Более стабильная интеграция сигналов
  - Более высокий порог активации
  - Лучше подходит для сложных паттернов

#### Длина дендритов

- **Короткие дендриты** (1-3 сегмента):
  - Минимальная задержка обработки
  - Быстрая реакция на входные сигналы
  - Ограниченные возможности временной обработки

- **Длинные дендриты** (10+ сегментов):
  - Значительная задержка обработки
  - Возможность обработки сложных временных паттернов
  - Может потребоваться больше времени на обучение

#### Количество синапсов

- **Один синапс на дендрит:**
  - Простая структура
  - Быстрое обучение
  - Ограниченная способность к интеграции

- **Несколько синапсов на дендрит:**
  - Более сложная структура
  - Улучшенная интеграция сигналов
  - Может потребоваться больше времени на обучение

### Связь с другими методами обучения

Структурная адаптация может комбинироваться с другими методами обучения:

- **STDP (Spike-Timing-Dependent Plasticity)** — изменение синаптических весов в зависимости от времени спайков
- **Инкрементальное обучение** — обучение на новых образцах без переобучения на всех предыдущих
- **Классификация** — применение структурной адаптации для решения задач классификации

### Примеры использования

#### Пример 1: Простое распознавание паттерна

```cpp
// Создание NNeuronTrainer
NNeuronTrainer* trainer = CreateComponent<NNeuronTrainer>("Trainer");

// Настройка параметров
trainer->NumInputDendrite = 3;  // 3 компонента в паттерне
trainer->MaxDendriteLength = 50;
trainer->LTZThreshold = 0.0117;  // Универсальный порог
trainer->SpikesFrequency = 1.5;

// Задание входного паттерна (временные задержки в секундах)
MDMatrix<double> pattern;
pattern.Resize(3, 1);
pattern[0] = 0.0;   // Первый спайк в момент 0
pattern[1] = 0.1;   // Второй спайк через 0.1 сек
pattern[2] = 0.2;   // Третий спайк через 0.2 сек
trainer->InputPattern = pattern;

// Запуск обучения
trainer->IsNeedToTrain = true;
trainer->Reset();
```

#### Пример 2: Обучение на нескольких паттернах

Структурная адаптация может использоваться для обучения нейрона распознавать несколько различных паттернов, где каждый паттерн соответствует отдельному классу.

### Результаты экспериментов

Согласно публикации [1]:

- Метод структурной адаптации успешно применяется для обучения компартментной спайковой модели нейрона
- Универсальное значение порога активации позволяет использовать один и тот же порог для различных размеров входных паттернов
- Качество распознавания паттернов сопоставимо с классическими методами обучения
- Структурная адаптация обеспечивает автоматический подбор оптимальной структуры нейрона для каждого паттерна

### Связанные материалы

- [`IncrementalLearning.md`](IncrementalLearning.md) — стратегия инкрементального обучения, использующая структурную адаптацию
- [`Classification.md`](Classification.md) — применение структурной адаптации для задач классификации
- [`CSNM-Models.md`](CSNM-Models.md) — описание компартментной спайковой модели нейрона
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — модель преобразования импульсных потоков
- `Libraries/Nmsdk-PulseLib/Docs/Components/NNeuronTrainer.md` — документация компонента NNeuronTrainer

## Литература

1. Korsakov, A., Astapova, L., Bakhshiev, A. The Method of Structural Adaptation of the Compartmental Spiking Neuron Model // Cyber-Physical Systems and Control II. CPS&C 2021. Lecture Notes in Networks and Systems, vol 460. Springer, Cham, 2023. [DOI](https://doi.org/10.1007/978-3-031-20875-1_51)

---

## EN

## Structural adaptation method for the compartmental spiking neuron model

### Purpose of the method

The structural adaptation method automatically selects parameters of the compartmental spiking neuron model depending on a given input pattern. Unlike traditional learning methods where only synaptic weights change, structural adaptation changes the neuron's topology itself: soma size, dendrite length, and number of synapses on each dendrite.

### Core concepts

#### Learning task

The learning task consists of forming a response to a pattern represented as a **vector of single spikes with temporal coding**, where each vector component enters a separate dendrite of the neuron.

Temporal coding means numerical information is converted into a pulse sequence where the spike arrival time carries information about the value. For example, a larger value may be encoded by an earlier spike time.

#### Automatic neuron parameter selection

Depending on the given pattern, the algorithm automatically selects the following neuron model parameters:

1. **Soma size** (number of somatic membrane segments, N_s)
   - Affects the neuron's ability to integrate input signals
   - A larger soma provides more stable integration but may reduce sensitivity

2. **Dendrite length** (number of segments in each dendrite, N_d)
   - Determines signal propagation delay from synapse to soma
   - Longer dendrites better process temporal patterns
   - Each dendrite may have its own length

3. **Number of synapses on each dendrite** (N_syn)
   - Determines number of input channels for each dendrite
   - Affects the neuron's ability to distinguish different patterns

#### Pattern recognition criterion

The criterion for pattern recognition by a trained model is **output spike generation** by the neuron when the corresponding input pattern is presented.

#### Universal activation threshold value

Experimentally, a **universal neuron activation threshold value** was determined that does not depend on the size of the vector describing the input pattern. This important property allows using the same threshold for various classification tasks without adjustment.

### Structural adaptation algorithm

The structural adaptation process can be represented by the following stages:

**Structural adaptation process diagram:**

```mermaid
flowchart TD
    Start[Начало обучения] --> Analyze[Анализ входного паттерна]
    Analyze --> Determine[Определение необходимой структуры]
    Determine --> Create[Автоматическое создание/модификация структуры]
    Create --> Train[Обучение на заданном паттерне]
    Train --> Check{Нейрон генерирует спайк?}
    Check -->|Нет| Adjust[Корректировка структуры]
    Adjust --> Create
    Check -->|Да| End[Обучение завершено]
```

#### Stage 1: Input pattern analysis

- Determine pattern vector dimension (number of components)
- Analyze temporal coding (spike arrival times)
- Determine required number of dendrites (equal to pattern vector dimension)

#### Stage 2: Determine required structure

- Select initial neuron structure:
  - Number of somatic segments (usually starts at minimum)
  - Number of dendrites (equal to input pattern dimension)
  - Initial length of each dendrite (usually starts at 1 segment)
  - Number of synapses on each dendrite (usually starts at 1)

#### Stage 3: Automatic structure creation/modification

At this stage:
- Neuron structure is created with specified parameters
- Input generators are connected to corresponding synapses
- Membrane, channel, and synapse parameters are configured

#### Stage 4: Training on the given pattern

- Present input pattern to neuron
- Monitor neuron activity
- Measure membrane potential amplitude
- Check output spike generation

#### Stage 5: Structure adjustment (if necessary)

If the neuron does not generate a spike or generates it incorrectly:
- Increase dendrite length (to improve temporal processing)
- Change soma size (to change activation threshold)
- Add synapses (to strengthen input signal)
- Retrain with new structure

### Implementation in NMSDK

In NMSDK, structural adaptation is implemented through the `NNeuronTrainer` component (`Nmsdk-PulseLib` library).

#### Main NNeuronTrainer parameters

- `NumInputDendrite` — number of input dendrites (corresponds to input pattern dimension)
- `MaxDendriteLength` — maximum dendrite length
- `InputPattern` — input pattern matrix (temporal coding)
- `LTZThreshold` — low-threshold zone activation threshold
- `FixedLTZThreshold` — fixed activation threshold
- `TrainingLTZThreshold` — activation threshold during training
- `SpikesFrequency` — spike generation frequency
- `StructureBuildMode` — structure build mode (1 — structural adaptation)
- `CalculateMode` — calculation mode (defines learning algorithm)

#### Structural adaptation process in NNeuronTrainer

The `NNeuronTrainer` component implements structural adaptation as follows:

1. **Structure initialization:**
   - Create neuron with initial structure
   - Create pulse generators for each input dendrite
   - Connect generators to synapses on dendrites

2. **Iterative learning:**
   - At each iteration, membrane potential amplitude is measured
   - If amplitude increases when dendrite length increases — dendrite continues growing
   - If amplitude does not increase — dendrite is shortened or learning moves to next dendrite

3. **Dendrite synchronization:**
   - Algorithm seeks to synchronize times of maximum amplitude arrival on different dendrites
   - This ensures optimal temporal pattern processing

4. **Learning completion:**
   - Learning completes when all dendrites are synchronized and neuron generates a spike when pattern is presented

### Corresponding SpikeSamples configurations

The following configurations demonstrate structural adaptation:

- **`SpikeSamples/StructTrain/SpikeTrainer`** — basic structural learning
  - Demonstrates structural adaptation process on a simple pattern
  - Uses `NNeuronTrainer` component for automatic structure adjustment

- **`SpikeSamples/StructTrain/SpikeAnsTrainer`** — structural learning with answers
  - Extended version with ability to train on multiple patterns
  - Demonstrates forming responses to different input patterns

- **`SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM*`** — CSNM models with structural adaptation capability
  - Demonstrate structural adaptation on compartmental neuron models
  - Show influence of spatial parameters on adaptation process

### Parameters affecting structural adaptation

#### Maximum dendrite length (`MaxDendriteLength`)

- Limits maximum number of segments in each dendrite
- Affects maximum signal processing delay
- Recommended values: 10 to 100 segments depending on task

#### Maximum number of synapses

- Determined by neuron structure and membrane parameters
- Affects neuron's ability to integrate multiple inputs
- Usually set equal to number of input dendrites

#### Neuron activation threshold (`LTZThreshold`, `FixedLTZThreshold`)

- Universal threshold value independent of input pattern size
- Critically important for correct pattern recognition
- May be fixed or adaptive depending on learning mode

#### Temporal coding parameters

- `SpikesFrequency` — spike generation frequency of input generators
- `Delay` — training start delay relative to system start
- `InputPattern` — matrix of temporal delays for each pattern component

### Structural adaptation process diagram

**Structural adaptation process sequence diagram:**

```mermaid
sequenceDiagram
    participant Input as Входной паттерн
    participant Trainer as NNeuronTrainer
    participant Neuron as Нейрон
    participant Structure as Структура нейрона

    Input->>Trainer: Вектор спайков с временным кодированием
    Trainer->>Trainer: Анализ паттерна
    Trainer->>Structure: Определение начальной структуры
    Structure->>Neuron: Создание нейрона
    Trainer->>Neuron: Предъявление паттерна
    Neuron->>Trainer: Амплитуда потенциала
    Trainer->>Trainer: Проверка генерации спайка
    alt Спайк не генерируется
        Trainer->>Structure: Корректировка структуры
        Structure->>Neuron: Модификация нейрона
        Trainer->>Neuron: Повторное предъявление
    else Спайк генерируется
        Trainer->>Trainer: Обучение завершено
    end
```

### Influence of parameters on adaptation result

#### Soma size

- **Small soma** (1-2 segments):
  - High sensitivity to input signals
  - Fast spike generation
  - May be unstable with complex patterns

- **Large soma** (3+ segments):
  - More stable signal integration
  - Higher activation threshold
  - Better suited for complex patterns

#### Dendrite length

- **Short dendrites** (1-3 segments):
  - Minimal processing delay
  - Fast response to input signals
  - Limited temporal processing capability

- **Long dendrites** (10+ segments):
  - Significant processing delay
  - Ability to process complex temporal patterns
  - May require more training time

#### Number of synapses

- **One synapse per dendrite:**
  - Simple structure
  - Fast learning
  - Limited integration capability

- **Multiple synapses per dendrite:**
  - More complex structure
  - Improved signal integration
  - May require more training time

### Link to other learning methods

Structural adaptation can be combined with other learning methods:

- **STDP (Spike-Timing-Dependent Plasticity)** — synaptic weight changes depending on spike timing
- **Incremental learning** — learning on new samples without retraining on all previous ones
- **Classification** — applying structural adaptation to classification tasks

### Usage examples

#### Example 1: Simple pattern recognition

```cpp
// Создание NNeuronTrainer
NNeuronTrainer* trainer = CreateComponent<NNeuronTrainer>("Trainer");

// Настройка параметров
trainer->NumInputDendrite = 3;  // 3 компонента в паттерне
trainer->MaxDendriteLength = 50;
trainer->LTZThreshold = 0.0117;  // Универсальный порог
trainer->SpikesFrequency = 1.5;

// Задание входного паттерна (временные задержки в секундах)
MDMatrix<double> pattern;
pattern.Resize(3, 1);
pattern[0] = 0.0;   // Первый спайк в момент 0
pattern[1] = 0.1;   // Второй спайк через 0.1 сек
pattern[2] = 0.2;   // Третий спайк через 0.2 сек
trainer->InputPattern = pattern;

// Запуск обучения
trainer->IsNeedToTrain = true;
trainer->Reset();
```

#### Example 2: Training on multiple patterns

Structural adaptation can be used to train a neuron to recognize multiple different patterns, where each pattern corresponds to a separate class.

### Experimental results

According to publication [1]:

- Structural adaptation method is successfully applied for training the compartmental spiking neuron model
- Universal activation threshold value allows using the same threshold for different input pattern sizes
- Pattern recognition quality is comparable to classical learning methods
- Structural adaptation provides automatic selection of optimal neuron structure for each pattern

### Related materials

- [`IncrementalLearning.md`](IncrementalLearning.md) — incremental learning strategy using structural adaptation
- [`Classification.md`](Classification.md) — applying structural adaptation to classification tasks
- [`CSNM-Models.md`](CSNM-Models.md) — compartmental spiking neuron model description
- [`ImpulseProcessingModel.md`](ImpulseProcessingModel.md) — impulse stream processing model
- `Libraries/Nmsdk-PulseLib/Docs/Components/NNeuronTrainer.md` — NNeuronTrainer component documentation

## Literature

1. Korsakov, A., Astapova, L., Bakhshiev, A. The Method of Structural Adaptation of the Compartmental Spiking Neuron Model // Cyber-Physical Systems and Control II. CPS&C 2021. Lecture Notes in Networks and Systems, vol 460. Springer, Cham, 2023. [DOI](https://doi.org/10.1007/978-3-031-20875-1_51)

