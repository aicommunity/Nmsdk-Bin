# SelectivityFastResponse — отчёт (этап 1)

Сетка **DissociationTC × MembraneCapacity** для ускорения EPSP у `NNeuronTimeLearner` без смены Rm/Rsyn.  
Каталог: `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastResponse/`.  
Мета: `grid_cells.tsv`, сводка: `grid_summary.csv`. Setup: `scripts/setup_grid.sh`, прогон: `scripts/run_grid.sh`.

**Контрольный аудит паттернов (2026-08-23):** все 9 EXP Train/Test — `InputPattern = [0.01, 0.08, 0.16, 0.24]` с, learner span 480 мс; ошибок масштабирования нет (в отличие от FastSpan до fix).

## API (PulseLib)

На `NPulseNeuron` (opt-in, default off):

| Свойство | Default | Смысл |
|----------|---------|--------|
| `UseElementDefaults` | `false` | Включить override дочерних C/TC |
| `MembraneCapacity` | `0` (≤0 = не трогать) | Capacity Exc/Inh каналов Soma+Dendrite |
| `SynapseDissociationTC` | `0` (≤0 = не трогать) | DissociationTC Exc/Inh синапсов |

`ApplyElementDefaults()` — в конце `NPulseNeuron::ABuild` (после `Common::ABuild`, когда TimeStep уже задан).  
`NSPNeuronGen` без флага — поведение старых моделей не меняется.

UploadClass (имена без `_`), регистрация в `NPulseLibrary`:

| UploadClass | DissociationTC | MembraneCapacity |
|-------------|----------------|------------------|
| `NSPNeuronGen` (ctrl) | Bio default 0.005 | Bio default ~1e-9 |
| `NSPNeuronGenD005C5e10` | 0.005 | 5e-10 |
| `NSPNeuronGenD005C25e11` | 0.005 | **5e-10**† |
| `NSPNeuronGenD002C1e9` | 0.002 | 1e-9 |
| `NSPNeuronGenD002C5e10` | 0.002 | 5e-10 |
| `NSPNeuronGenD002C25e11` | 0.002 | 2.5e-10 |
| `NSPNeuronGenD001C1e9` | 0.001 | 1e-9 |
| `NSPNeuronGenD001C5e10` | 0.001 | 5e-10 |
| `NSPNeuronGenD001C25e11` | 0.001 | 2.5e-10 |

† В коде UploadClass для `D005C25e11` сейчас записано `5e-10` (как у `C5e10`), не `2.5e-10`. В `grid_cells.tsv` intent = 2.5e-10; метрики `EXPD005C25e11` совпали с `EXPD005C5e10` — фактически дубль ячейки C=5e-10.

## Общий протокол Train/Test (все EXP)

| Параметр | Значение |
|----------|----------|
| Паттерн | несжатый эталон `[0.01, 0.08, 0.16, 0.24]` с (span 0.48 с) |
| `SynapseClassName` | `NPSynapseBio` |
| Cold TipR | `86e6 × 4` |
| Cold L / parts | `1 1 1 1` |
| `SyncTolerance` | **0.01** |
| `PeakMeasureMargin` | **0.06** |
| `FixedLTZThreshold` | **0.0115** |
| `TrainingLTZThreshold` | `100` |
| `UseAverageLTZonePotential` | `1` |
| `ResistanceAdjustGain` | `0.4` |
| `Delay` (learner) | `1.5` |
| `ResetToUntrainedState` | `1` |
| `GlobalTimeStep` | 2000 (dt 0.5 мс) |
| Train / Test | `-t 160 -S` (или 240) / `-t 20` |
| Gate `train_ok` | trial0 target `neuron_fired==1` |

Cold Train (важно): в шаблоне `Model_00.xml` есть встроенный `NeuronClassName=NSPNeuronGen`. Если не переписать, первый `BuildStructure` собирает Gen, затем класс меняется — tip-links ломаются (`amp=0`).  
`setup_grid.sh` патчит Parameters и Model: Neuron Class, `NeuronClassName`, L=1, TipR=86e6×4.

## Каталог EXP

| EXP | NeuronClassName | D (с) | C | UseElementDefaults | Описание |
|-----|-----------------|-------|---|--------------------|----------|
| `EXP00CtrlExp04` | `NSPNeuronGen` | 0.005† | ~1e-9† | `0` | контроль PhaseA EXP04; Bio defaults |
| `EXPD005C5e10` | `NSPNeuronGenD005C5e10` | 0.005 | 5e-10 | `1` | только C↓ при Bio Dissoc |
| `EXPD005C25e11` | `NSPNeuronGenD005C25e11` | 0.005 | intent 2.5e-10 / факт 5e-10 | `1` | см. сноску UploadClass † |
| `EXPD002C1e9` | `NSPNeuronGenD002C1e9` | 0.002 | 1e-9 | `1` | D↓ без C↓ |
| `EXPD002C5e10` | `NSPNeuronGenD002C5e10` | 0.002 | 5e-10 | `1` | |
| `EXPD002C25e11` | `NSPNeuronGenD002C25e11` | 0.002 | 2.5e-10 | `1` | лучший t_peak |
| `EXPD001C1e9` | `NSPNeuronGenD001C1e9` | 0.001 | 1e-9 | `1` | D↓↓ без C↓ |
| `EXPD001C5e10` | `NSPNeuronGenD001C5e10` | 0.001 | 5e-10 | `1` | |
| `EXPD001C25e11` | `NSPNeuronGenD001C25e11` | 0.001 | 2.5e-10 | `1` | 2-й по t_peak |

† Ctrl: D/C не задаются через API; Bio Dissoc=5 мс, Capacity канала ~1e-9.

Пути: `…/SelectivityFastResponse/<EXP>/{Train,Test}/` — `Parameters_00.xml`, `Model_00.xml`, `Project.ini`.

## Сводка (`grid_summary.csv`)

| exp | D | C | train_ok | acc | fn/fp | t_peak | Δt vs ctrl | L после Train |
|-----|---|---|----------|-----|-------|--------|------------|---------------|
| `EXP00CtrlExp04` | 0.005 | 1e-9 | 1 | 1/8 | 0/7 | 0.089 | 0 | 50 42 26 1 |
| `EXPD005C5e10` | 0.005 | 5e-10 | 1 | 1/8 | 0/7 | 0.065 | −0.024 | 49 41 25 1 |
| `EXPD005C25e11` | 0.005 | 2.5e-10‡ | 1 | 1/8 | 0/7 | 0.065 | −0.024 | 49 41 25 1 |
| `EXPD002C1e9` | 0.002 | 1e-9 | **0** | 7/8 | 1/0 | — | брак | 51 42 26 1 |
| `EXPD002C5e10` | 0.002 | 5e-10 | 1 | 1/8 | 0/7 | 0.0785 | −0.0105 | 50 41 25 1 |
| `EXPD002C25e11` | 0.002 | 2.5e-10 | 1 | 1/8 | 0/7 | **0.0295** | **−0.0595** | 52 44 25 1 |
| `EXPD001C1e9` | 0.001 | 1e-9 | **0** | 7/8 | 1/0 | — | брак | 50 42 26 1 |
| `EXPD001C5e10` | 0.001 | 5e-10 | 1 | 1/8 | 0/7 | 0.076 | −0.013 | 52 41 25 1 |
| `EXPD001C25e11` | 0.001 | 2.5e-10 | 1 | 1/8 | 0/7 | 0.0345 | −0.0545 | 53 33 25 1 |

‡ Intent в TSV; фактический UploadClass/XML Capacity = 5e-10 (дубль `EXPD005C5e10`).

## Выводы

1. **Меньше C ускоряет ответ** при том же D: ctrl 0.089 → C=5e-10 ≈0.065; C=2.5e-10 ещё быстрее на части ячеек.
2. **Лучшие по (train_ok, ↓t_peak):** `EXPD002C25e11` (0.0295) и `EXPD001C25e11` (0.0345).
3. **Брак:** D↓ при C=1e-9 (`EXPD002C1e9`, `EXPD001C1e9`) — target не стреляет (`train_ok=0`); одного снижения DissociationTC без снижения C недостаточно / вредно на cold TipR.
4. **Селективность:** у всех `train_ok=1` ячеек acc=1/8 при fp=7 (перестрел nontarget). Этап 1 измерял latency/gate fire; калибровка SyncTol/порога — отдельно (как PhaseA EXP04 фон уже 0.01).

## Рекомендации (этап 1)

- Для ускорения: **C ≈ 2.5e-10…5e-10** при D ∈ {0.002, 0.005}; ориентир `NSPNeuronGenD002C25e11` / конфиг `EXPD002C25e11`.
- Не ставить D=0.001/0.002 при C=1e-9 без доп. калибровки.
- Rm/Rsyn не трогать независимо (этап 1).
- Исправить UploadClass `NSPNeuronGenD005C25e11` → C=2.5e-10, если нужна отдельная точка сетки.

## Сноска Exc/Inh

Асимметрия возбуждения/торможения (GABAA vs AMPA, Cm у PV+) в этапе 1 не моделировалась: Exc и Inh получают одинаковые C и DissociationTC. Возможный следующий шаг — раздельные overrides.

## Команды

```bash
./scripts/setup_grid.sh
./scripts/run_grid.sh          # TRAIN_T=240 при необходимости
```
