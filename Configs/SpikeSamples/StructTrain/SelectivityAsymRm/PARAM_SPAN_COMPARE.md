# AsymRm: параметры 25 vs 50 vs 100 мс

Дата: 2026-09-08. Источник: Train `Parameters_00.xml` на диске.

## Главный вывод

**`SynapseDissociationTC` (D), `MembraneCapacity` (C), Rm/Rsyn внутри пакета одинаковы для всех span.**  
Со span масштабируются только ISI (`InputPattern`) и окна `PeakMeasureMargin` / `SyncTolerance` (Test; Train SyncTol иногда шире).

Это согласуется с гипотезой: временная динамика EPSP подобрана под ~25 мс; на 50/100 при том же D отношение EPSP/ISI ухудшает разделение → `fire_all` на Done; Pack C gen 50/100 stall — отдельный слой (amp_dt), не другие D/C.

## Таблица (pack A gen)

| Тег | span25 | span50 | span100 |
|-----|--------|--------|---------|
| `SynapseDissociationTC` | **0.001** | **0.001** | **0.001** |
| `SynapseSecretionTC` | 0.001 | 0.001 | 0.001 |
| `MembraneCapacity` | 2.5e−11 | 2.5e−11 | 2.5e−11 |
| `ExcMembraneResistance` | 1e7 | 1e7 | 1e7 |
| `PeakMeasureMargin` | 0.002 | ≈0.00292 | ≈0.00583 |
| `SyncTolerance` (Train) | 0.0025 | 0.005 | ≈0.00417 |
| `DendriteLength` | 6 5 4 1 | 11 9 7 1 | 21 17 11 1 |
| `FixedLTZThreshold` | ≈0.087 | 0.100 | 0.100 |
| `IsNeedToTrain` | 0 | 0 | 0 |
| Test gate (2026-09-08) | **PASS 6/8** | fire_all 1/8 | fire_all 1/8 |

## Pack C gen (сравнение Done 25 vs stuck 50/100)

| Тег | span25 (Done) | span50 (stuck) | span100 (stuck) |
|-----|---------------|----------------|-----------------|
| D / C | 0.001 / 2.5e−11 | то же | то же |
| `ExcMembraneResistance` | 5e6 | 5e6 | 5e6 |
| `FixedLTZThreshold` | ≈0.086 | **0.0115 cold** | **0.0115 cold** |
| `IsNeedToTrain` | 0 | **1** | **1** |
| `InitialSomaPotential` d0–2 | ≈0.100 | ≈**0.042** | ≈**0.042** |

Setup: [`scripts/setup_asymrm.sh`](scripts/setup_asymrm.sh) всегда пишет D=`0.001`. Scale ISI/Peak: [`scripts/patch_pattern_scale.py`](scripts/patch_pattern_scale.py).

## Пилоты (новые EXP, оригиналы не трогать)

| Новый EXP | Источник | Изменение | Итог |
|-----------|----------|-----------|------|
| `EXP_span50ms_packA_gen_Dspan` | packA gen 50 | D=**0.002** cold | Need=1, amp pathology (abort) |
| `EXP_span100ms_packA_gen_Dspan` | packA gen 100 | D=**0.004** cold | Done, test **fire_all** 1/8 |
| `EXP_span50ms_packC_gen_ampaudit` | packC gen 50 stuck | AmpDtAudit | ≥66 событий; TipR skip `|dt|>5` |
| `EXP_span100ms_packC_gen_ampaudit` | packC gen 100 stuck | AmpDtAudit | 0 событий за T=80 |

См. `grid_cells_pilot.tsv`, `SELECTIVITY_REPORT.md`, `PACKC_GEN_DIAGNOSIS.md`.
