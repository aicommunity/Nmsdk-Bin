# TipEpsCombined — REPORT R1

Два режима: (1) dual-pulse на `NPSynapseBio`; (2) канал (справочно).  
Каталог: `Bin/Configs/SpikeSamples/NeuralElements/TipEpsCombined/`.  
Ячейки: `cells/D*_ISI*` (синапс), `cells/CH_*` (канал).

## Общий протокол — синапс

| Параметр | Значение |
|----------|----------|
| Элемент | `NPSynapseBio` |
| Dual-pulse | один Gen: `Frequency = 1/ISI`, не два независимых Gen |
| `SecretionTC` | **0.001** с |
| `Delay` | **0.05** с (первый импульс) |
| `GlobalTimeStep` | **2000** |
| Gate | `sep = (min(p1,p2) − trough) / min(p1,p2) ≥ 0.30` |

ISI привязаны к сжатым span (min ISI после floor):

| Метка | ISI | Frequency (Гц) | Соответствует span |
|-------|-----|----------------|--------------------|
| `ISI100` | **16.7 мс** | ≈59.88 | min ISI @ T=100 мс |
| `ISI50` | **8.3 мс** | ≈120.48 | min ISI @ T=50 мс |
| `ISI25` | **4.2 мс** | ≈238.10 | min ISI @ T=25 мс |

## Каталог ячеек — синапс

| cell | Путь | DissociationTC | ISI | Frequency | Описание |
|------|------|----------------|-----|-----------|----------|
| `D005_ISI100` | `cells/D005_ISI100/` | 0.005 | 16.7 мс | 59.88 | Bio Dissoc × span100 |
| `D005_ISI50` | `cells/D005_ISI50/` | 0.005 | 8.3 мс | 120.48 | Bio × span50 |
| `D005_ISI25` | `cells/D005_ISI25/` | 0.005 | 4.2 мс | 238.10 | Bio × span25 (на грани) |
| `D002_ISI100` | `cells/D002_ISI100/` | 0.002 | 16.7 мс | 59.88 | |
| `D002_ISI50` | `cells/D002_ISI50/` | 0.002 | 8.3 мс | 120.48 | |
| `D002_ISI25` | `cells/D002_ISI25/` | 0.002 | 4.2 мс | 238.10 | рабочий D для FastSpan |
| `D001_ISI100` | `cells/D001_ISI100/` | 0.001 | 16.7 мс | 59.88 | |
| `D001_ISI50` | `cells/D001_ISI50/` | 0.001 | 8.3 мс | 120.48 | |
| `D001_ISI25` | `cells/D001_ISI25/` | 0.001 | 4.2 мс | 238.10 | лучший sep на ISI25 |

Общее: `SecretionTC=0.001`, `Delay=0.05`, GlobalTimeStep=2000.

## Результаты — синапс dual-pulse

| cell | D | ISI | sep | gate |
|------|---|-----|-----|------|
| `D005_ISI100` | 0.005 | 16.7 мс | 0.96 | PASS |
| `D005_ISI50` | 0.005 | 8.3 мс | 0.77 | PASS |
| `D005_ISI25` | 0.005 | 4.2 мс | **0.47** | PASS (на грани) |
| `D002_ISI25` | 0.002 | 4.2 мс | 0.82 | PASS |
| `D001_ISI25` | 0.001 | 4.2 мс | **0.98** | PASS |

На уровне **синапса** Bio D=5 мс ещё проходит ISI25, но с малым запасом. D=0.001–0.002 дают комфортный sep.

## Каталог ячеек — канал (справочно)

Standalone `NPExcChannelBio`, `FBResistance=1e7`, dual-pulse на ISI25 (`Frequency≈238.1`), `Delay=0.2`.

| cell | Путь | Dissoc | Capacity | Описание |
|------|------|--------|----------|----------|
| `CH_D001_C1e9_ISI25` | `cells/CH_D001_C1e9_ISI25/` | 0.001 | 1e-9 | Bio C |
| `CH_D001_C5e10_ISI25` | `cells/CH_D001_C5e10_ISI25/` | 0.001 | 5e-10 | |
| `CH_D001_C25e11_ISI25` | `cells/CH_D001_C25e11_ISI25/` | 0.001 | 2.5e-10 | целевой C |
| `CH_D001_C1e10_ISI25` | `cells/CH_D001_C1e10_ISI25/` | 0.001 | 1e-10 | |

Без мембраны-owner доминирует релаксация −1→0; детект sep по детренду ненадёжен. Опора на τ из ChannelRcSweep: C≤2.5e-10.

## Рабочая пара для StructTrain

**DissociationTC=0.002, Capacity=2.5e-10** → класс `NSPNeuronGenD002C25e11`  
(альтернатива D=0.001: `NSPNeuronGenD001C25e11`).
