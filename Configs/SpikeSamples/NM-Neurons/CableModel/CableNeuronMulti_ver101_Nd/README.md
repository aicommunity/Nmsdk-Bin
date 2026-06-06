## CableNeuronMulti_ver101_Nd — влияние количества дендритов (версия 101)

**Путь:** `Bin/Configs/SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_ver101_Nd`
**Статус валидации:** VALID (см. `Reports/SpikeSamples-Validation-Report.md`)

### Назначение конфигурации

Эта конфигурация демонстрирует **влияние количества дендритов (Nd) на поведение нейрона** в многокомпартментной кабельной модели CSNM (версия 101). Конфигурация содержит несколько нейронов (`NPulseNeuronCableMulti`) с различным количеством дендритов для сравнения их поведения.

Согласно [2] и `CSNM-Models.md`, количество дендритов влияет на пространственную структуру нейрона и обработку сигналов. Данная конфигурация позволяет количественно изучить эти эффекты с параметрами версии 101.

### Структура модели

Конфигурация содержит несколько кабельных нейронов с различным количеством дендритов (версия 101):

```mermaid
flowchart TD
    Generator[PGenerator<br/>NPGenerator<br/>5 Гц] --> CableNeuron[CableNeuron<br/>NPulseNeuronCableMulti<br/>Nd=1]
    Generator --> CableNeuron2[CableNeuron2<br/>NPulseNeuronCableMulti<br/>Nd=2]
    Generator --> CableNeuron3[CableNeuron3<br/>NPulseNeuronCableMulti<br/>Nd=3]
    Generator --> CableNeuron4[CableNeuron4<br/>NPulseNeuronCableMulti<br/>Nd=4]
    Generator --> CableNeuron5[CableNeuron5<br/>NPulseNeuronCableMulti<br/>Nd=5]
    Generator --> CableNeuron6[CableNeuron6<br/>NPulseNeuronCableMulti<br/>Nd=6]
```

### Эксперимент и моделируемые реакции

#### Цель эксперимента

Изучение влияния количества дендритов на поведение нейрона:
- Влияние количества дендритов на пространственную структуру нейрона
- Влияние на обработку сигналов от различных источников
- Влияние на интеграцию сигналов в соме

#### Ожидаемые результаты

- **Пространственная структура:** увеличение количества дендритов увеличивает пространственную сложность нейрона
- **Обработка сигналов:** большее количество дендритов позволяет обрабатывать сигналы от большего количества источников
- **Интеграция сигналов:** количество дендритов влияет на интеграцию сигналов в соме

### Связанные материалы

- Теория и функциональное описание:
  - [`Bin/Docs/SpikeSamples/CSNM-Models.md`](../../../../../Docs/SpikeSamples/CSNM-Models.md) — модели кабельных нейронов CSNM
- Описание конфигурации:
  - `Description.rtf` — подробное описание конфигурации (в формате RTF)
- Связанные конфигурации:
  - `CableNeuronMulti_ver101_Nsyn` — влияние количества синапсов (версия 101)
  - `CableNeuronMulti_ver101_Nd_matching` — влияние количества дендритов с matching (версия 101)

## Литература

1. Bakhshiev A. V., Demcheva A. A. Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310. [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310)

2. Демчева А.А. Разработка сегментной спайковой модели нейрона на основе кабельной теории для нейроморфных систем: выпускная квалификационная работа магистра. 2023. [онлайн](https://doi.org/10.18720/SPBPU/3/2023/vr/vr23-5657)
