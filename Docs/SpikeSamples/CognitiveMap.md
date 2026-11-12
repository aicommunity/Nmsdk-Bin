## RU

## Алгоритм формирования когнитивной карты

Алгоритм формирования когнитивной карты предназначен для построения графа ситуаций, в которых робот оказывается в процессе исследования среды. Каждый узел графа соответствует ситуации с необходимостью выбора направления движения. Алгоритм обеспечивает последовательное исследование среды, запоминание пройденных путей и оптимизацию маршрутов.

### Компоненты узла графа

Каждый узел графа когнитивной карты содержит следующие компоненты:

- **AS** (ActivitySwitcher) — блок последовательного переключения активности
- **SM** (SignalManager) — блок управления сигналами, содержащий:
  - **PI** (PostInput) — нейрон слоя PostInput для распознавания знакомых ситуаций
  - **PC** (PreControl) — нейрон слоя PreControl для лавинного распространения сигнала
- **NT** (NeuronTrainer) — обучаемые нейроны для запоминания ситуаций
- **Нейроны действия** — нейроны, соответствующие возможным направлениям движения

### Структура графа

Узлы графа организованы по уровням:
- **Уровень 0** — корневой узел (исходное положение робота)
- **Уровень 1, 2, ...** — дочерние узлы, создаваемые при попадании в новые ситуации

Узлы на одной глубине от корневого узла принадлежат к одному уровню.

### Диаграмма последовательности: создание корневого узла и дочерних узлов

```mermaid
sequenceDiagram
    participant Robot as Робот
    participant System as Система управления
    participant Node0 as Узел 0 (корневой)
    participant AS0 as AS_0
    participant SM0 as SM_0
    participant PI0 as PI_0
    participant PC0 as PC_0
    participant Node1 as Узел 1 (дочерний)
    participant Node2 as Узел 2 (дочерний)
    participant AS1 as AS_1
    participant AS2 as AS_2
    participant Action1 as Нейрон действия 1
    participant Action2 as Нейрон действия 2

    Note over System: Инициализация алгоритма
    System->>Node0: Создание корневого узла<br/>(исходное положение робота)
    activate Node0
    Node0->>AS0: Создание блока AS_0
    Node0->>SM0: Создание блока SM_0
    SM0->>PI0: Создание нейрона PI_0
    SM0->>PC0: Создание нейрона PC_0

    Note over Robot: Попадание в ситуацию с выбором
    Robot->>System: Сигнал о попадании в ситуацию
    System->>SM0: Проверка знакомости ситуации
    SM0->>PI0: Проверка активности PI_0
    PI0-->>SM0: Ситуация не знакома

    Note over System: Создание дочерних узлов
    System->>Node1: Создание узла 1<br/>(N_poss = 2)
    activate Node1
    System->>Node2: Создание узла 2
    activate Node2

    Node1->>AS1: Создание блока AS_1
    Node2->>AS2: Создание блока AS_2

    Note over System: Подключение связей к нейронам действия
    AS1->>Action1: Выход AS_1 → возбуждающий вход<br/>нейрона действия 1
    AS2->>Action2: Выход AS_2 → возбуждающий вход<br/>нейрона действия 2

    Note over System: Построение связей между узлами
    AS0->>AS1: Возбуждающая связь<br/>w_1 = 1.0
    AS0->>AS2: Возбуждающая связь<br/>w_2 = 0.75
    AS1->>AS0: Обратная связь<br/>w_fb = 0
    AS2->>AS0: Обратная связь<br/>w_fb = 0

    Note over System: Лавинное распространение сигнала
    PC0->>PC1: Связь PC_0 → PC_1<br/>w = 1.0
    PC0->>PC2: Связь PC_0 → PC_2<br/>w = 1.0
```

### Диаграмма последовательности: активация дочернего узла и запоминание ситуации

```mermaid
sequenceDiagram
    participant AS0 as AS_0
    participant SM0 as SM_0
    participant PI0 as PI_0
    participant NT0 as NT_0
    participant AS1 as AS_1
    participant Action1 as Нейрон действия 1
    participant Robot as Робот

    Note over AS0: Завершение запоминания ситуации 0
    SM0->>NT0: Обучение нейрона NT_0<br/>(ситуация запомнена)
    activate NT0
    NT0-->>SM0: Обучение завершено

    Note over SM0: Удаление входящих связей на PC_0
    SM0->>PC0: Удаление всех входящих связей<br/>на нейрон PC_0

    Note over AS0: Активация дочернего узла
    AS0->>AS1: Передача активности<br/>(w_1 = 1.0)
    activate AS1
    AS1->>Action1: Генерация сигнала действия
    Action1->>Robot: Сигнал: выполнить действие 1

    Note over Robot: Выполнение действия
    Robot->>Robot: Перемещение в направлении 1
    Robot->>SM0: Попадание в ситуацию 1
```

### Диаграмма последовательности: изменение весов связей при исследовании

```mermaid
sequenceDiagram
    participant System as Система управления
    participant Node_i as Узел i (текущий)
    participant AS_i as AS_i
    participant Node_i1 as Узел i+1 (дочерний)
    participant AS_i1 as AS_(i+1)
    participant Node_i2 as Узел i+2 (дочерний)
    participant AS_i2 as AS_(i+2)
    participant Robot as Робот

    Note over Robot: Исследование направления i+1
    Robot->>System: Попадание в тупик<br/>или знакомую ситуацию
    System->>AS_i: Уменьшение веса w_(i+1) = 0

    Note over System: Проверка всех направлений
    System->>System: Все последующие ситуации<br/>в направлении i+1 изучены?

    alt Все ситуации изучены
        System->>AS_i: Увеличение веса<br/>w_(i+2) = 1.0
        System->>AS_i2: Активация следующего<br/>дочернего узла
    else Все направления изучены
        System->>AS_i: Увеличение веса<br/>обратной связи w_fb = 1.0
        System->>AS_i: Возврат к родительскому узлу
    end

    Note over System: Веса связей как вентили
    Note over AS_i: w = 1.0 → узел активируется
    Note over AS_i: w = 0.75 → узел в покое
    Note over AS_i: w = 0 → узел заблокирован
```

### Диаграмма последовательности: лавинное распространение сигнала через PreControl

```mermaid
sequenceDiagram
    participant System as Система управления
    participant Node0 as Узел 0 (уровень 0)
    participant PC0 as PC_0
    participant Node1 as Узел 1 (уровень 1)
    participant PC1 as PC_1
    participant Node2 as Узел 2 (уровень 1)
    participant PC2 as PC_2
    participant Node3 as Узел 3 (уровень 2)
    participant PC3 as PC_3
    participant Node4 as Узел 4 (уровень 2)
    participant PC4 as PC_4

    Note over System: Создание новых дочерних узлов
    System->>Node3: Создание узла 3
    System->>Node4: Создание узла 4

    Note over System: Построение связей лавинного распространения
    Note over System: От всех пройденных узлов<br/>на уровнях выше
    PC0->>PC3: Связь PC_0 → PC_3<br/>w = 1.0
    PC0->>PC4: Связь PC_0 → PC_4<br/>w = 1.0
    PC1->>PC3: Связь PC_1 → PC_3<br/>w = 1.0
    PC1->>PC4: Связь PC_1 → PC_4<br/>w = 1.0
    PC2->>PC3: Связь PC_2 → PC_3<br/>w = 1.0
    PC2->>PC4: Связь PC_2 → PC_4<br/>w = 1.0

    Note over System: Веса связей не изменяются<br/>в процессе работы системы
```

### Диаграмма последовательности: проверка целесообразности движения при повторном попадании

```mermaid
sequenceDiagram
    participant Robot as Робот
    participant System as Система управления
    participant Node_i as Узел i (текущий)
    participant PI_i as PI_i
    participant PC_i as PC_i
    participant Node_prev as Предыдущий узел
    participant Node_next as Последующие узлы<br/>(уровни ниже)
    participant PC_next as PC последующих узлов
    participant AS_i as AS_i

    Note over Robot: Повторное попадание в узел i
    Robot->>System: Попадание в узел i
    System->>PI_i: Проверка активности PI_i
    PI_i-->>System: Ситуация знакома<br/>(PI_i активен)

    Note over System: Проверка уровня
    System->>System: Уровень узла i < уровня<br/>предыдущего узла?

    alt Уровень меньше (не продвинулись)
        Note over System: Механизм лавинного возбуждения
        System->>PC_i: Передача сигнала от PI_i<br/>на короткое время
        activate PC_i
        PC_i->>PC_next: Лавинное распространение<br/>к узлам на уровнях ниже
        activate PC_next

        alt Есть ответная реакция
            PC_next-->>System: Срабатывание PC<br/>(есть неисследованные узлы)
            Note over System: Продолжаем исследование
        else Нет ответной реакции
            PC_next-->>System: Нет срабатывания<br/>(все направления изучены)
            System->>AS_i: Уменьшение веса связи<br/>на последнее направление w = 0
            System->>AS_i: Увеличение веса связи<br/>на следующее направление w = 1.0
        end
        deactivate PC_next
        deactivate PC_i
    else Уровень не меньше
        Note over System: Продвинулись дальше<br/>продолжаем исследование
    end
```

### Диаграмма последовательности: слияние совпадающих узлов

```mermaid
sequenceDiagram
    participant System as Система управления
    participant Node_new as Новый узел<br/>(необученный)
    participant Node_active as Активный узел<br/>(обученный)
    participant AS_new as AS нового узла
    participant SM_new as SM нового узла
    participant AS_active as AS активного узла
    participant SM_active as SM активного узла

    Note over System: Попадание в новый узел
    System->>Node_new: Создание нового узла
    activate Node_new

    Note over System: Детектирование активности
    System->>System: Проверка активности<br/>других узлов графа
    System->>Node_active: Обнаружение активности<br/>обученного узла
    activate Node_active

    Note over System: Слияние узлов
    System->>System: Перенос связей<br/>нового узла на активный

    Note over System: Перенос входных связей
    AS_new->>AS_active: Перенос входных связей<br/>от родительских узлов
    SM_new->>SM_active: Перенос входных связей<br/>на SM активного узла

    Note over System: Перенос выходных связей
    AS_new->>AS_active: Перенос выходных связей<br/>к дочерним узлам
    AS_new->>AS_active: Перенос связей<br/>к нейронам действия

    Note over System: Удаление нового узла
    System->>Node_new: Удаление узла<br/>(слияние завершено)
    deactivate Node_new

    Note over System: Использование активного узла
    System->>Node_active: Все связи перенесены<br/>на активный узел
    deactivate Node_active
```

### Описание алгоритма по этапам

#### Этап 1: Инициализация — создание корневого узла

В начале работы алгоритма строится первый (корневой) узел, соответствующий исходному положению робота.

**Компоненты корневого узла:**
- Блок ActivitySwitcher (AS_0)
- Блок SignalManager (SM_0) с нейронами PI_0 и PC_0
- Обучаемые нейроны (NT_0) для запоминания ситуации

#### Этап 2: Создание дочерних узлов при попадании в новую ситуацию

Каждый раз при получении сигнала о попадании в ситуацию с необходимостью выбора проверяется, является ли данная ситуация уже знакомой.

**Если ситуация не знакома:**
1. Создается N_poss новых узлов — по одному для каждого из возможных направлений движения
2. Выход каждого из только что созданных элементов подключается к возбуждающему входу соответствующего нейрона действия
3. От блока ActivitySwitcher текущего узла на каждый из только что созданных (дочерних) узлов строятся возбуждающие связи

**Начальные веса связей:**
- w_1 = 1.0 (вес связи на первый дочерний нейрон)
- w_i = 0.75 (веса остальных связей, i > 1)
- w_fb = 0 (вес обратных связей от дочерних узлов к родительскому)

#### Этап 3: Лавинное распространение сигнала через PreControl

При создании новых узлов помимо связей между родительским и дочерним узлами дополнительно строится отдельная система связей между нейронами PreControl (PC) различных узлов графа.

**Механизм работы:**
- От нейронов PC каждого из пройденных узлов на уровнях выше к нейронам PC каждого из только что созданных дочерних узлов строятся связи
- Веса всех связей этой сети по умолчанию равны единице и не изменяются в процессе работы системы
- При запоминании ситуации все входящие связи на нейрон PC соответствующего ей узла удаляются
- «Откликнуться» на лавинное возбуждение могут только нейроны тех узлов, в которых робот еще не был

#### Этап 4: Изменение весов связей в ходе перемещения

Веса связей изменяются в ходе перемещения робота. Вес уменьшается до w_i = 0, если выполняется одно из следующих условий:

1. **Выбор этого направления приводит в тупик или в уже знакомую ситуацию**
   - Вес связи на это направление устанавливается w_i = 0
   - Увеличивается вес связи на следующий дочерний узел w_(i+1) = 1

2. **Все последующие ситуации в этом направлении уже были изучены**
   - Вес связи на это направление устанавливается w_i = 0
   - Увеличивается вес связи на следующий дочерний узел w_(i+1) = 1

3. **Все последующие ситуации по всем дочерним направлениям уже исследованы**
   - Вес связи на последнее направление устанавливается w_i = 0
   - Увеличивается вес обратной связи w_fb = 1

**Роль весов связей:**
Веса связей выполняют роль вентиля — выходной сигнал текущего AS активирует тот из дочерних AS, вес связи с которым равен единице, остальные узлы остаются в покое.

#### Этап 5: Проверка целесообразности движения при повторном попадании

Если робот попал в некоторый узел повторно, и номер уровня этого узла меньше, чем уровень предыдущего пройденного узла (то есть, робот не продвинулся дальше в исследовании среды), необходимо проверить целесообразность дальнейшего движения.

**Механизм лавинного возбуждения:**
1. На вход нейрона PC текущего узла на короткое время передается выходной сигнал нейрона PostInput (он активен, так как ситуация уже была запомнена)
2. От нейрона PC текущего узла распространяется лавинное возбуждение к нейронам PC всех последующих узлов на уровнях ниже
3. Если какой-то из них сработал, значит, в этом направлении остались еще не исследованные узлы
4. Если же ответной реакции на лавинное возбуждение не последовало, следует:
   - Уменьшить вес связи на последнем пройденном дочернем направлении текущего узла
   - Увеличить вес связи на следующее дочернее направление

#### Этап 6: Слияние совпадающих узлов

Если при попадании в новый узел детектируется активность на другом, уже «обученном», узле графа, то входные и выходные связи данного узла переносятся на активный узел.

**Процесс слияния:**
1. Обнаружение активности на обученном узле
2. Перенос всех входных связей нового узла на активный узел
3. Перенос всех выходных связей нового узла на активный узел
4. Удаление нового узла после переноса связей

### Схема графа для первой ситуации с двумя возможными действиями

```mermaid
flowchart TD
    subgraph Node0["Узел 0 (корневой, уровень 0)"]
        AS0["AS_0"]
        SM0["SM_0"]
        PI0["PI_0"]
        PC0["PC_0"]
        NT0["NT_0<br/>(обученный)"]
        AS0 <--> SM0
        SM0 --> PI0
        SM0 --> PC0
        SM0 --> NT0
    end

    subgraph Node1["Узел 1 (дочерний, уровень 1)"]
        AS1["AS_1"]
        SM1["SM_1"]
        PI1["PI_1"]
        PC1["PC_1"]
        AS1 <--> SM1
        SM1 --> PI1
        SM1 --> PC1
    end

    subgraph Node2["Узел 2 (дочерний, уровень 1)"]
        AS2["AS_2"]
        SM2["SM_2"]
        PI2["PI_2"]
        PC2["PC_2"]
        AS2 <--> SM2
        SM2 --> PI2
        SM2 --> PC2
    end

    Action1["Нейрон действия 1"]
    Action2["Нейрон действия 2"]

    AS0 -->|"w_1 = 1.0<br/>(синий)"| AS1
    AS0 -->|"w_2 = 0.75<br/>(синий)"| AS2
    AS1 -.->|"w_fb = 0<br/>(красный)"| AS0
    AS2 -.->|"w_fb = 0<br/>(красный)"| AS0

    AS1 -->|"возбуждающий<br/>(зеленый)"| Action1
    AS2 -->|"возбуждающий<br/>(зеленый)"| Action2

    PC0 -->|"w = 1.0<br/>(оранжевый)"| PC1
    PC0 -->|"w = 1.0<br/>(оранжевый)"| PC2

    style Node0 fill:#e1f5ff
    style Node1 fill:#fff4e1
    style Node2 fill:#fff4e1
    style NT0 fill:#d0d0d0
    style Action1 fill:#90ee90
    style Action2 fill:#90ee90
```

**Обозначения на схеме:**
- **Синий** — связи от текущего узла к дочерним (возбуждающие)
- **Красный** — обратные связи от дочерних узлов к родительскому
- **Оранжевый** — связи для лавинного распространения сигнала через PreControl
- **Зеленый** — связи к нейронам действия
- **Серый** — обученный нейрон (NT_0)

### Примечания

- Алгоритм обеспечивает последовательное исследование среды с запоминанием пройденных путей
- Механизм изменения весов связей позволяет оптимизировать маршруты и избегать повторного исследования уже изученных областей
- Лавинное распространение сигнала через PreControl обеспечивает эффективную проверку наличия неисследованных направлений
- Слияние совпадающих узлов оптимизирует структуру графа и предотвращает избыточное дублирование информации

## Литература

12. **Korsakov, A., Bakhshiev, A., Astapova, L., Stankevich, L.** Behavioral functions implementation on spiking neural networks // Informatics and Automation, 2021, 20:3, 591–622.

    [DOI](https://doi.org/10.15622/ia.2021.3.4) | [Literature-References.md](../Literature-References.md)

---

## EN

## Cognitive map formation algorithm

The cognitive map formation algorithm is designed to build a situation graph in which the robot finds itself during environment exploration. Each graph node corresponds to a situation requiring a movement direction choice. The algorithm ensures sequential environment exploration, memorization of traversed paths, and route optimization.

### Graph node components

Each cognitive map graph node contains the following components:

- **AS** (ActivitySwitcher) — sequential activity switching block
- **SM** (SignalManager) — signal management block containing:
  - **PI** (PostInput) — PostInput layer neuron for recognizing familiar situations
  - **PC** (PreControl) — PreControl layer neuron for avalanche signal propagation
- **NT** (NeuronTrainer) — trainable neurons for memorizing situations
- **Action neurons** — neurons corresponding to possible movement directions

### Graph structure

Graph nodes are organized by levels:
- **Level 0** — root node (robot's initial position)
- **Level 1, 2, ...** — child nodes created when entering new situations

Nodes at the same depth from the root belong to the same level.

### Sequence diagram: root node and child node creation

```mermaid
sequenceDiagram
    participant Robot as Робот
    participant System as Система управления
    participant Node0 as Узел 0 (корневой)
    participant AS0 as AS_0
    participant SM0 as SM_0
    participant PI0 as PI_0
    participant PC0 as PC_0
    participant Node1 as Узел 1 (дочерний)
    participant Node2 as Узел 2 (дочерний)
    participant AS1 as AS_1
    participant AS2 as AS_2
    participant Action1 as Нейрон действия 1
    participant Action2 as Нейрон действия 2

    Note over System: Initialization алгоритма
    System->>Node0: Creation корневого узла<br/>(исходное положение робота)
    activate Node0
    Node0->>AS0: Creation блока AS_0
    Node0->>SM0: Creation блока SM_0
    SM0->>PI0: Creation нейрона PI_0
    SM0->>PC0: Creation нейрона PC_0

    Note over Robot: Попадание в ситуацию с выбором
    Robot->>System: Сигнал о попадании в ситуацию
    System->>SM0: Проверка знакомости ситуации
    SM0->>PI0: Проверка активности PI_0
    PI0-->>SM0: Ситуация не знакома

    Note over System: Creation дочерних узлов
    System->>Node1: Creation узла 1<br/>(N_poss = 2)
    activate Node1
    System->>Node2: Creation узла 2
    activate Node2

    Node1->>AS1: Creation блока AS_1
    Node2->>AS2: Creation блока AS_2

    Note over System: Подключение связей к нейронам действия
    AS1->>Action1: Выход AS_1 → возбуждающий вход<br/>нейрона действия 1
    AS2->>Action2: Выход AS_2 → возбуждающий вход<br/>нейрона действия 2

    Note over System: Build связей между узлами
    AS0->>AS1: Возбуждающая связь<br/>w_1 = 1.0
    AS0->>AS2: Возбуждающая связь<br/>w_2 = 0.75
    AS1->>AS0: Обратная связь<br/>w_fb = 0
    AS2->>AS0: Обратная связь<br/>w_fb = 0

    Note over System: Лавинное распространение сигнала
    PC0->>PC1: Связь PC_0 → PC_1<br/>w = 1.0
    PC0->>PC2: Связь PC_0 → PC_2<br/>w = 1.0
```

### Sequence diagram: child node activation and situation memorization

```mermaid
sequenceDiagram
    participant AS0 as AS_0
    participant SM0 as SM_0
    participant PI0 as PI_0
    participant NT0 as NT_0
    participant AS1 as AS_1
    participant Action1 as Нейрон действия 1
    participant Robot as Робот

    Note over AS0: Завершение запоминания ситуации 0
    SM0->>NT0: Обучение нейрона NT_0<br/>(ситуация запомнена)
    activate NT0
    NT0-->>SM0: Обучение завершено

    Note over SM0: Удаление входящих связей на PC_0
    SM0->>PC0: Удаление всех входящих связей<br/>на нейрон PC_0

    Note over AS0: Активация дочернего узла
    AS0->>AS1: Передача активности<br/>(w_1 = 1.0)
    activate AS1
    AS1->>Action1: Генерация сигнала действия
    Action1->>Robot: Сигнал: выполнить действие 1

    Note over Robot: Выполнение действия
    Robot->>Robot: Перемещение в направлении 1
    Robot->>SM0: Попадание в ситуацию 1
```

### Sequence diagram: connection weight changes during movement

```mermaid
sequenceDiagram
    participant System as Система управления
    participant Node_i as Узел i (текущий)
    participant AS_i as AS_i
    participant Node_i1 as Узел i+1 (дочерний)
    participant AS_i1 as AS_(i+1)
    participant Node_i2 as Узел i+2 (дочерний)
    participant AS_i2 as AS_(i+2)
    participant Robot as Робот

    Note over Robot: Исследование направления i+1
    Robot->>System: Попадание в тупик<br/>или знакомую ситуацию
    System->>AS_i: Уменьшение веса w_(i+1) = 0

    Note over System: Проверка всех направлений
    System->>System: Все последующие ситуации<br/>в направлении i+1 изучены?

    alt Все ситуации изучены
        System->>AS_i: Увеличение веса<br/>w_(i+2) = 1.0
        System->>AS_i2: Активация следующего<br/>дочернего узла
    else Все направления изучены
        System->>AS_i: Увеличение веса<br/>обратной связи w_fb = 1.0
        System->>AS_i: Возврат к родительскому узлу
    end

    Note over System: Веса связей как вентили
    Note over AS_i: w = 1.0 → узел активируется
    Note over AS_i: w = 0.75 → узел в покое
    Note over AS_i: w = 0 → узел заблокирован
```

### Sequence diagram: avalanche signal propagation through PreControl

```mermaid
sequenceDiagram
    participant System as Система управления
    participant Node0 as Узел 0 (уровень 0)
    participant PC0 as PC_0
    participant Node1 as Узел 1 (уровень 1)
    participant PC1 as PC_1
    participant Node2 as Узел 2 (уровень 1)
    participant PC2 as PC_2
    participant Node3 as Узел 3 (уровень 2)
    participant PC3 as PC_3
    participant Node4 as Узел 4 (уровень 2)
    participant PC4 as PC_4

    Note over System: Creation новых дочерних узлов
    System->>Node3: Creation узла 3
    System->>Node4: Creation узла 4

    Note over System: Build связей лавинного распространения
    Note over System: От всех пройденных узлов<br/>на уровнях выше
    PC0->>PC3: Связь PC_0 → PC_3<br/>w = 1.0
    PC0->>PC4: Связь PC_0 → PC_4<br/>w = 1.0
    PC1->>PC3: Связь PC_1 → PC_3<br/>w = 1.0
    PC1->>PC4: Связь PC_1 → PC_4<br/>w = 1.0
    PC2->>PC3: Связь PC_2 → PC_3<br/>w = 1.0
    PC2->>PC4: Связь PC_2 → PC_4<br/>w = 1.0

    Note over System: Веса связей не изменяются<br/>в процессе работы системы
```

### Sequence diagram: movement advisability check on re-entry

```mermaid
sequenceDiagram
    participant Robot as Робот
    participant System as Система управления
    participant Node_i as Узел i (текущий)
    participant PI_i as PI_i
    participant PC_i as PC_i
    participant Node_prev as Предыдущий узел
    participant Node_next as Последующие узлы<br/>(уровни ниже)
    participant PC_next as PC последующих узлов
    participant AS_i as AS_i

    Note over Robot: Повторное попадание в узел i
    Robot->>System: Попадание в узел i
    System->>PI_i: Проверка активности PI_i
    PI_i-->>System: Ситуация знакома<br/>(PI_i активен)

    Note over System: Проверка уровня
    System->>System: Уровень узла i < уровня<br/>предыдущего узла?

    alt Уровень меньше (не продвинулись)
        Note over System: Механизм лавинного возбуждения
        System->>PC_i: Передача сигнала от PI_i<br/>на короткое время
        activate PC_i
        PC_i->>PC_next: Лавинное распространение<br/>к узлам на уровнях ниже
        activate PC_next

        alt Есть ответная реакция
            PC_next-->>System: Срабатывание PC<br/>(есть неисследованные узлы)
            Note over System: Продолжаем исследование
        else Нет ответной реакции
            PC_next-->>System: Нет срабатывания<br/>(все направления изучены)
            System->>AS_i: Уменьшение веса связи<br/>на последнее направление w = 0
            System->>AS_i: Увеличение веса связи<br/>на следующее направление w = 1.0
        end
        deactivate PC_next
        deactivate PC_i
    else Уровень не меньше
        Note over System: Продвинулись дальше<br/>продолжаем исследование
    end
```

### Sequence diagram: merging matching nodes

```mermaid
sequenceDiagram
    participant System as Система управления
    participant Node_new as Новый узел<br/>(необученный)
    participant Node_active as Активный узел<br/>(обученный)
    participant AS_new as AS нового узла
    participant SM_new as SM нового узла
    participant AS_active as AS активного узла
    participant SM_active as SM активного узла

    Note over System: Попадание в новый узел
    System->>Node_new: Creation нового узла
    activate Node_new

    Note over System: Детектирование активности
    System->>System: Проверка активности<br/>других узлов графа
    System->>Node_active: Обнаружение активности<br/>обученного узла
    activate Node_active

    Note over System: Слияние узлов
    System->>System: Перенос связей<br/>нового узла на активный

    Note over System: Перенос входных связей
    AS_new->>AS_active: Перенос входных связей<br/>от родительских узлов
    SM_new->>SM_active: Перенос входных связей<br/>на SM активного узла

    Note over System: Перенос выходных связей
    AS_new->>AS_active: Перенос выходных связей<br/>к дочерним узлам
    AS_new->>AS_active: Перенос связей<br/>к нейронам действия

    Note over System: Удаление нового узла
    System->>Node_new: Удаление узла<br/>(слияние завершено)
    deactivate Node_new

    Note over System: Использование активного узла
    System->>Node_active: Все связи перенесены<br/>на активный узел
    deactivate Node_active
```

### Algorithm description by stages

#### Stage 1: Initialization — root node creation

At algorithm start, the first (root) node corresponding to the robot's initial position is built.

**Root node components:**
- ActivitySwitcher block (AS_0)
- SignalManager block (SM_0) with neurons PI_0 and PC_0
- Trainable neurons (NT_0) for memorizing the situation

#### Stage 2: Child node creation when entering a new situation

Each time a signal is received about entering a situation requiring a choice, it is checked whether the situation is already familiar.

**If the situation is unfamiliar:**
1. N_poss new nodes are created — one for each possible movement direction
2. Output of each newly created element is connected to the excitatory input of the corresponding action neuron
3. Excitatory connections are built from the current node's ActivitySwitcher block to each newly created (child) node

**Initial connection weights:**
- w_1 = 1.0 (weight of connection to first child neuron)
- w_i = 0.75 (weights of remaining connections, i > 1)
- w_fb = 0 (weight of feedback connections from child nodes to parent)

#### Stage 3: Avalanche signal propagation through PreControl

When creating new nodes, in addition to connections between parent and child nodes, a separate connection system between PreControl (PC) neurons of different graph nodes is additionally built.

**Mechanism:**
- Connections are built from PC neurons of each traversed node at higher levels to PC neurons of each newly created child node
- Weights of all connections in this network default to one and do not change during system operation
- When memorizing a situation, all incoming connections to the PC neuron of the corresponding node are removed
- Only neurons of nodes the robot has not yet visited can "respond" to avalanche excitation

#### Stage 4: Connection weight changes during movement

Connection weights change as the robot moves. Weight decreases to w_i = 0 if one of the following conditions is met:

1. **Choosing this direction leads to a dead end or an already familiar situation**
   - Connection weight for this direction is set to w_i = 0
   - Weight of connection to next child node w_(i+1) = 1 is increased

2. **All subsequent situations in this direction have already been explored**
   - Connection weight for this direction is set to w_i = 0
   - Weight of connection to next child node w_(i+1) = 1 is increased

3. **All subsequent situations in all child directions have been explored**
   - Connection weight for last direction is set to w_i = 0
   - Feedback connection weight w_fb = 1 is increased

**Role of connection weights:**
Connection weights act as valves — output signal of the current AS activates the child AS whose connection weight equals one; other nodes remain at rest.

#### Stage 5: Movement advisability check on re-entry

If the robot re-enters a node and this node's level number is less than the level of the previously traversed node (i.e., the robot did not advance further in environment exploration), advisability of further movement must be checked.

**Avalanche excitation mechanism:**
1. PostInput neuron output signal is briefly fed to the PC neuron input of the current node (it is active since the situation was already memorized)
2. Avalanche excitation propagates from the current node's PC neuron to PC neurons of all subsequent nodes at lower levels
3. If any of them fires, there remain unexplored nodes in that direction
4. If no response to avalanche excitation follows, then:
   - Decrease connection weight on the last traversed child direction of the current node
   - Increase connection weight on the next child direction

#### Stage 6: Merging matching nodes

If when entering a new node activity is detected on another, already "trained" graph node, input and output connections of this node are transferred to the active node.

**Merge process:**
1. Detect activity on trained node
2. Transfer all input connections of new node to active node
3. Transfer all output connections of new node to active node
4. Delete new node after connection transfer

### Graph diagram for first situation with two possible actions

```mermaid
flowchart TD
    subgraph Node0["Узел 0 (корневой, уровень 0)"]
        AS0["AS_0"]
        SM0["SM_0"]
        PI0["PI_0"]
        PC0["PC_0"]
        NT0["NT_0<br/>(обученный)"]
        AS0 <--> SM0
        SM0 --> PI0
        SM0 --> PC0
        SM0 --> NT0
    end

    subgraph Node1["Узел 1 (дочерний, уровень 1)"]
        AS1["AS_1"]
        SM1["SM_1"]
        PI1["PI_1"]
        PC1["PC_1"]
        AS1 <--> SM1
        SM1 --> PI1
        SM1 --> PC1
    end

    subgraph Node2["Узел 2 (дочерний, уровень 1)"]
        AS2["AS_2"]
        SM2["SM_2"]
        PI2["PI_2"]
        PC2["PC_2"]
        AS2 <--> SM2
        SM2 --> PI2
        SM2 --> PC2
    end

    Action1["Нейрон действия 1"]
    Action2["Нейрон действия 2"]

    AS0 -->|"w_1 = 1.0<br/>(синий)"| AS1
    AS0 -->|"w_2 = 0.75<br/>(синий)"| AS2
    AS1 -.->|"w_fb = 0<br/>(красный)"| AS0
    AS2 -.->|"w_fb = 0<br/>(красный)"| AS0

    AS1 -->|"возбуждающий<br/>(зеленый)"| Action1
    AS2 -->|"возбуждающий<br/>(зеленый)"| Action2

    PC0 -->|"w = 1.0<br/>(оранжевый)"| PC1
    PC0 -->|"w = 1.0<br/>(оранжевый)"| PC2

    style Node0 fill:#e1f5ff
    style Node1 fill:#fff4e1
    style Node2 fill:#fff4e1
    style NT0 fill:#d0d0d0
    style Action1 fill:#90ee90
    style Action2 fill:#90ee90
```

**Diagram notation:**
- **Blue** — connections from current node to children (excitatory)
- **Red** — feedback connections from child nodes to parent
- **Orange** — connections for avalanche signal propagation through PreControl
- **Green** — connections to action neurons
- **Gray** — trained neuron (NT_0)

### Notes

- Algorithm ensures sequential environment exploration with memorization of traversed paths
- Connection weight change mechanism allows route optimization and avoids re-exploring already studied areas
- Avalanche signal propagation through PreControl provides efficient check for unexplored directions
- Merging matching nodes optimizes graph structure and prevents redundant information duplication

## Literature

12. **Korsakov, A., Bakhshiev, A., Astapova, L., Stankevich, L.** Behavioral functions implementation on spiking neural networks // Informatics and Automation, 2021, 20:3, 591–622.

    [DOI](https://doi.org/10.15622/ia.2021.3.4) | [Literature-References.md](../Literature-References.md)
