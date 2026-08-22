# SelectivityFastSpan — REPORT

Проверка сжатых span **100 / 50 / 25 мс** с парой **(DissociationTC=0.002, Capacity=2.5e-10)** на Train **и** Test.  
Каталог: `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/`.  
Мета: `grid_cells.tsv`, сводка: `grid_summary.csv`, лог: `run_fastspan_rerun.log`.

## Invalidation (прогон до 2026-08-22)

Предыдущие цифры R1 **не использовать**:

| Проблема | Следствие |
|----------|-----------|
| `NSPNeuronGenPreinh2_5` без UED/D/C | Preinh Train/Test считали Bio EPSP (D=5 мс, C=1e-9), только k=2.5 |
| R1 Test Model не из Train (inject/sync ломался) | чужой L (напр. `12 11 7 1`) + Bio Dissoc на Test |
| `sync \|\| true` | ошибки глотались |

После фикса: UploadClass `NSPNeuronGenPreinh2_5D002C25e11`, fail-hard sync, `verify_element_params.py` (все Dissoc=0.002, Cap=2.5e-10).

## Общий протокол (rerun)

| Параметр | Cold / протокол |
|----------|-----------------|
| Эталон | `[0.01, 0.08, 0.16, 0.24]` с → α=T/0.48, floor ISI 1.5 мс |
| Cold TipR / L | `86e6×4` / `1 1 1 1` |
| `ResistanceAdjustGain` | 0.4 |
| `Delay` (learner) | 1.5 |
| Train / Test | `-t 160 -S` / `-t 20` |
| Gate | target_hit + Acc≥4 + не fire_all |

Сжатые паттерны:

| span T | InputPattern (с) | SyncTol | PeakMeasureMargin |
|--------|------------------|---------|-------------------|
| 100 мс | `0.0015, 0.003472, 0.006944, 0.010417` | 0.004167 | 0.005833 |
| 50 мс | `0.0015, 0.001736, 0.003472, 0.005208` | 0.002083 | 0.002917 |
| 25 мс | `0.0015, 0.0015, 0.001736, 0.002604` | 0.0015 | 0.002 |

## Классы нейронов (факт UploadClass)

### `NSPNeuronGenD002C25e11` (fast / fast_ts10k)

| Параметр | Значение |
|----------|----------|
| `UseElementDefaults` | true |
| `SynapseDissociationTC` | **0.002** с |
| `MembraneCapacity` | **2.5e-10** |
| Мембрана | `NPMembraneBio` |
| Tip-синапсы | `NPSynapseBio` |

### `NSPNeuronGenPreinh2_5D002C25e11` (preinh / preinh_ts10k)

| Параметр | Значение |
|----------|----------|
| `MembraneClassName` | `NPMembraneBioPreinh2_5` |
| Tip-синапсы | `NPSynapseBioPreinh2_5`, `InhibitionCoeff=2.5` |
| `UseElementDefaults` | true |
| `SynapseDissociationTC` | **0.002** с |
| `MembraneCapacity` | **2.5e-10** |

Verify после Train/sync (все 8 EXP): Dissoc×N=0.002, Cap×N=2.5e-10; preinh — InhCoeff=2.5; L Train≡Test Model.

## Каталог EXP и результаты (rerun 2026-08-22)

| EXP | NeuronClass | span | GlobalTS | FixedLTZ | Acc | mode | gate | L после Train |
|-----|-------------|------|----------|----------|-----|------|------|---------------|
| `EXP_span100ms_fast` | `NSPNeuronGenD002C25e11` | 100 | 2000 | ~0.0147 | 1/8 | fire_all | FAIL | 2 1 2 1 |
| `EXP_span100ms_fast_preinh` | `…Preinh2_5D002C25e11` | 100 | 2000 | ~0.0144 | 1/8 | fire_all | FAIL | 3 1 3 1 |
| `EXP_span50ms_fast` | `NSPNeuronGenD002C25e11` | 50 | 2000 | 0.05 | 1/8 | fire_all | FAIL | 2 1 1 1 |
| `EXP_span50ms_fast_preinh` | `…Preinh2_5D002C25e11` | 50 | 2000 | ~0.0185 | 1/8 | fire_all | FAIL | 3 1 1 1 |
| `EXP_span25ms_fast` | `NSPNeuronGenD002C25e11` | 25 | 2000 | ~0.0147 | 1/8 | fire_all | FAIL | 3 1 1 1 |
| `EXP_span25ms_fast_preinh` | `…Preinh2_5D002C25e11` | 25 | 2000 | ~0.032 | 1/8 | fire_all | FAIL | 3 1 1 1 |
| `EXP_span25ms_fast_ts10k` | `NSPNeuronGenD002C25e11` | 25 | **10000** | **0.04** | 1/8 | fire_all | FAIL | 3 1 1 1 |
| `EXP_span25ms_fast_preinh_ts10k` | `…Preinh2_5D002C25e11` | 25 | **10000** | **0.04** | 1/8 | fire_all | FAIL | 3 1 1 1 |

Target hit есть (fp=7): после обучения сома отвечает на все короткие паттерны.

## Вывод

Даже при **подтверждённых** узких EPSP (D=0.002, C=2.5e-10) на Train и Test, с Preinh k=2.5 и при dt=0.1 мс (ts10k), quality-gate селективности на span ≤100 мс **не** достигается (`fire_all`). Ускорение синапса/мембраны необходимо, но недостаточно для текущего learner+tip протокола.

Следующие направления: различение по форме/таймингу пиков (не только sum), сильнее Preinh k, другой tip R / число дендритов, или смена задачи селективности под короткие span.

## Команды

```bash
./scripts/setup_fastspan.sh
MAX_JOBS=4 ./scripts/run_fastspan.sh   # verify D/C после Train и после sync
```
