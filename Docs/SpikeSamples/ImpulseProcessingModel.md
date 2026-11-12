## RU

## Модель преобразования импульсных потоков в естественном нейроне

В работе [2] вводится детальная математическая модель:

- синапса (выделение и распад медиатора, пресинаптическое торможение);
- ионного механизма мембраны (апериодическое звено с переменной постоянной времени);
- генератора потенциала действия с обратной связью на соматические участки.

В NMSDK эта модель реализована через компоненты PulseLib (`NPulseSynapse`, `NPulseChannel`, `NPulseMembrane`, `NPulseNeuron`), а в SpikeSamples представлены конфигурации, демонстрирующие поведение такой модели в разных режимах.

### Соответствующие конфигурации SpikeSamples

Основные конфигурации, иллюстрирующие модель преобразования импульсных потоков:

- `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
- `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-03/04/05/06-Neuron-*`
- `SpikeSamples/NM-Neurons/NM-PN-07/08-LtmNeuron-*`
- `SpikeSamples/NM-Neurons/LIF-Neuron` (сравнительная упрощённая модель)
- `SpikeSamples/Memory/MEM-OneNeuron3`, `SpikeSamples/Memory/MEM-SimpleMemory2`
- `SpikeSamples/STDP/STDP-Simple-01`

Каждая из них использует один и тот же набор базовых компонент PulseLib, отличаясь:

- структурой сети (число участков мембраны, организация синапсов);
- параметрами синапсов и каналов (временные константы, сопротивления, веса);
- режимами стимуляции (частота входных импульсов, сложные паттерны).

### Функциональная схема потока сигналов

```mermaid
flowchart TD
    afferentInput["AfferentInput (импульсный поток)"] --> synapse["NPulseSynapse (выделение/распад медиатора)"]
    synapse --> channel["NPulseChannel (ионный механизм)"]
    channel --> membrane["NPulseMembrane (участок мембраны)"]
    membrane --> ltZone["NPulseLTZone (низкопороговая зона)"]
    ltZone --> neuronOutput["Выход нейрона (импульсный поток)"]
    neuronOutput --> feedback["Feedback (перезаряд сомы)"]
    feedback --> membrane
```

В терминах работы [2]:

- **входной импульсный поток** — последовательность дискретных импульсов на синапсах;
- **синапс** интегрирует импульсы через параметры `PulseAmplitude`, `SecretionTC`, `DissociationTC`, с возможным пресинаптическим торможением (`InhibitionCoeff`, `UsePresynapticInhibition`);
- **ионный механизм** реализует инерционное звено с постоянными `Rm`, `Cm`, `RF`, параметрами `Capacity`, `Resistance`, `FBResistance`;
- **генератор потенциала действия** формирует выходные импульсы при превышении порога `P` и запускает перезарядку мембраны.

### Типичные эффекты, демонстрируемые в SpikeSamples

- **Преобразование частоты**: зависимость частоты выходных разрядов от частоты входного потока (графики типа рис. 14 в работе [2]); реализуется в PN‑конфигурациях и памяти.
- **Пресинаптическое торможение**: снижение эффективности синапса при слишком высокой частоте входа (эффект «защиты от насыщения»), используемый, в частности, для стабилизации активности в кольцевых структурах и моторных контурах.
- **Зависимость от параметров мембраны**: конфигурации `CableModel/*` и `NM-PN-*` позволяют варьировать R, C, пороги и глубину ОС, меняя скорость и устойчивость реакций.

Подробное описание каждого конкретного эксперимента и соответствия параметров теоретической модели приведено в `README.md` в каждой папке `SpikeSamples/...`.

## Литература

1. [31] Математическое моделирование процессов преобразования импульсных потоков в естественном нейроне // Нейрокомпьютеры: разработка, применение, №3, 2009. – с.71-80. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

## SpikeSamples — модель преобразования импульсных потоков

Этот документ основан на работе [2] и описывает, как её идеи реализованы в конфигурациях `Bin/Configs/SpikeSamples`.

### Функциональные блоки модели

В статье выделяются три ключевых уровня:

1. **Синапс** — преобразует входной дискретный поток импульсов в аналоговую величину (концентрация медиатора, проводимость), учитывая:
   - различные постоянные времени выделения и распада медиатора;
   - эффект пресинаптического торможения при высоких частотах входа.
2. **Ионные механизмы мембраны** — пара деполяризующего и гиперполяризующего каналов:
   - описываются эквивалентной RC‑схемой с сопротивлениями R0, RF и ёмкостью Cm;
   - суммарный вклад ионных механизмов определяет локальный вклад участка мембраны в внутриклеточный потенциал.
3. **Генератор потенциала действия** — формирует спайк при превышении порога P и замыкает контур обратной связи, перезаряжая мембрану.

В PulseLib эти блоки реализованы как:

- `NPulseSynapse` / `NPulseSynapseCommon` — модель синапса, параметры:
  - `PulseAmplitude`, `SecretionTC`, `DissociationTC`, `InhibitionCoeff`, `Resistance`, `UsePresynapticInhibition` и др.;
- `NPulseChannel` / `NPulseChannelCommon` — ионный механизм:
  - `Capacity`, `Resistance`, `FBResistance`, `RestingResistance`, `Type` (возбуждающий/тормозный);
- `NPulseMembrane` / `NPulseMembraneCommon` — агрегирует каналы и синапсы, суммирует их вклад в `SumPotential` и реализует обратную связь через `Feedback`;
- `NPulseLTZone` — низкопороговая зона (генератор спайков).

### Конфигурации SpikeSamples, иллюстрирующие преобразование импульсных потоков

Ключевые конфигурации:

- одиночные нейроны с различной структурой мембраны:
  - `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
  - `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
  - `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`
- примеры памяти и условных рефлексов:
  - `SpikeSamples/Memory/MEM-OneNeuron3`
  - `SpikeSamples/Memory/MEM-SimpleMemory2`
  - `SpikeSamples/Memory/SpikeAssociationPlus`
  - `SpikeSamples/Memory/SpikeConditionalReflex`
- тренировка и структурное обучение:
  - `SpikeSamples/StructTrain/SpikeTrainer`
  - `SpikeSamples/StructTrain/SpikeAnsTrainer`
- пластиность и STDP:
  - `SpikeSamples/STDP/STDP-Simple-01`

### Поток сигналов в типичной конфигурации

Обобщённо поток сигналов можно представить так:

```mermaid
flowchart TD
    afferentInput["Входной импульсный поток"] --> synapse["NPulseSynapse\n(SecretionTC, DissociationTC, InhibitionCoeff)"]
    synapse --> channel["NPulseChannel\n(Capacity, Resistance, Type)"]
    channel --> membrane["NPulseMembrane\n(SumPotential, Feedback)"]
    membrane --> ltZone["NPulseLTZone\n(Threshold P)"]
    ltZone --> neuronOutput["Выходной спайковый поток"]
    neuronOutput -->|обратная связь| membrane
```

Разные конфигурации `SpikeSamples` реализуют различные комбинации:

- числа синапсов и их пространственного расположения на мембране;
- частоты и паттернов входных воздействий;
- структурной организации (количество участков сомы и дендритов).

### Примеры экспериментов из SpikeSamples

1. **Частотные характеристики одиночного нейрона** (нейрон N1/N2 в статье):
   - Конфигурации `NM-PN-*` и `NM-PN-NeuronSizeActivity` используют одинаковые параметры моделей, но разное число участков сомы и дендритов.
   - В `README.md` для этих конфигураций должны быть:
     - зависимость частоты выходных спайков от частоты входа;
     - различия между малым и крупным нейронами.

2. **Эффект пресинаптического торможения**:
   - Конфигурации в группах `Memory` и `StructTrain` используют высокочастотную стимуляцию некоторых входов и демонстрируют:
     - снижение эффективности синаптического влияния при превышении критической частоты;
     - защиту сети от насыщения за счёт уменьшения вклада аномально активных входов.

3. **Формирование условного рефлекса**:
   - `SpikeSamples/Memory/SpikeConditionalReflex` и `SpikeSamples/Memory/SpikeAssociationPlus` иллюстрируют,
     как при одновременной или последовательной активации разных входов закрепляется ассоциация между паттернами,
     и как изменяется характер ответов нейрона/сети.

4. **Структурная адаптация и обучение**:
   - Конфигурации `SpikeSamples/StructTrain/*` демонстрируют:
     - изменение структуры сети (число и расположение синапсов, возможные изменения связей) под действием тренировочных паттернов;
     - переход от ручной настройки параметров к самоорганизующемуся описанию связей.

5. **STDP и пластичность**:
   - `SpikeSamples/STDP/STDP-Simple-01` показывает,
     как зависимость изменения веса синапса от относительного времени пресинаптического и постсинаптического спайка
     может быть реализована средствами PulseLib и использована для обучения сети.

### Рекомендации по README для соответствующих конфигураций

Для каждой конфигурации из перечисленных групп `README.md` содержит:

- чёткое текстовое описание:
  - какие входные стимулы используются (частота, длительность, паттерн);
  - какие выходные характеристики анализируются (частота, число спайков в пачке, наличие пресинаптического торможения и т.п.);
- отсылки к соответствующим разделам статьи (рисунки, графики);
- пояснение, какие параметры в `Parameters.xml` критичны для результата (τs, τd, R0, RF, Cm, порог P, глубина обратной связи и т.п.).

Этот документ служит «каркасом»; детализация по каждой конфигурации фиксируется в её локальном `README.md`.

---

## EN

## Impulse stream processing model in a natural neuron

Work [2] introduces a detailed mathematical model of:

- the synapse (mediator secretion and decay, presynaptic inhibition);
- the membrane ionic mechanism (aperiodic element with variable time constant);
- the action potential generator with feedback to somatic segments.

In NMSDK this model is implemented through PulseLib components (`NPulseSynapse`, `NPulseChannel`, `NPulseMembrane`, `NPulseNeuron`), and SpikeSamples contains configurations demonstrating the behavior of such a model in different modes.

### Corresponding SpikeSamples configurations

Main configurations illustrating the impulse stream processing model:

- `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
- `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-03/04/05/06-Neuron-*`
- `SpikeSamples/NM-Neurons/NM-PN-07/08-LtmNeuron-*`
- `SpikeSamples/NM-Neurons/LIF-Neuron` (comparative simplified model)
- `SpikeSamples/Memory/MEM-OneNeuron3`, `SpikeSamples/Memory/MEM-SimpleMemory2`
- `SpikeSamples/STDP/STDP-Simple-01`

Each uses the same set of basic PulseLib components, differing in:

- network structure (number of membrane segments, synapse organization);
- synapse and channel parameters (time constants, resistances, weights);
- stimulation modes (input pulse frequency, complex patterns).

### Functional signal flow diagram

```mermaid
flowchart TD
    afferentInput["AfferentInput (импульсный поток)"] --> synapse["NPulseSynapse (выделение/распад медиатора)"]
    synapse --> channel["NPulseChannel (ионный механизм)"]
    channel --> membrane["NPulseMembrane (участок мембраны)"]
    membrane --> ltZone["NPulseLTZone (низкопороговая зона)"]
    ltZone --> neuronOutput["Выход нейрона (импульсный поток)"]
    neuronOutput --> feedback["Feedback (перезаряд сомы)"]
    feedback --> membrane
```

In terms of work [2]:

- **input impulse stream** — a sequence of discrete pulses at synapses;
- **synapse** integrates pulses through parameters `PulseAmplitude`, `SecretionTC`, `DissociationTC`, with possible presynaptic inhibition (`InhibitionCoeff`, `UsePresynapticInhibition`);
- **ionic mechanism** implements an inertial element with constants `Rm`, `Cm`, `RF`, parameters `Capacity`, `Resistance`, `FBResistance`;
- **action potential generator** forms output pulses when threshold `P` is exceeded and triggers membrane recharge.

### Typical effects demonstrated in SpikeSamples

- **Frequency conversion**: dependence of output discharge frequency on input stream frequency (graphs like Fig. 14 in work [2]); implemented in PN configurations and memory.
- **Presynaptic inhibition**: reduced synaptic efficacy at excessively high input frequency (saturation protection effect), used in particular to stabilize activity in ring structures and motor circuits.
- **Dependence on membrane parameters**: `CableModel/*` and `NM-PN-*` configurations allow varying R, C, thresholds, and feedback depth, changing reaction speed and stability.

Detailed description of each specific experiment and correspondence of parameters to the theoretical model is given in `README.md` in each `SpikeSamples/...` folder.

## Literature

1. [31] Mathematical modeling of impulse stream processing in a natural neuron // Neurocomputers: Development, Application, No. 3, 2009. – pp. 71-80. [online](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

## SpikeSamples — impulse stream processing model

This document is based on work [2] and describes how its ideas are implemented in `Bin/Configs/SpikeSamples` configurations.

### Functional blocks of the model

The article distinguishes three key levels:

1. **Synapse** — converts the input discrete pulse stream into an analog quantity (mediator concentration, conductance), accounting for:
   - different secretion and decay time constants;
   - presynaptic inhibition effect at high input frequencies.
2. **Membrane ionic mechanisms** — a pair of depolarizing and hyperpolarizing channels:
   - described by an equivalent RC circuit with resistances R0, RF and capacitance Cm;
   - the total contribution of ionic mechanisms determines the local contribution of a membrane segment to intracellular potential.
3. **Action potential generator** — forms a spike when threshold P is exceeded and closes the feedback loop, recharging the membrane.

In PulseLib these blocks are implemented as:

- `NPulseSynapse` / `NPulseSynapseCommon` — synapse model, parameters:
  - `PulseAmplitude`, `SecretionTC`, `DissociationTC`, `InhibitionCoeff`, `Resistance`, `UsePresynapticInhibition`, etc.;
- `NPulseChannel` / `NPulseChannelCommon` — ionic mechanism:
  - `Capacity`, `Resistance`, `FBResistance`, `RestingResistance`, `Type` (excitatory/inhibitory);
- `NPulseMembrane` / `NPulseMembraneCommon` — aggregates channels and synapses, sums their contribution to `SumPotential` and implements feedback through `Feedback`;
- `NPulseLTZone` — low-threshold zone (spike generator).

### SpikeSamples configurations illustrating impulse stream processing

Key configurations:

- single neurons with different membrane structures:
  - `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
  - `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
  - `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`
- memory and conditioned reflex examples:
  - `SpikeSamples/Memory/MEM-OneNeuron3`
  - `SpikeSamples/Memory/MEM-SimpleMemory2`
  - `SpikeSamples/Memory/SpikeAssociationPlus`
  - `SpikeSamples/Memory/SpikeConditionalReflex`
- training and structural learning:
  - `SpikeSamples/StructTrain/SpikeTrainer`
  - `SpikeSamples/StructTrain/SpikeAnsTrainer`
- plasticity and STDP:
  - `SpikeSamples/STDP/STDP-Simple-01`

### Signal flow in a typical configuration

The signal flow can be represented as follows:

```mermaid
flowchart TD
    afferentInput["Входной импульсный поток"] --> synapse["NPulseSynapse
(SecretionTC, DissociationTC, InhibitionCoeff)"]
    synapse --> channel["NPulseChannel
(Capacity, Resistance, Type)"]
    channel --> membrane["NPulseMembrane
(SumPotential, Feedback)"]
    membrane --> ltZone["NPulseLTZone
(Threshold P)"]
    ltZone --> neuronOutput["Output spikeовый поток"]
    neuronOutput -->|обратная связь| membrane
```

Different `SpikeSamples` configurations implement various combinations of:

- number of synapses and their spatial placement on the membrane;
- frequency and patterns of input stimulation;
- structural organization (number of soma and dendrite segments).

### Experiment examples from SpikeSamples

1. **Frequency characteristics of a single neuron** (neurons N1/N2 in the article):
   - `NM-PN-*` and `NM-PN-NeuronSizeActivity` configurations use identical model parameters but different numbers of soma and dendrite segments.
   - `README.md` for these configurations should include:
     - dependence of output spike frequency on input frequency;
     - differences between small and large neurons.

2. **Presynaptic inhibition effect**:
   - Configurations in `Memory` and `StructTrain` groups use high-frequency stimulation of some inputs and demonstrate:
     - reduced synaptic influence when critical frequency is exceeded;
     - network saturation protection by reducing contribution of abnormally active inputs.

3. **Conditioned reflex formation**:
   - `SpikeSamples/Memory/SpikeConditionalReflex` and `SpikeSamples/Memory/SpikeAssociationPlus` illustrate
     how simultaneous or sequential activation of different inputs consolidates association between patterns,
     and how the character of neuron/network responses changes.

4. **Structural adaptation and learning**:
   - `SpikeSamples/StructTrain/*` configurations demonstrate:
     - network structure changes (number and placement of synapses, possible connection changes) under training patterns;
     - transition from manual parameter tuning to self-organizing connection description.

5. **STDP and plasticity**:
   - `SpikeSamples/STDP/STDP-Simple-01` shows
     how dependence of synaptic weight change on relative timing of pre- and postsynaptic spikes
     can be implemented with PulseLib and used for network training.

### README recommendations for corresponding configurations

For each configuration in the listed groups, `README.md` should contain:

- clear textual description of:
  - input stimuli used (frequency, duration, pattern);
  - output characteristics analyzed (frequency, number of spikes in a burst, presence of presynaptic inhibition, etc.);
- references to corresponding article sections (figures, graphs);
- explanation of which parameters in `Parameters.xml` are critical for the result (τs, τd, R0, RF, Cm, threshold P, feedback depth, etc.).

This document serves as a framework; details for each configuration are recorded in its local `README.md`.
