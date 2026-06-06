## RU

## Серия экспериментов: реакции одиночных нейронов

Работы [26], [29], [30] описывают **базовую модель импульсного нейрона** с разбиением мембраны на участки (дендриты, сома, низкопороговая зона) и исследуют:

- влияние размера сомы и числа участков мембраны на паттерн ответа;
- временную и пространственную суммацию возбуждающих/тормозных входов;
- пейсмекерные нейроны и нейроны с несколькими устойчивыми состояниями мембранного потенциала.

### Соответствующие конфигурации SpikeSamples

Конфигурации в `Bin/Configs/SpikeSamples/NM-Neurons` иллюстрируют приведённые в статьях схемы:

- `NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
- `NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
- `NM-Neurons/NM-PN-03-Neuron-4M4D3St3In`
- `NM-Neurons/NM-PN-04-Neuron-3M1St3In3`
- `NM-Neurons/NM-PN-05-Neuron-4M1D3St3In`
- `NM-Neurons/NM-PN-06-Neuron-1M4D3St3In`
- `NM-Neurons/NM-PN-07-LtmNeuron-1M1St3In3`
- `NM-Neurons/NM-PN-08-LtmNeuron-3M1St3In3`
- `NM-Neurons/NM-PN-NeuronSizeActivity`
- `NM-Neurons/LIF-Neuron`

Для каждой из этих конфигураций подготовлен локальный `README.md` с описанием:

- структуры нейрона (количество участков мембраны в соме и дендритах, структура LT‑зоны);
- типов входов (дендритные, соматические, пейсмекерные), их временного профиля;
- типичных реакций (число импульсов в пачке, зависимость частоты от числа участков сомы, пейсмекерная активность и т.д.).

### Концептуальная схема модели одиночного импульсного нейрона

```mermaid
classDiagram
    class NPulseNeuron {
        +Membranes : NPulseMembraneCommon[*]
        +LTZone : NPulseLTZone
        +PosGenerator : NConstGenerator
        +NegGenerator : NConstGenerator
    }
    class NPulseMembraneCommon {
        +ExcitatoryChannels : NPulseChannelCommon[*]
        +InhibitoryChannels : NPulseChannelCommon[*]
        +ExcitatorySynapses : NPulseSynapseCommon[*]
        +InhibitorySynapses : NPulseSynapseCommon[*]
    }
    NPulseNeuron o-- NPulseMembraneCommon : membranes
    NPulseNeuron o-- NPulseLTZone : ltZone
    NPulseNeuron o-- NConstGenerator : posGenerator
    NPulseNeuron o-- NConstGenerator : negGenerator
    NPulseMembraneCommon *-- NPulseChannelCommon
    NPulseMembraneCommon *-- NPulseSynapseCommon
```

В терминах работ [26], [29]:

- участки мембраны `Mi` реализуются как экземпляры `NPulseMembrane` / `NPulseMembraneCommon`;
- пары ионных механизмов (деполяризация/гиперполяризация) представлены возбуждающими и тормозными каналами (`ExcChannel` / `InhChannel`) и синапсами;
- низкопороговая зона и генератор потенциала действия — `NPulseLTZone` и связанная с ней обратная связь.

### Типовые сценарии экспериментов

Для большинства конфигураций серии PN‑нейронов в SpikeSamples сценарии повторяют или близки к описанным в работах [26], [29]:

- **Одиночный возбуждающий импульс** на одном из входов:
  - анализируется задержка и затухание сигнала при распространении по дендриту;
  - сравниваются реакции при стимуляции дистальных и проксимальных участков.
- **Серии импульсов различной частоты**:
  - для маленьких нейронов наблюдаются пачки импульсов с убывающей частотой;
  - для крупных нейронов — одиночные импульсы или редкие разряды.
- **Модификация структуры сомы**:
  - увеличение числа соматических участков ведёт к снижению частоты и изменению числа импульсов в пачке (см. `NM-PN-NeuronSizeActivity`).

Подробное соответствие каждого эксперимента конкретной конфигурации приведено в локальных `README.md` в `SpikeSamples/NM-Neurons/...`.

## SpikeSamples — реакции одиночных нейронов

Этот документ связывает конфигурации из `Bin/Configs/SpikeSamples/NM-Neurons/*` с моделью нейрона, описанной в работах [26], [29].

### Базовая модель спайкового нейрона

В основе всех конфигураций группы `NM-Neurons` лежит модель нейрона, где:

- мембрана представлена набором участков, каждый из которых содержит пару ионных механизмов (деполяризующий и гиперполяризующий);
- синапсы преобразуют входные импульсы в аналоговые величины (концентрация медиатора) и через изменение проводимости управляют эффективностью ионных механизмов;
- генератор потенциала действия формирует спайки при превышении суммарным мембранным потенциалом порогового значения.

В PulseLib это реализовано через связку:

- `NPulseNeuron` / `NPulseNeuronCommon` — нейрон как сеть участков мембраны и LT‑зоны;
- `NPulseMembrane` / `NPulseMembraneCommon` — участки мембраны (сома и дендриты) с каналами и синапсами;
- `NPulseChannel` / `NPulseChannelCommon` — ионные механизмы (возбуждающие и тормозные);
- `NPulseSynapse` / `NPulseSynapseCommon` — химические синапсы;
- `NPulseLTZone` — низкопороговая зона (генератор спайков).

Схематично одиночный нейрон можно изобразить так:

```mermaid
classDiagram
    class NPulseNeuron {
        "Membranes[NPulseMembraneCommon*]"
        "LTZone[NPulseLTZone]"
        "PosGenerator[NConstGenerator]"
        "NegGenerator[NConstGenerator]"
    }
    class NPulseMembraneCommon {
        "ExcitatoryChannels[NPulseChannelCommon*]"
        "InhibitoryChannels[NPulseChannelCommon*]"
        "ExcitatorySynapses[NPulseSynapseCommon*]"
        "InhibitorySynapses[NPulseSynapseCommon*]"
    }
    NPulseNeuron o-- NPulseMembraneCommon : membranes
    NPulseNeuron o-- NPulseLTZone : ltZone
    NPulseNeuron o-- NConstGenerator : posGenerator
    NPulseNeuron o-- NConstGenerator : negGenerator
    NPulseMembraneCommon *-- NPulseChannelCommon
    NPulseMembraneCommon *-- NPulseSynapseCommon
```

### Конфигурации NM-PN-01..08 и размер сомы

Конфигурации:

- `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
- `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-03-Neuron-4M4D3St3In`
- `SpikeSamples/NM-Neurons/NM-PN-04-Neuron-3M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-05-Neuron-4M1D3St3In`
- `SpikeSamples/NM-Neurons/NM-PN-06-Neuron-1M4D3St3In`
- `SpikeSamples/NM-Neurons/NM-PN-07-LtmNeuron-1M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-08-LtmNeuron-3M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`

демонстрируют влияние:

- **размера сомы** (числа участков мембраны, охваченных обратной связью генератора);
- **структуры дендритов** (число и топология последовательных участков);
- **расположения синапсов** (на дендритах или на соме)

на частоту и структуру спайковых паттернов ответа на однотипную стимуляцию.

В работах [26], [29] показано, что:

- малый нейрон (малая сома) при стимуляции одиночными входами генерирует пачки импульсов с убывающей частотой;
- крупный нейрон (большая сома) при тех же параметрах модели даёт одиночные спайки или короткие пачки;
- перемещение синапса с дендрита на сому увеличивает эффективность возбуждения.

Эти эффекты воспроизводятся в `SpikeSamples/NM-Neurons/*` за счёт изменения структуры мембраны при сохранении одинаковых параметров ионных механизмов и синапсов (R0, RF, Cm, τs, τd, порог P и т.п.) в `Parameters.xml`.

### Конфигурация LIF-Neuron

Конфигурация:

- `SpikeSamples/NM-Neurons/LIF-Neuron`

представляет упрощённую модель нейрона типа Leaky Integrate-and-Fire (LIF), реализованную средствами PulseLib. Она служит сравнительным примером между:

- полнодетализированными моделями мембраны (множество участков с деполяризующими/гиперполяризующими ионными механизмами);
- и упрощённой моделью с одной интегрирующей ёмкостью и утечкой.

В `README.md` этой конфигурации рекомендуется фиксировать:

- диапазон входных частот;
- зависимость числа спайков от частоты стимуляции;
- отличие формы мембранного потенциала от более сложных моделей.

### Кабельные конфигурации CableNeuron*

Группа:

- `SpikeSamples/NM-Neurons/CableModel/CableNeuron*`

содержит кабельные (компартментные) модели, в том числе варианты CSNM (compartmental spiking neuron model), которые используются в более поздних публикациях [7], [4] и др. Здесь мембрана представлена как цепочка или дерево участков, моделирующих распространение потенциала по дендриту.

В `README.md` этих конфигураций приведены:

- схема ветвления дендритов (mermaid‑диаграмма);
- описание типов экспериментов: локальное возбуждение дистальных участков, одновременное возбуждение нескольких ветвей, влияние длины и диаметра на затухание и задержку;
- связь с результатами, показанными на графиках в работах [26], [29] (например, задержка и амплитуда ответа в зависимости от точки приложения стимула).

### Как использовать этот документ

- Для каждого каталога `SpikeSamples/NM-Neurons/*` создан свой `README.md`, который:
  - ссылается на данный обзор;
  - уточняет конкретный сценарий эксперимента для данного конфигурационного файла;
  - приводит краткие результаты и ожидаемые графики (словами).
- Этот файл служит **мостом** между теоретическим описанием в работах [26], [29], [30] и конкретной структурой моделей в `SpikeSamples`.

## Литература

1. [31] Воспроизведение реакций естественных нейронов как результат моделирования структурно-функциональных свойств мембраны и организации синаптического аппарата // Нейрокомпьютеры: разработка, применение, №7, 2012. – с.25-35. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=20:2012-07-19-04-53-55&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=17997711)

2. [31] Математическое моделирование процессов преобразования импульсных потоков в естественном нейроне // Нейрокомпьютеры: разработка, применение, №3, 2009. – с.71-80. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

3. Романов С.П., [27] Математическая модель биологического нейрона // Труды семинара "Моделирование неравновесных систем - 2000" (20-22 октября 2000 г. Красноярск)

4. Korsakov, A., Astapova, L., Bakhshiev, A. The Method of Structural Adaptation of the Compartmental Spiking Neuron Model // Cyber-Physical Systems and Control II. CPS&C 2021. Lecture Notes in Networks and Systems, vol 460. Springer, Cham, 2023. [DOI](https://doi.org/10.1007/978-3-031-20875-1_51)

5. Bakhshiev A. V., Demcheva A. A. Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310. [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310)

---

## EN

## Experiment series: single-neuron responses

Works [26], [29], [30] describe the **basic impulse neuron model** with membrane divided into segments (dendrites, soma, low-threshold zone) and investigate:

- influence of soma size and number of membrane segments on response pattern;
- temporal and spatial summation of excitatory/inhibitory inputs;
- pacemaker neurons and neurons with multiple stable membrane potential states.

### Corresponding SpikeSamples configurations

Configurations in `Bin/Configs/SpikeSamples/NM-Neurons` illustrate the schemes presented in the articles:

- `NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
- `NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
- `NM-Neurons/NM-PN-03-Neuron-4M4D3St3In`
- `NM-Neurons/NM-PN-04-Neuron-3M1St3In3`
- `NM-Neurons/NM-PN-05-Neuron-4M1D3St3In`
- `NM-Neurons/NM-PN-06-Neuron-1M4D3St3In`
- `NM-Neurons/NM-PN-07-LtmNeuron-1M1St3In3`
- `NM-Neurons/NM-PN-08-LtmNeuron-3M1St3In3`
- `NM-Neurons/NM-PN-NeuronSizeActivity`
- `NM-Neurons/LIF-Neuron`

Each configuration has a local `README.md` describing:

- neuron structure (number of membrane segments in soma and dendrites, LT-zone structure);
- input types (dendritic, somatic, pacemaker), their temporal profile;
- typical responses (number of impulses in a burst, frequency dependence on soma segment count, pacemaker activity, etc.).

### Conceptual diagram of the single impulse neuron model

```mermaid
classDiagram
    class NPulseNeuron {
        +Membranes : NPulseMembraneCommon[*]
        +LTZone : NPulseLTZone
        +PosGenerator : NConstGenerator
        +NegGenerator : NConstGenerator
    }
    class NPulseMembraneCommon {
        +ExcitatoryChannels : NPulseChannelCommon[*]
        +InhibitoryChannels : NPulseChannelCommon[*]
        +ExcitatorySynapses : NPulseSynapseCommon[*]
        +InhibitorySynapses : NPulseSynapseCommon[*]
    }
    NPulseNeuron o-- NPulseMembraneCommon : membranes
    NPulseNeuron o-- NPulseLTZone : ltZone
    NPulseNeuron o-- NConstGenerator : posGenerator
    NPulseNeuron o-- NConstGenerator : negGenerator
    NPulseMembraneCommon *-- NPulseChannelCommon
    NPulseMembraneCommon *-- NPulseSynapseCommon
```

In terms of works [26], [29]:

- membrane segments `Mi` are implemented as instances of `NPulseMembrane` / `NPulseMembraneCommon`;
- pairs of ionic mechanisms (depolarization/hyperpolarization) are represented by excitatory and inhibitory channels (`ExcChannel` / `InhChannel`) and synapses;
- low-threshold zone and action potential generator — `NPulseLTZone` and associated feedback.

### Typical experiment scenarios

For most PN-neuron configurations in SpikeSamples, scenarios repeat or are close to those described in works [26], [29]:

- **Single excitatory pulse** on one input:
  - signal delay and attenuation during dendritic propagation are analyzed;
  - responses to distal vs. proximal segment stimulation are compared.
- **Pulse series at different frequencies**:
  - small neurons show impulse bursts with decreasing frequency;
  - large neurons — single impulses or rare discharges.
- **Soma structure modification**:
  - increasing somatic segment count leads to reduced frequency and changed number of impulses in a burst (see `NM-PN-NeuronSizeActivity`).

Detailed correspondence of each experiment to a specific configuration is given in local `README.md` files in `SpikeSamples/NM-Neurons/...`.

## SpikeSamples — single-neuron responses

This document links configurations from `Bin/Configs/SpikeSamples/NM-Neurons/*` to the neuron model described in works [26], [29].

### Basic spiking neuron model

All configurations in the `NM-Neurons` group are based on a neuron model where:

- membrane is represented by a set of segments, each containing a pair of ionic mechanisms (depolarizing and hyperpolarizing);
- synapses convert input impulses into analog quantities (mediator concentration) and control ionic mechanism efficacy through conductance changes;
- action potential generator forms spikes when total membrane potential exceeds threshold.

In PulseLib this is implemented through:

- `NPulseNeuron` / `NPulseNeuronCommon` — neuron as a network of membrane segments and LT-zone;
- `NPulseMembrane` / `NPulseMembraneCommon` — membrane segments (soma and dendrites) with channels and synapses;
- `NPulseChannel` / `NPulseChannelCommon` — ionic mechanisms (excitatory and inhibitory);
- `NPulseSynapse` / `NPulseSynapseCommon` — chemical synapses;
- `NPulseLTZone` — low-threshold zone (spike generator).

A single neuron can be schematically represented as:

```mermaid
classDiagram
    class NPulseNeuron {
        "Membranes[NPulseMembraneCommon*]"
        "LTZone[NPulseLTZone]"
        "PosGenerator[NConstGenerator]"
        "NegGenerator[NConstGenerator]"
    }
    class NPulseMembraneCommon {
        "ExcitatoryChannels[NPulseChannelCommon*]"
        "InhibitoryChannels[NPulseChannelCommon*]"
        "ExcitatorySynapses[NPulseSynapseCommon*]"
        "InhibitorySynapses[NPulseSynapseCommon*]"
    }
    NPulseNeuron o-- NPulseMembraneCommon : membranes
    NPulseNeuron o-- NPulseLTZone : ltZone
    NPulseNeuron o-- NConstGenerator : posGenerator
    NPulseNeuron o-- NConstGenerator : negGenerator
    NPulseMembraneCommon *-- NPulseChannelCommon
    NPulseMembraneCommon *-- NPulseSynapseCommon
```

### NM-PN-01..08 configurations and soma size

Configurations:

- `SpikeSamples/NM-Neurons/NM-PN-01-Neuron-1M1St1In1`
- `SpikeSamples/NM-Neurons/NM-PN-02-Neuron-1M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-03-Neuron-4M4D3St3In`
- `SpikeSamples/NM-Neurons/NM-PN-04-Neuron-3M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-05-Neuron-4M1D3St3In`
- `SpikeSamples/NM-Neurons/NM-PN-06-Neuron-1M4D3St3In`
- `SpikeSamples/NM-Neurons/NM-PN-07-LtmNeuron-1M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-08-LtmNeuron-3M1St3In3`
- `SpikeSamples/NM-Neurons/NM-PN-NeuronSizeActivity`

demonstrate the influence of:

- **soma size** (number of membrane segments covered by generator feedback);
- **dendrite structure** (number and topology of sequential segments);
- **synapse placement** (on dendrites or soma)

on frequency and structure of spike response patterns to uniform stimulation.

Works [26], [29] show that:

- a small neuron (small soma) stimulated by single inputs generates impulse bursts with decreasing frequency;
- a large neuron (large soma) with the same model parameters produces single spikes or short bursts;
- moving a synapse from dendrite to soma increases excitation efficacy.

These effects are reproduced in `SpikeSamples/NM-Neurons/*` by changing membrane structure while keeping identical ionic mechanism and synapse parameters (R0, RF, Cm, τs, τd, threshold P, etc.) in `Parameters.xml`.

### LIF-Neuron configuration

Configuration:

- `SpikeSamples/NM-Neurons/LIF-Neuron`

represents a simplified Leaky Integrate-and-Fire (LIF) neuron model implemented with PulseLib. It serves as a comparative example between:

- fully detailed membrane models (multiple segments with depolarizing/hyperpolarizing ionic mechanisms);
- and a simplified model with a single integrating capacitance and leak.

`README.md` for this configuration should record:

- input frequency range;
- dependence of spike count on stimulation frequency;
- difference in membrane potential shape from more complex models.

### CableNeuron* cable configurations

Group:

- `SpikeSamples/NM-Neurons/CableModel/CableNeuron*`

contains cable (compartmental) models, including CSNM (compartmental spiking neuron model) variants used in later publications [7], [4], etc. Here membrane is represented as a chain or tree of segments modeling potential propagation along dendrites.

`README.md` for these configurations includes:

- dendrite branching diagram (mermaid);
- experiment type descriptions: local distal segment excitation, simultaneous excitation of multiple branches, influence of length and diameter on attenuation and delay;
- link to results shown in graphs in works [26], [29] (e.g., response delay and amplitude depending on stimulus application point).

### How to use this document

- For each `SpikeSamples/NM-Neurons/*` directory, a local `README.md` has been created that:
  - references this overview;
  - specifies the concrete experiment scenario for the configuration file;
  - provides brief results and expected graphs (in words).
- This file serves as a **bridge** between theoretical description in works [26], [29], [30] and the concrete model structure in `SpikeSamples`.

## Literature

1. [31] Reproducing natural neuron responses as a result of modeling structural-functional properties of the membrane and synaptic apparatus organization // Neurocomputers: Development, Application, No. 7, 2012. – pp. 25-35. [online](https://neuromodeler.ru/index.php?option=com_content&view=article&id=20:2012-07-19-04-53-55&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=17997711)

2. [31] Mathematical modeling of impulse stream processing in a natural neuron // Neurocomputers: Development, Application, No. 3, 2009. – pp. 71-80. [online](https://neuromodeler.ru/index.php?option=com_content&view=article&id=24:2012-11-07-16-42-21&catid=67&lang=ru&Itemid=676) | [elibrary](https://www.elibrary.ru/item.asp?id=13070281)

3. Romanov S. P., [27] Mathematical model of a biological neuron // Proceedings of the seminar "Modeling Non-Equilibrium Systems - 2000" (October 20-22, 2000, Krasnoyarsk)

4. Korsakov, A., Astapova, L., Bakhshiev, A. The Method of Structural Adaptation of the Compartmental Spiking Neuron Model // Cyber-Physical Systems and Control II. CPS&C 2021. Lecture Notes in Networks and Systems, vol 460. Springer, Cham, 2023. [DOI](https://doi.org/10.1007/978-3-031-20875-1_51)

5. Bakhshiev A. V., Demcheva A. A. Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310. [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310)

