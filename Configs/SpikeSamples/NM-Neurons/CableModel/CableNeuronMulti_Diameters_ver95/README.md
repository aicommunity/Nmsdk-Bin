## CableNeuronMulti_Diameters_ver95 — влияние диаметра дендритов (версия 95)

**Путь:** `Bin/Configs/SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_Diameters_ver95`
**Статус валидации:** VALID (см. `Reports/SpikeSamples-Validation-Report.md`)

### Назначение конфигурации

Эта конфигурация демонстрирует **влияние диаметра дендритов на распространение сигнала** в многокомпартментной кабельной модели CSNM (версия 95). Конфигурация содержит несколько нейронов (`NPulseNeuronCableMulti`) с различным диаметром дендритов для сравнения их поведения.

Согласно [2] и `CSNM-Models.md`, диаметр дендритов влияет на:
- Сопротивление аксоплазмы (r_i ∝ 1/D²)
- Сопротивление мембраны (r_m ∝ 1/D)
- Постоянную длины (λ = √(r_m/r_i) ∝ √D)
- Скорость распространения сигнала

### Структура модели

Конфигурация содержит несколько кабельных нейронов с различным диаметром дендритов (версия 95):

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
    Generator --> CableNeuron13[CableNeuron13<br/>Диаметр D13]
```

### Отличия от других версий

Данная конфигурация использует параметры версии 95 библиотеки NMSDK. Для сравнения с другими версиями см.:
- `CableNeuronMulti_Diameters` — базовая версия
- `CableNeuronMulti_Diameters_ver93` — версия 93
- `CableNeuronMulti_Diameters_ver94` — версия 94
- `CableNeuronMulti_Diameters_ver101` — версия 101

### Связанные материалы

- Теория и функциональное описание:
  - [`Bin/Docs/SpikeSamples/CSNM-Models.md`](../../../../../Docs/SpikeSamples/CSNM-Models.md) — модели кабельных нейронов CSNM
- Описание конфигурации:
  - `Description.rtf` — подробное описание конфигурации (в формате RTF)

## Литература

1. Bakhshiev A. V., Demcheva A. A. Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310. [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310)

2. Демчева А.А. Разработка сегментной спайковой модели нейрона на основе кабельной теории для нейроморфных систем: выпускная квалификационная работа магистра. 2023. [онлайн](https://doi.org/10.18720/SPBPU/3/2023/vr/vr23-5657)
