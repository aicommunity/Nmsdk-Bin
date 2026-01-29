## CableNeuronMulti_II_Diameters — влияние диаметра дендритов (вариант II)

**Путь:** `Bin/Configs/SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_II_Diameters`
**Статус валидации:** VALID (см. `Reports/SpikeSamples-Validation-Report.md`)

### Назначение конфигурации

Эта конфигурация демонстрирует **влияние диаметра дендритов на распространение сигнала** в многокомпартментной кабельной модели CSNM (вариант II). Конфигурация содержит несколько нейронов (`NPulseNeuronCableMulti`) с различным диаметром дендритов для сравнения их поведения.

Согласно [2] и `CSNM-Models.md`, диаметр дендритов влияет на постоянную длины, сопротивление и скорость распространения сигнала. Данная конфигурация позволяет количественно изучить эти эффекты с параметрами варианта II.

### Структура модели

Конфигурация содержит несколько кабельных нейронов с различным диаметром дендритов (вариант II):

```mermaid
flowchart TD
    Generator[PGenerator<br/>NPGenerator<br/>5 Гц] --> CableNeuron[CableNeuron<br/>Диаметр D1]
    Generator --> CableNeuron2[CableNeuron2<br/>Диаметр D2]
    Generator --> CableNeuron3[CableNeuron3<br/>Диаметр D3]
    Generator --> CableNeuron4[CableNeuron4<br/>Диаметр D4]
    Generator --> CableNeuron5[CableNeuron5<br/>Диаметр D5]
    Generator --> CableNeuron6[CableNeuron6<br/>Диаметр D6]
    Generator --> CableNeuron7[CableNeuron7<br/>Диаметр D7]
    Generator --> CableNeuron8[CableNeuron8<br/>Диаметр D8]
    Generator --> CableNeuron9[CableNeuron9<br/>Диаметр D9]
    Generator --> CableNeuron10[CableNeuron10<br/>Диаметр D10]
    Generator --> CableNeuron11[CableNeuron11<br/>Диаметр D11]
    Generator --> CableNeuron12[CableNeuron12<br/>Диаметр D12]
```

### Отличия от базовой версии

Данная конфигурация является вариантом II базовой конфигурации `CableNeuronMulti_Diameters`. Отличия могут включать:
- Различные параметры диаметра дендритов
- Различные параметры кабельного уравнения
- Различную структуру нейронов

### Связанные материалы

- Теория и функциональное описание:
  - [`Bin/Docs/SpikeSamples/CSNM-Models.md`](../../../../Docs/SpikeSamples/CSNM-Models.md) — модели кабельных нейронов CSNM
- Описание конфигурации:
  - `Description.rtf` — подробное описание конфигурации (в формате RTF)
- Связанные конфигурации:
  - `CableNeuronMulti_Diameters` — базовая версия
  - `CableNeuronMulti_II_Lengths` — влияние длины (вариант II)

## Литература

1. Bakhshiev A. V., Demcheva A. A. Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310. [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310)

2. Демчева А.А. Разработка сегментной спайковой модели нейрона на основе кабельной теории для нейроморфных систем: выпускная квалификационная работа магистра. 2023. [онлайн](https://doi.org/10.18720/SPBPU/3/2023/vr/vr23-5657)
