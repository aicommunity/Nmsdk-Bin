## CableNeuronMulti_Diameters_ver94 — влияние диаметра дендритов (версия 94)

**Путь:** `Bin/Configs/SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_Diameters_ver94`
**Статус валидации:** VALID (см. `Reports/SpikeSamples-Validation-Report.md`)

### Назначение конфигурации

Эта конфигурация демонстрирует **влияние диаметра дендритов на распространение сигнала** в многокомпартментной кабельной модели CSNM (версия 94). Конфигурация является вариантом `CableNeuronMulti_Diameters` с параметрами версии 94 библиотеки NMSDK.

Согласно [2] и `CSNM-Models.md`, диаметр дендритов влияет на постоянную длины, сопротивление и скорость распространения сигнала. Данная конфигурация позволяет количественно изучить эти эффекты с параметрами версии 94.

### Отличия от других версий

Данная конфигурация использует параметры версии 94 библиотеки NMSDK. Для сравнения с другими версиями см.:
- `CableNeuronMulti_Diameters` — базовая версия
- `CableNeuronMulti_Diameters_ver93` — версия 93
- `CableNeuronMulti_Diameters_ver95` — версия 95
- `CableNeuronMulti_Diameters_ver101` — версия 101

### Связанные материалы

- Теория и функциональное описание:
  - [`Bin/Docs/SpikeSamples/CSNM-Models.md`](../../../../Docs/SpikeSamples/CSNM-Models.md) — модели кабельных нейронов CSNM
- Описание конфигурации:
  - `Description.rtf` — подробное описание конфигурации (в формате RTF)

## Литература

1. Bakhshiev A. V., Demcheva A. A. Compartmental spiking neuron model CSNM // Izvestiya VUZ. Applied Nonlinear Dynamics, 2022, vol. 30, iss. 3, pp. 299-310. [DOI](https://doi.org/10.18500/0869-6632-2022-30-3-299-310)

2. Демчева А.А. Разработка сегментной спайковой модели нейрона на основе кабельной теории для нейроморфных систем: выпускная квалификационная работа магистра. 2023. [онлайн](https://doi.org/10.18720/SPBPU/3/2023/vr/vr23-5657)
