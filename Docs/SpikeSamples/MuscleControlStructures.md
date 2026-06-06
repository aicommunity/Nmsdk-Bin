## RU

## Нейронные структуры управления мышечным сокращением

В работе [1] рассматриваются:

- афферентные нейроны (каналы Ia, II, Ib);
- мотонейроны, клетки Реншоу, тормозные интернейроны;
- способы регуляции силы мышечного сокращения (частота разрядов, количество активных мотонейронов);
- рефлекторные и возвратные контуры в спинном мозге.

### Соответствующие конфигурации SpikeSamples

В `Bin/Configs/SpikeSamples` этим темам соответствуют, прежде всего:

- `MC0-RCN/MC-RCN-00-*/...`
  — рефлекторные контуры (Ring/Reflex Control Networks) с мотонейронами, реншовскими клетками, ветвлением афферентных путей.
- `MC0-RCN/MC-RCN-01-NumMotionElements-Pendulum/...`
  — влияние количества двигательных элементов и структуры обратных связей на динамику маятниковой модели.
- `MC1-PCN/*` (`MotionControl_Test`, `MultiPositionControl_*`, `NewPositionControl_Test`)
  — более прикладные схемы позиционного управления с участием спайковых сетей.
- `EyeRetina/EyeRetinaMuscle`
  — пример зрительно‑двигательного контура «ретина → сеть обработки → мышца».

Каждая из этих конфигураций снабжена `Description.rtf` с подробным описанием экспериментов; новая документация в локальных `README.md` консолидирует эти описания в Markdown‑формате и дополняет их схемами (mermaid‑диаграммы), статусом валидации и ссылками на профильные статьи.

### Обобщённая схема контура мотонейрон – клетка Реншоу

```mermaid
flowchart LR
    afferentIa["AfferentNeuron_Ia"] --> motoneuron["Motoneuron"]
    motoneuron --> muscle["Muscle"]
    motoneuron --> renshaw["RenshawCell"]
    renshaw --> motoneuron
    renshaw --> inhInterneuron["InhibitoryInterneuron"]
    inhInterneuron --> antagonistMN["AntagonistMotoneuron"]
```

Ключевые эффекты, которые демонстрируются в SpikeSamples‑конфигурациях:

- **возвратное торможение** мотонейронов через клетки Реншоу;
- **взаимное торможение антагонистических мышц** через интернейроны;
- **зависимость частоты разрядов мотонейронов** от частоты афферентного входа и параметров тормозных контуров.

### Связь с конкретными конфигурациями

- `MC0-RCN/*`
  — ближе всего к схемам, описанным в статье: явная реализация афферентных каналов, мотонейронов, реншовских клеток и мышечных моделей (маятник / DC‑двигатель).
- `MC1-PCN/*`
  — использует схожие принципы на более высоком уровне (позиционное управление), но может рассматриваться как развитие базовых RCN‑схем.
- `EyeRetina/EyeRetinaMuscle`
  — добавляет сенсорный (зрительный) фронт‑энд и связывает его с моторным контуром.

Для каждого из этих наборов конфигураций подготовлены локальные `README.md`, где:

- описывается биологическая мотивация эксперимента;
- приводится структура сети (включая mermaid‑диаграммы для конкретных вариантов);
- перечисляются сценарии стимуляции и качественные результаты (например, стабилизация частоты разрядов при росте частоты входа, согласованное управление несколькими мышцами и т.п.).

## SpikeSamples — нейронные структуры управления мышечным сокращением

Этот документ основан на работе [1] и описывает, как соответствующие схемы реализованы в конфигурациях `Bin/Configs/SpikeSamples`.

### Биологический прототип

Рассматривается классическая схема спинальных нервных структур:

- афферентные нейроны (Ia, II, Ib), передающие информацию от мышечных веретён и органов Гольджи;
- мотонейроны, иннервирующие мышечные волокна;
- тормозные интернейроны;
- клетки Реншоу, обеспечивающие возвратное торможение мотонейронов;
- мышца как объект управления.

Сеть реализует:

- моно- и дисинаптические рефлекторные дуги;
- возвратное торможение;
- альфа‑гамма‑координацию при наличии дополнительных управляющих входов.

### Конфигурации SpikeSamples, связанные с управлением движением

Основные конфигурации:

- `SpikeSamples/MC1-PCN/MotionControl_Test`
- `SpikeSamples/MC1-PCN/NewPositionControl_Test`
- `SpikeSamples/MC1-PCN/MultiPositionControl_SimpleTest`
- `SpikeSamples/MC1-PCN/MultiPositionControl_SoloModeTest`
- `SpikeSamples/MC1-PCN/MultiPositionControl_TaskTest`
- `SpikeSamples/MC1-PCN/MultiPositionControl_RememberStateTest`
- `SpikeSamples/MC1-PCN/MultiPC_TwoLevelsTask`

Дополнительно, некоторые аспекты афферентных каналов и сенсорики демонстрируются в:

- `SpikeSamples/NM-AfferentNeurons/*`
- `SpikeSamples/NeuralElements/NReceptor`

Каждая из конфигураций MC1‑PCN моделирует:

- подмножество описанной в статье схемы;
- конкретный сценарий управления (позиционное, многопозиционное, с запоминанием состояний, с многоуровневой иерархией и т.п.).

### Схема мотонейрон — клетка Реншоу (возвратное торможение)

Ключевой мотив статьи — возвратное торможение мотонейрона через клетку Реншоу, стабилизирующее частоту его разрядов при возрастании входной частоты.

Схематично это можно изобразить так:

```mermaid
flowchart TD
    afferentIa["Afferent Ia/II\n(SpikeSamples/NM-AfferentNeurons)"] --> motoneuron["Motoneuron\n(NPulseNeuron)"]
    motoneuron --> muscle["Muscle\n(модель мышцы или выходной канал)"]
    motoneuron --> renshaw["Renshaw cell\n(NPulseNeuron)"]
    renshaw -->|тормозное влияние| motoneuron
```

В конфигурациях MC1‑PCN:

- роль афферентных входов могут играть генераторы спайков или афферентные нейроны (`NM-AN-*`);
- мотонейроны и клетки Реншоу реализованы на базе `NPulseNeuron` с разной структурой мембраны и входными связями;
- мышца представлена либо агрегированным выходом сети, либо отдельной подсистемой (в некоторых конфигурациях).

### Примеры сценариев из MC1-PCN

1. **MotionControl_Test / NewPositionControl_Test**
   - демонстрируют базовый контур «афферентация → мотонейрон → мышца» с обратной связью по положению;
   - в `README.md` следует описать:
     - какие каналы афферентной обратной связи используются;
     - как меняется паттерн разрядов мотонейронов при различных траекториях задания;
     - как это соотносится с результатами статьи (стабилизация, динамика выхода).

2. **MultiPositionControl_* и MultiPC_TwoLevelsTask**
   - расширяют базовую схему до многопозицонного и/или иерархического управления:
     - несколько мотонейронов и мышц‑эффекторов;
     - распределение ролей между уровнями (локальные и глобальные петли обратной связи);
   - в `README.md` важно зафиксировать:
     - карту нейронных блоков (какой конфигурационный узел соответствует какому элементу схемы из статьи);
     - сценарии: смена целевых позиций, память о предыдущем положении, взаимодействие антагонистических мышц.

3. **Связь с афферентными конфигурациями**
   - `SpikeSamples/NM-AfferentNeurons/*` и `SpikeSamples/NeuralElements/NReceptor` демонстрируют формирование афферентных импульсных потоков;
   - в их `README.md` стоит описывать:
     - АЧХ афферентного нейрона (зависимость частоты выходных импульсов от входного сигнала);
     - типы входного сигнала (растяжение мышцы, сила натяжения сухожилия и т.п.);
     - как эти каналы используются в конфигурациях MC1‑PCN.

### Рекомендации по README для конфигураций управления мышцей

Для каждой конфигурации MC1‑PCN:

- чётко прописать:
  - какие нейронные блоки моделируются (мотонейроны, клетки Реншоу, интернейроны, афферентные каналы);
  - каковы основные параметры (порог, глубина обратной связи, временные константы);
  - какие сценарии экспериментов рассматриваются (ступенчатое задание, синусоидальное, траектория, многопозиционный режим);
- привести хотя бы одну mermaid‑диаграмму структуры;
- связать наблюдаемые паттерны (ограничение частоты, стабилизация, фазовые соотношения) с соответствующими рисунками/графиками из статьи.

Этот документ задаёт рамку для таких README; конкретные детали по каждой конфигурации описываются на уровне её папки в `SpikeSamples/MC1-PCN/*`.

## Литература

1. [31] Моделирование нейронных структур управления мышечным сокращением. Схемы нейронных сетей. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=29:1&catid=67&lang=ru&Itemid=676)

---

## EN

## Neural structures for muscle contraction control

Work [1] covers:

- afferent neurons (Ia, II, Ib channels);
- motoneurons, Renshaw cells, inhibitory interneurons;
- methods of regulating muscle contraction force (discharge frequency, number of active motoneurons);
- reflex and recurrent circuits in the spinal cord.

### Corresponding SpikeSamples configurations

In `Bin/Configs/SpikeSamples`, these topics correspond primarily to:

- `MC0-RCN/MC-RCN-00-*/...`
  — reflex circuits (Ring/Reflex Control Networks) with motoneurons, Renshaw cells, branching afferent pathways.
- `MC0-RCN/MC-RCN-01-NumMotionElements-Pendulum/...`
  — influence of the number of motor elements and feedback structure on pendulum model dynamics.
- `MC1-PCN/*` (`MotionControl_Test`, `MultiPositionControl_*`, `NewPositionControl_Test`)
  — more applied positional control schemes involving spiking networks.
- `EyeRetina/EyeRetinaMuscle`
  — example of a visuomotor circuit "retina → processing network → muscle".

Each configuration includes `Description.rtf` with detailed experiment descriptions; the new documentation in local `README.md` files consolidates these descriptions in Markdown format and supplements them with diagrams (mermaid), validation status, and links to relevant articles.

### General motoneuron – Renshaw cell circuit diagram

```mermaid
flowchart LR
    afferentIa["AfferentNeuron_Ia"] --> motoneuron["Motoneuron"]
    motoneuron --> muscle["Muscle"]
    motoneuron --> renshaw["RenshawCell"]
    renshaw --> motoneuron
    renshaw --> inhInterneuron["InhibitoryInterneuron"]
    inhInterneuron --> antagonistMN["AntagonistMotoneuron"]
```

Key effects demonstrated in SpikeSamples configurations:

- **recurrent inhibition** of motoneurons through Renshaw cells;
- **reciprocal inhibition of antagonist muscles** through interneurons;
- **dependence of motoneuron discharge frequency** on afferent input frequency and inhibitory circuit parameters.

### Link to specific configurations

- `MC0-RCN/*`
  — closest to schemes described in the article: explicit implementation of afferent channels, motoneurons, Renshaw cells, and muscle models (pendulum / DC motor).
- `MC1-PCN/*`
  — uses similar principles at a higher level (positional control), but can be viewed as an extension of basic RCN schemes.
- `EyeRetina/EyeRetinaMuscle`
  — adds a sensory (visual) front end and connects it to the motor circuit.

For each configuration set, local `README.md` files have been prepared with:

- biological motivation of the experiment;
- network structure (including mermaid diagrams for specific variants);
- stimulation scenarios and qualitative results (e.g., discharge frequency stabilization as input frequency increases, coordinated control of multiple muscles, etc.).

## SpikeSamples — neural structures for muscle contraction control

This document is based on work [1] and describes how the corresponding schemes are implemented in `Bin/Configs/SpikeSamples` configurations.

### Biological prototype

The classical spinal neural structure scheme is considered:

- afferent neurons (Ia, II, Ib) transmitting information from muscle spindles and Golgi organs;
- motoneurons innervating muscle fibers;
- inhibitory interneurons;
- Renshaw cells providing recurrent inhibition of motoneurons;
- muscle as the controlled object.

The network implements:

- mono- and disynaptic reflex arcs;
- recurrent inhibition;
- alpha-gamma coordination when additional control inputs are present.

### SpikeSamples configurations related to movement control

Main configurations:

- `SpikeSamples/MC1-PCN/MotionControl_Test`
- `SpikeSamples/MC1-PCN/NewPositionControl_Test`
- `SpikeSamples/MC1-PCN/MultiPositionControl_SimpleTest`
- `SpikeSamples/MC1-PCN/MultiPositionControl_SoloModeTest`
- `SpikeSamples/MC1-PCN/MultiPositionControl_TaskTest`
- `SpikeSamples/MC1-PCN/MultiPositionControl_RememberStateTest`
- `SpikeSamples/MC1-PCN/MultiPC_TwoLevelsTask`

Additionally, some aspects of afferent channels and sensing are demonstrated in:

- `SpikeSamples/NM-AfferentNeurons/*`
- `SpikeSamples/NeuralElements/NReceptor`

Each MC1-PCN configuration models:

- a subset of the scheme described in the article;
- a specific control scenario (positional, multi-position, with state memory, with multi-level hierarchy, etc.).

### Motoneuron — Renshaw cell scheme (recurrent inhibition)

A key theme of the article is recurrent motoneuron inhibition through a Renshaw cell, stabilizing discharge frequency as input frequency increases.

This can be schematically represented as:

```mermaid
flowchart TD
    afferentIa["Afferent Ia/II
(SpikeSamples/NM-AfferentNeurons)"] --> motoneuron["Motoneuron
(NPulseNeuron)"]
    motoneuron --> muscle["Muscle
(модель мышцы или выходной канал)"]
    motoneuron --> renshaw["Renshaw cell
(NPulseNeuron)"]
    renshaw -->|тормозное влияние| motoneuron
```

In MC1-PCN configurations:

- afferent inputs may be played by spike generators or afferent neurons (`NM-AN-*`);
- motoneurons and Renshaw cells are implemented based on `NPulseNeuron` with different membrane structures and input connections;
- muscle is represented either as an aggregated network output or as a separate subsystem (in some configurations).

### Scenario examples from MC1-PCN

1. **MotionControl_Test / NewPositionControl_Test**
   - demonstrate the basic circuit "afferentation → motoneuron → muscle" with position feedback;
   - `README.md` should describe:
     - which afferent feedback channels are used;
     - how motoneuron discharge patterns change under different command trajectories;
     - how this relates to article results (stabilization, output dynamics).

2. **MultiPositionControl_* and MultiPC_TwoLevelsTask**
   - extend the basic scheme to multi-position and/or hierarchical control:
     - multiple motoneurons and effector muscles;
     - role distribution between levels (local and global feedback loops);
   - `README.md` should record:
     - map of neural blocks (which configuration node corresponds to which article scheme element);
     - scenarios: target position changes, memory of previous position, antagonist muscle interaction.

3. **Link to afferent configurations**
   - `SpikeSamples/NM-AfferentNeurons/*` and `SpikeSamples/NeuralElements/NReceptor` demonstrate formation of afferent impulse streams;
   - their `README.md` should describe:
     - afferent neuron frequency response (dependence of output pulse frequency on input signal);
     - input signal types (muscle stretch, tendon tension force, etc.);
     - how these channels are used in MC1-PCN configurations.

### README recommendations for muscle control configurations

For each MC1-PCN configuration:

- clearly specify:
  - which neural blocks are modeled (motoneurons, Renshaw cells, interneurons, afferent channels);
  - main parameters (threshold, feedback depth, time constants);
  - which experiment scenarios are considered (step command, sinusoidal, trajectory, multi-position mode);
- include at least one mermaid structure diagram;
- relate observed patterns (frequency limiting, stabilization, phase relationships) to corresponding figures/graphs from the article.

This document sets the framework for such README files; specific details for each configuration are described at the `SpikeSamples/MC1-PCN/*` folder level.

## Literature

1. [31] Modeling neural structures for muscle contraction control. Neural network schemes. [online](https://neuromodeler.ru/index.php?option=com_content&view=article&id=29:1&catid=67&lang=ru&Itemid=676)

