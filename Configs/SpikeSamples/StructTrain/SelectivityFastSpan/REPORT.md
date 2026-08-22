# SelectivityFastSpan — REPORT

Проверка сжатых span **100 / 50 / 25 мс** с быстрыми элементами и Preinh2_5.  
Каталог: `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/`.  
Мета: `grid_cells.tsv`, сводка: `grid_summary.csv`. Setup: `scripts/setup_fastspan.sh`, прогон: `scripts/run_fastspan.sh`.

## Общий протокол (все EXP)

| Параметр | Cold (до Train) | Примечание |
|----------|-----------------|------------|
| Источник шаблона | time-compress PresynapticInhib (span-базлайн) | паттерн + margins через `patch_pattern_scale.py` |
| Эталон | `InputPattern = [0.01, 0.08, 0.16, 0.24]` с, span 0.48 с | сжатие `α = T/0.48`, floor ISI **1.5 мс** |
| `SynapseClassName` (learner) | `NPSynapseBio` | tip-синапсы — по классу нейрона |
| Cold `TipSynapseResistance` | `86e6 × 4` | после Train — выученные R |
| Cold `DendriteLength` / `NumDendriteMembranePartsVec` | `1 1 1 1` | колонка L в таблице — **после** Train |
| `ResistanceAdjustGain` | `0.4` | |
| `Delay` (learner) | `1.5` | |
| `TrainingLTZThreshold` | `100` | |
| `StructureBuildMode` | `1` (cold Train) | |
| `ResetToUntrainedState` | `1` | cold start |
| Train / Test | `-t 160 -S` / `-t 20` | quality-gate: Acc и mode |
| Gate | `train_ok` + не `fire_all` | target_hit=1 при fp=7 → FAIL |

Сжатые паттерны и margins (`patch_pattern_scale.py`):

| span T | α | `InputPattern` (с) | SyncTol | PeakMeasureMargin |
|--------|---|--------------------|---------|-------------------|
| 100 мс | 0.2083 | `0.0015, 0.003472, 0.006944, 0.010417` | 0.004167 | 0.005833 |
| 50 мс | 0.1042 | `0.0015, 0.001736, 0.003472, 0.005208` | 0.002083 | 0.002917 |
| 25 мс | 0.0521 | `0.0015, 0.0015, 0.001736, 0.002604` | 0.0015 | 0.002 |

## Классы нейронов

### `NSPNeuronGenD002C25e11` (kind=`fast`)

| Параметр | Значение |
|----------|----------|
| Описание | UploadClass fast-grid: узкий EPSP без Preinh |
| `UseElementDefaults` | `1` |
| `SynapseDissociationTC` | **0.002** с (2 мс) |
| `MembraneCapacity` | **2.5e-10** (Exc/Inh Soma+Dendrite) |
| Мембрана | `NPMembraneBio` |
| Tip-синапсы | `NPSynapseBio` (без Preinh) |
| Источник | `NPulseLibrary` FastCell `{0.002, 2.5e-10}` |

### `NSPNeuronGenPreinh2_5` (kind=`preinh`)

| Параметр | Значение |
|----------|----------|
| Описание | Preinh k=2.5 + intended те же D/C overrides, что у fast |
| `MembraneClassName` | `NPMembraneBioPreinh2_5` |
| Tip-синапсы | `NPSynapseBioPreinh2_5` |
| `UsePresynapticInhibition` | `1` |
| `InhibitionCoeff` | **2.5** |
| Cold intent (`setup_fastspan.sh`) | `UseElementDefaults=1`, D=`0.002`, C=`2.5e-10` |
| Bio defaults без override | Dissoc 5 мс, C 1e-9 | если UED не применился |

## Каталог EXP

### R1 — `GlobalTimeStep=2000` (dt 0.5 мс)

| EXP | Класс | span | kind | Описание |
|-----|-------|------|------|----------|
| `EXP_span100ms_fast` | `NSPNeuronGenD002C25e11` | 100 мс | fast | сжатый span + fast D/C |
| `EXP_span100ms_fast_preinh` | `NSPNeuronGenPreinh2_5` | 100 мс | preinh | то же + Preinh k=2.5 |
| `EXP_span50ms_fast` | `NSPNeuronGenD002C25e11` | 50 мс | fast | |
| `EXP_span50ms_fast_preinh` | `NSPNeuronGenPreinh2_5` | 50 мс | preinh | |
| `EXP_span25ms_fast` | `NSPNeuronGenD002C25e11` | 25 мс | fast | |
| `EXP_span25ms_fast_preinh` | `NSPNeuronGenPreinh2_5` | 25 мс | preinh | |

Ключевые параметры по ячейкам (после Train: L и FixedLTZ из логов; паттерн/margins — cold):

| EXP | D / C (intent) | GlobalTS | SyncTol | PeakMargin | FixedLTZ (после Train) | L после Train |
|-----|----------------|----------|---------|------------|------------------------|---------------|
| `EXP_span100ms_fast` | 0.002 / 2.5e-10 | 2000 | 0.004167 | 0.005833 | ~0.0147 | 4 3 2 1 |
| `EXP_span100ms_fast_preinh` | 0.002 / 2.5e-10 + k=2.5 | 2000 | 0.004167 | 0.005833 | ~0.0144 | 5 4 4 1 |
| `EXP_span50ms_fast` | 0.002 / 2.5e-10 | 2000 | 0.002083 | 0.002917 | ~0.05 | 3 3 2 1† |
| `EXP_span50ms_fast_preinh` | 0.002 / 2.5e-10 + k=2.5 | 2000 | 0.002083 | 0.002917 | ~0.0185 | 4 4 4 1† |
| `EXP_span25ms_fast` | 0.002 / 2.5e-10 | 2000 | 0.0015 | 0.002 | ~0.0147 | 1 1 1 1† / 3 1 2 1 |
| `EXP_span25ms_fast_preinh` | 0.002 / 2.5e-10 + k=2.5 | 2000 | 0.0015 | 0.002 | ~0.032 | 4 1 4 1† |

† L в таблице результатов R1 из `run_fastspan.log`; в сохранённых XML после повторных прогонов L может отличаться.

### Эскалация — span25, `GlobalTimeStep=10000` + порог 0.04

| EXP | Класс | Отличие от R1 |
|-----|-------|----------------|
| `EXP_span25ms_fast_ts10k` | `NSPNeuronGenD002C25e11` | `Project.ini`: GlobalTimeStep/DefaultTimeStep=**10000**; `FixedLTZThreshold=0.04`; паттерн/Sync/Peak как у span25 |
| `EXP_span25ms_fast_preinh_ts10k` | `NSPNeuronGenPreinh2_5` | то же + Preinh k=2.5 |

## Элементный пререквизит (NeuralElements)

| Бенч | Каталог / ячейки | Вывод |
|------|------------------|--------|
| SynapseBioTcSweep | `NeuralElements/SynapseBioTcSweep/cells/D005…D0005` | FWHM gate 2.1 мс: D≤0.001; D=0.002 OK с запасом |
| ChannelRcSweep | `…/ChannelRcSweep/cells/3a_*`, `3b_*` | τ≈C·1e7; C≤2.5e-10 для τ≲2.5 мс |
| TipEps dual-pulse | `…/TipEpsCombined/cells/D*_ISI*` | sep≥0.30 на ISI25 для D∈{0.005…0.001} |

## Результаты R1 (GlobalTimeStep=2000)

| EXP | Acc | mode | gate | L (лог) |
|-----|-----|------|------|---------|
| `EXP_span100ms_fast` | 1/8 | fire_all | FAIL | 4 3 2 1 |
| `EXP_span100ms_fast_preinh` | 1/8 | fire_all | FAIL | 5 4 4 1 |
| `EXP_span50ms_fast` | 1/8 | fire_all | FAIL | 3 3 2 1 |
| `EXP_span50ms_fast_preinh` | 1/8 | fire_all | FAIL | 4 4 4 1 |
| `EXP_span25ms_fast` | 1/8 | fire_all | FAIL | 1 1 1 1 |
| `EXP_span25ms_fast_preinh` | 1/8 | fire_all | FAIL | 4 1 4 1 |

Target hit есть, nontarget тоже стреляет (fp=7).

## Эскалация

1. **Peak floor** (`NNeuronTimeLearner` / Branch): XML `PeakMeasureMargin` может быть уже cable floor; `kDelayPerSegDefault` 10→**5 мс**. Rebuild Console. Повтор 25/50: снова **fire_all**.
2. **`EXP_span25ms_*_ts10k`**: TimeStep=10000 + FixedLTZ=0.04 — снова **fire_all**.  
   `soma_amp_sum` ≈ 0.165–0.17 на **всех** trials (target и distractors).

| EXP | Acc | mode | FixedLTZ | L |
|-----|-----|------|----------|---|
| `EXP_span25ms_fast_ts10k` | 1/8 | fire_all | 0.04 | 3 1 2 1 |
| `EXP_span25ms_fast_preinh_ts10k` | 1/8 | fire_all | 0.04 | 3 1 2 1 |

## Вывод

Ускорение синапса/мембраны необходимо, но **недостаточно** для селективности на span ≤100 мс в текущем learner+tip протоколе: после обучения сома отвечает одинаково на все короткие паттерны. Следующие направления: различение по форме/таймингу пиков (не только sum), сильнее Preinh k, другой tip R / число дендритов, или смена задачи селективности под короткие span.

## Команды

```bash
./scripts/setup_fastspan.sh
MAX_JOBS=4 ./scripts/run_fastspan.sh
```
