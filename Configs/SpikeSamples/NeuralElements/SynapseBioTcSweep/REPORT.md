# SynapseBioTcSweep — REPORT R1

Одиночный `NPSynapseBio`: ширина EPSP vs `DissociationTC`.  
Каталог: `Bin/Configs/SpikeSamples/NeuralElements/SynapseBioTcSweep/`.  
Ячейки: `cells/<name>/` (`Model_00.xml`, `Parameters_00.xml`, `project.ini`).

## Общий протокол

| Параметр | Значение |
|----------|----------|
| Элемент | `NPSynapseBio` (standalone) |
| `GlobalTimeStep` | **2000** (dt 0.5 мс) |
| `SecretionTC` | **0.001** с (1 мс) |
| Стимул | pulse **1 мс** @ `Delay=0.05` с |
| `Frequency` | **2 Hz** |
| `SIM_T` | 3 с (`NeuroModelerConsole -s -t 3 -x`) |
| Метрика | FWHM / t_tail10 / peak первого пика Output |
| Gate | FWHM ≤ **2.1 мс** (= 0.5·min_ISI(25 мс)); steps/τ ≥ 2 желательно |

## Каталог ячеек

| cell | Путь | `DissociationTC` | Описание |
|------|------|------------------|----------|
| `D005` | `cells/D005/` | **0.005** с (Bio default) | эталон Bio, ожидаемо широкий |
| `D002` | `cells/D002/` | **0.002** с | кандидат FastSpan |
| `D001` | `cells/D001/` | **0.001** с | FWHM-gate PASS |
| `D0005` | `cells/D0005/` | **0.0005** с | узкий, но 1 шаг на τ при TS=2000 |

Общее для всех ячеек: `SecretionTC=0.001`, `Frequency=2`, `Delay=0.05`, GlobalTimeStep=2000.

## Метрики (первый пик)

| cell | Dissoc | steps/τ | FWHM (мс) | t_tail10 (мс) | peak (Output) | gate FWHM≤2.1 мс |
|------|--------|---------|-----------|---------------|---------------|------------------|
| `D005` | 0.005 | 10 | **4.5** | 11.0 | ~8.7e-9 | FAIL |
| `D002` | 0.002 | 4 | **2.5** | 4.5 | ~8.7e-9 | FAIL |
| `D001` | 0.001 | 2 | **2.0** | 2.0 | ~8.7e-9 | **PASS** (на грани steps) |
| `D0005` | 0.0005 | 1 | **1.5** | 0.5 | ~8.7e-9 | PASS FWHM / **FAIL steps** (VDissoc=1) |

Тренд: меньше DissociationTC → уже FWHM. Bio 5 мс **не** совместим с ISI(25 мс)≈4.2 мс.

## Рекомендация

Рабочий ориентир синапса: **DissociationTC = 0.001 с** (1 мс). D=0.0005 не использовать при TimeStep=2000.

R2 не требуется для FWHM-gate; опционально `D001_ts10k` при нестабильности на TipEps.
