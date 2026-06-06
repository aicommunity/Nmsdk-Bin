## RU

## Блок ActivitySwitcher: алгоритм последовательного переключения активности

Блок ActivitySwitcher (AS) позволяет реализовать последовательное переключение активности между узлами графа — это необходимо для запоминания и воспроизведения последовательности ситуаций. Принцип работы блока был изначально описан в работе [12] (см. нейронная сеть управления движением по траектории); для использования в данной работе конфигурация блока была обновлена с учетом актуальной версии нейрона CSNM.

### Описание компонентов

Блок ActivitySwitcher состоит из двух нейронов (N1 и N2), образующих кольцевую структуру с обратной связью. Структурные элементы блока:

- **N1** — первый нейрон блока AS
  - Сома: S¹
  - Дендриты: D¹, D², D³, D⁴, D⁵ (5 сегментов)
- **N2** — второй нейрон блока AS
  - Сома: S¹
  - Дендриты: D¹, D², D³ (3 сегмента)

#### Входные сигналы

- **u^top** — входной сигнал с высшего уровня системы управления (для первого блока AS)
- **u^(AS_(i-1))** — сигнал с предыдущего блока AS (для блоков начиная со второго)
- **y^PIN** — выходной сигнал нейрона PostInput i-го блока SignalManager

#### Выходные сигналы

- **u^(AS_i)** — выходной сигнал i-го блока AS (подается на следующий блок и на тормозные входы следующего блока)
- **Y** — выход второго нейрона (N2) блока AS

### Принцип работы

Способ подключения связей обеспечивает необходимые временные задержки сигналов и силу их воздействия, благодаря чему возбуждение и торможение нейронов происходит в нужной последовательности.

#### Временные задержки

Величина задержки зависит от количества сегментов дендрита, которое преодолевает сигнал от синапса до сомы нейрона — чем больше длина дендрита (т.е. чем из большего числа сегментов он состоит), тем больше задержка и наоборот.

#### Сила воздействия сигналов

Сила воздействия сигнала тем больше, чем ближе к соме нейрона подводится сигнал. Возможность задавать конфигурацию нейрона является отличительной чертой модели CSNM [10].

### Диаграмма последовательности алгоритма

```mermaid
sequenceDiagram
    participant TopLevel as Верхний уровень СУ
    participant AS_i as AS_i (блок i)
    participant N1_i as N1_i
    participant N2_i as N2_i
    participant SM_i as SignalManager_i
    participant PostInput_i as PostInput_i
    participant AS_next as AS_(i+1) (блок i+1)
    participant N1_next as N1_(i+1)
    participant N2_next as N2_(i+1)

    Note over AS_i: Этап 1: Активация первого блока
    TopLevel->>N1_i: u^top (на сому S¹)
    activate N1_i
    N1_i->>N1_i: Активация нейрона

    Note over AS_i: Этап 2: Кольцевая генерация импульсов
    N1_i->>N2_i: Возбуждение
    activate N2_i
    N2_i->>N1_i: Обратная связь
    N1_i->>AS_i: Генерация u^(AS_i)
    N2_i->>AS_i: Генерация u^(AS_i)

    Note over AS_next: Этап 3: Торможение следующего блока
    AS_i->>N1_next: u^(AS_i) → возбуждающий сигнал на D⁵
    AS_i->>N1_next: u^(AS_i) → тормозной сигнал на сому S¹
    AS_i->>N2_next: u^(AS_i) → тормозной сигнал на сому S¹
    Note over N1_next,N2_next: Торможение блокирует активацию<br/>(сила торможения > силы возбуждения)

    Note over SM_i: Этап 4: Распознавание знакомой ситуации
    SM_i->>PostInput_i: Обработка ситуации
    PostInput_i->>N1_i: y^PIN → тормозной сигнал на D¹
    PostInput_i->>N2_i: y^PIN → тормозной сигнал на D³
    deactivate N1_i
    deactivate N2_i
    Note over AS_i: Прекращение генерации u^(AS_i)

    Note over AS_next: Этап 5: Переключение на следующий блок
    AS_i->>N1_next: Снятие тормозного воздействия
    Note over N1_next: Задержанный возбуждающий сигнал<br/>с D⁵ достигает сомы
    activate N1_next
    N1_next->>N2_next: Возбуждение
    activate N2_next
    N2_next->>N1_next: Обратная связь
    N1_next->>AS_next: Генерация u^(AS_(i+1))
    N2_next->>AS_next: Генерация u^(AS_(i+1))
```

### Описание алгоритма по этапам

#### Этап 1: Активация первого блока AS

Первый AS в последовательности (т.е. блок, соответствующий начальной ситуации) активируется по приходу одиночного импульса с верхних слоев СУ (u^top) — так как он поступает непосредственно на сому (S¹), его достаточно для активации N1.

**Ключевые особенности:**
- Сигнал u^top поступает напрямую на сому первого нейрона N1
- Отсутствие задержки позволяет немедленно активировать нейрон
- Это единственный способ активации первого блока в последовательности

#### Этап 2: Генерация непрерывных импульсов

Нейроны N1 и N2 образуют кольцевую структуру с обратной связью, запускающую непрерывную генерацию импульсов на выходе элемента (u^(AS_i)).

**Механизм работы:**
- Активированный N1 возбуждает N2
- N2 через обратную связь поддерживает активность N1
- Образуется самоподдерживающийся цикл генерации импульсов
- Выходной сигнал u^(AS_i) генерируется непрерывно

#### Этап 3: Торможение следующего блока

Сигнал u^(AS_i) подается на вход нейрона N1 следующего блока AS: на возбуждающий синапс дендрита D⁵ и тормозные синапсы на сомах нейронов N1 и N2.

**Механизм торможения:**
- **Возбуждающий сигнал**: поступает на синапс пятого сегмента дендрита D⁵ нейрона N1 следующего блока
- **Тормозные сигналы**: поступают непосредственно на сомы нейронов N1 и N2 следующего блока
- Тормозное воздействие сигнала u^(AS_i), поступающее на сомы, имеет значительно больший вес, чем возбуждающее воздействие того же сигнала, подводимое к синапсу пятого сегмента дендрита
- Следовательно, торможение не позволяет активировать следующий блок AS, пока это тормозное воздействие не будет снято

#### Этап 4: Распознавание знакомой ситуации

Как только робот попадает в уже знакомую ситуацию, соответствующую текущему блоку AS, от нейрона PostInput соответствующего блока SignalManager поступает тормозное воздействие на D¹ и D³ нейронов N1 и N2.

**Процесс торможения текущего блока:**
- Сигнал y^PIN от PostInput блока SignalManager поступает на:
  - D¹ нейрона N1 (тормозной синапс)
  - D³ нейрона N2 (тормозной синапс)
- Торможение нейронов N1 и N2 прекращает активность текущего блока AS
- Генерация сигнала u^(AS_i) прекращается
- Снимается тормозное (а вместе с ним и возбуждающее) воздействие на следующий блок AS

#### Этап 5: Переключение на следующий блок

После прекращения генерации u^(AS_i) тормозное воздействие на следующий блок AS снимается. Однако возбуждающее воздействие подводилось к окончанию дендрита (D⁵), поэтому оно поступает на нейрон N1 следующего элемента со значительно большей временной задержкой — уже после того, как тормозное воздействие было снято, и поэтому активирует следующий блок AS.

**Временная последовательность переключения:**
1. **Момент t₀**: Прекращение генерации u^(AS_i) → снятие тормозного воздействия с AS_(i+1)
2. **Момент t₀ + Δt**: Задержанный возбуждающий сигнал с D⁵ достигает сомы N1_(i+1)
3. **Момент t₀ + Δt**: Активация N1_(i+1) запускает кольцевую генерацию в AS_(i+1)
4. **Результат**: Переключение активности с блока AS_i на блок AS_(i+1)

**Ключевой момент алгоритма:**
Временная задержка возбуждающего сигнала (обусловленная прохождением через 5 сегментов дендрита D⁵) обеспечивает, что активация следующего блока происходит только после полного снятия торможения. Это гарантирует корректное последовательное переключение активности между блоками.

### Схема подключения связей

```mermaid
flowchart TD
    subgraph AS_i["Блок ActivitySwitcher i"]
        N1_i["N1<br/>S¹, D¹-D⁵"]
        N2_i["N2<br/>S¹, D¹-D³"]
        N1_i <--> N2_i
    end

    subgraph AS_next["Блок ActivitySwitcher i+1"]
        N1_next["N1<br/>S¹, D¹-D⁵"]
        N2_next["N2<br/>S¹, D¹-D³"]
        N1_next <--> N2_next
    end

    subgraph SM_i["SignalManager i"]
        PostInput_i["PostInput"]
    end

    TopLevel["Верхний уровень СУ<br/>u^top"] -->|"на S¹"| N1_i

    N1_i -->|"u^(AS_i)<br/>возбуждающий на D⁵"| N1_next
    N1_i -->|"u^(AS_i)<br/>тормозной на S¹"| N1_next
    N1_i -->|"u^(AS_i)<br/>тормозной на S¹"| N2_next

    PostInput_i -->|"y^PIN<br/>тормозной на D¹"| N1_i
    PostInput_i -->|"y^PIN<br/>тормозной на D³"| N2_i

    style N1_i fill:#e1f5ff
    style N2_i fill:#e1f5ff
    style N1_next fill:#fff4e1
    style N2_next fill:#fff4e1
    style PostInput_i fill:#ffe1f5
```

### Примечания

- Конфигурация блока ActivitySwitcher была обновлена с учетом актуальной версии нейрона CSNM
- Алгоритм обеспечивает надежное последовательное переключение активности благодаря использованию временных задержек и различий в силе воздействия сигналов
- Механизм работает только при правильной настройке параметров нейронов и синапсов, обеспечивающих необходимые соотношения между тормозными и возбуждающими воздействиями

## Литература

12. **Korsakov, A., Bakhshiev, A., Astapova, L., Stankevich, L.** Behavioral functions implementation on spiking neural networks // Informatics and Automation, 2021, 20:3, 591–622.

    [DOI](https://doi.org/10.15622/ia.2021.3.4) | [Literature-References.md](../Literature-References.md)

10. **Bakhshiev A. V., Demcheva A. A.** Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310.

    [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310) | [Literature-References.md](../Literature-References.md)

---

## EN

## ActivitySwitcher block: sequential activity switching algorithm

The ActivitySwitcher (AS) block enables sequential activity switching between graph nodes — necessary for memorizing and reproducing a sequence of situations. The block's operating principle was originally described in work [12] (see the neural network for trajectory movement control); for use in this work, the block configuration was updated to account for the current CSNM neuron version.

### Component description

The ActivitySwitcher block consists of two neurons (N1 and N2) forming a ring structure with feedback. Structural elements of the block:

- **N1** — first neuron of the AS block
  - Soma: S¹
  - Dendrites: D¹, D², D³, D⁴, D⁵ (5 segments)
- **N2** — second neuron of the AS block
  - Soma: S¹
  - Dendrites: D¹, D², D³ (3 segments)

#### Input signals

- **u^top** — input signal from the upper control system level (for the first AS block)
- **u^(AS_(i-1))** — signal from the previous AS block (for blocks starting from the second)
- **y^PIN** — output signal of the PostInput neuron of the i-th SignalManager block

#### Output signals

- **u^(AS_i)** — output signal of the i-th AS block (fed to the next block and to inhibitory inputs of the next block)
- **Y** — output of the second neuron (N2) of the AS block

### Operating principle

The connection wiring ensures necessary signal time delays and influence strength, thanks to which neuron excitation and inhibition occur in the required sequence.

#### Time delays

Delay magnitude depends on the number of dendrite segments the signal traverses from synapse to neuron soma — the longer the dendrite (i.e., the more segments it consists of), the greater the delay and vice versa.

#### Signal influence strength

Signal influence strength is greater the closer to the neuron soma the signal is applied. The ability to configure the neuron is a distinguishing feature of the CSNM model [10].

### Algorithm sequence diagram

```mermaid
sequenceDiagram
    participant TopLevel as Верхний уровень СУ
    participant AS_i as AS_i (блок i)
    participant N1_i as N1_i
    participant N2_i as N2_i
    participant SM_i as SignalManager_i
    participant PostInput_i as PostInput_i
    participant AS_next as AS_(i+1) (блок i+1)
    participant N1_next as N1_(i+1)
    participant N2_next as N2_(i+1)

    Note over AS_i: Этап 1: Активация первого блока
    TopLevel->>N1_i: u^top (на сому S¹)
    activate N1_i
    N1_i->>N1_i: Активация нейрона

    Note over AS_i: Этап 2: Кольцевая генерация импульсов
    N1_i->>N2_i: Возбуждение
    activate N2_i
    N2_i->>N1_i: Обратная связь
    N1_i->>AS_i: Генерация u^(AS_i)
    N2_i->>AS_i: Генерация u^(AS_i)

    Note over AS_next: Этап 3: Торможение следующего блока
    AS_i->>N1_next: u^(AS_i) → возбуждающий сигнал на D⁵
    AS_i->>N1_next: u^(AS_i) → тормозной сигнал на сому S¹
    AS_i->>N2_next: u^(AS_i) → тормозной сигнал на сому S¹
    Note over N1_next,N2_next: Торможение блокирует активацию<br/>(сила торможения > силы возбуждения)

    Note over SM_i: Этап 4: Распознавание знакомой ситуации
    SM_i->>PostInput_i: Processing ситуации
    PostInput_i->>N1_i: y^PIN → тормозной сигнал на D¹
    PostInput_i->>N2_i: y^PIN → тормозной сигнал на D³
    deactivate N1_i
    deactivate N2_i
    Note over AS_i: Прекращение генерации u^(AS_i)

    Note over AS_next: Этап 5: Переключение на следующий блок
    AS_i->>N1_next: Снятие тормозного воздействия
    Note over N1_next: Задержанный возбуждающий сигнал<br/>с D⁵ достигает сомы
    activate N1_next
    N1_next->>N2_next: Возбуждение
    activate N2_next
    N2_next->>N1_next: Обратная связь
    N1_next->>AS_next: Генерация u^(AS_(i+1))
    N2_next->>AS_next: Генерация u^(AS_(i+1))
```

### Algorithm description by stages

#### Stage 1: Activation of the first AS block

The first AS in the sequence (i.e., the block corresponding to the initial situation) is activated by arrival of a single pulse from upper CS layers (u^top) — since it arrives directly on the soma (S¹), it is sufficient to activate N1.

**Key features:**
- Signal u^top arrives directly on the soma of the first neuron N1
- Absence of delay allows immediate neuron activation
- This is the only way to activate the first block in the sequence

#### Stage 2: Continuous pulse generation

Neurons N1 and N2 form a ring structure with feedback, initiating continuous pulse generation at the element output (u^(AS_i)).

**Mechanism:**
- Activated N1 excites N2
- N2 through feedback maintains N1 activity
- A self-sustaining pulse generation cycle forms
- Output signal u^(AS_i) is generated continuously

#### Stage 3: Inhibition of the next block

Signal u^(AS_i) is fed to neuron N1 of the next AS block: to the excitatory synapse of dendrite D⁵ and inhibitory synapses on somata of neurons N1 and N2.

**Inhibition mechanism:**
- **Excitatory signal**: arrives at the synapse of the fifth dendrite segment D⁵ of neuron N1 of the next block
- **Inhibitory signals**: arrive directly on somata of neurons N1 and N2 of the next block
- Inhibitory influence of signal u^(AS_i) on somata has significantly greater weight than excitatory influence of the same signal applied to the synapse of the fifth dendrite segment
- Consequently, inhibition prevents activation of the next AS block while this inhibitory influence is not removed

#### Stage 4: Recognition of a familiar situation

As soon as the robot enters an already familiar situation corresponding to the current AS block, inhibitory influence from the PostInput neuron of the corresponding SignalManager block arrives on D¹ and D³ of neurons N1 and N2.

**Current block inhibition process:**
- Signal y^PIN from PostInput of the SignalManager block arrives at:
  - D¹ of neuron N1 (inhibitory synapse)
  - D³ of neuron N2 (inhibitory synapse)
- Inhibition of neurons N1 and N2 stops current AS block activity
- Generation of signal u^(AS_i) ceases
- Inhibitory (and together with it excitatory) influence on the next AS block is removed

#### Stage 5: Switching to the next block

After u^(AS_i) generation ceases, inhibitory influence on the next AS block is removed. However, excitatory influence was applied to the dendrite end (D⁵), so it reaches neuron N1 of the next element with significantly greater time delay — already after inhibitory influence was removed, and therefore activates the next AS block.

**Switching time sequence:**
1. **Time t₀**: Cessation of u^(AS_i) generation → removal of inhibitory influence from AS_(i+1)
2. **Time t₀ + Δt**: Delayed excitatory signal from D⁵ reaches soma of N1_(i+1)
3. **Time t₀ + Δt**: Activation of N1_(i+1) initiates ring generation in AS_(i+1)
4. **Result**: Activity switches from block AS_i to block AS_(i+1)

**Key algorithm point:**
Time delay of the excitatory signal (due to passage through 5 dendrite segments D⁵) ensures that activation of the next block occurs only after complete removal of inhibition. This guarantees correct sequential activity switching between blocks.

### Connection wiring diagram

```mermaid
flowchart TD
    subgraph AS_i["Блок ActivitySwitcher i"]
        N1_i["N1<br/>S¹, D¹-D⁵"]
        N2_i["N2<br/>S¹, D¹-D³"]
        N1_i <--> N2_i
    end

    subgraph AS_next["Блок ActivitySwitcher i+1"]
        N1_next["N1<br/>S¹, D¹-D⁵"]
        N2_next["N2<br/>S¹, D¹-D³"]
        N1_next <--> N2_next
    end

    subgraph SM_i["SignalManager i"]
        PostInput_i["PostInput"]
    end

    TopLevel["Верхний уровень СУ<br/>u^top"] -->|"на S¹"| N1_i

    N1_i -->|"u^(AS_i)<br/>возбуждающий на D⁵"| N1_next
    N1_i -->|"u^(AS_i)<br/>тормозной на S¹"| N1_next
    N1_i -->|"u^(AS_i)<br/>тормозной на S¹"| N2_next

    PostInput_i -->|"y^PIN<br/>тормозной на D¹"| N1_i
    PostInput_i -->|"y^PIN<br/>тормозной на D³"| N2_i

    style N1_i fill:#e1f5ff
    style N2_i fill:#e1f5ff
    style N1_next fill:#fff4e1
    style N2_next fill:#fff4e1
    style PostInput_i fill:#ffe1f5
```

### Notes

- ActivitySwitcher block configuration was updated to account for the current CSNM neuron version
- Algorithm ensures reliable sequential activity switching through use of time delays and differences in signal influence strength
- Mechanism works only with correct neuron and synapse parameter settings ensuring necessary ratios between inhibitory and excitatory influences

## Literature

12. **Korsakov, A., Bakhshiev, A., Astapova, L., Stankevich, L.** Behavioral functions implementation on spiking neural networks // Informatics and Automation, 2021, 20:3, 591–622.

    [DOI](https://doi.org/10.15622/ia.2021.3.4) | [Literature-References.md](../Literature-References.md)

10. **Bakhshiev A. V., Demcheva A. A.** Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310.

    [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310) | [Literature-References.md](../Literature-References.md)
