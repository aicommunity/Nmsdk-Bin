# NNeuronTimeLearner — алгоритм обучения

Обучение временного паттерна: один burst `NDatasetMatrix` (fan-out `Generator1`) на все дендриты; **joint train** — one-dendrite-per-burst подбор длины плюс нормализация амплитуд синапсами (как `NNeuronLearner`).

Реализация: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp).

## Wiring

```
DatasetMatrix.Generator1.Output
        │ fan-out
        ├─► Dendrite1_{L1}.ExcSynapse*
        ├─► Dendrite2_{L2}.ExcSynapse*
        ├─► …
        └─► DendriteN_{LN}.ExcSynapse*   (якорь длины, обычно L=1)
```

- `InputPattern` / `MatrixData`: ISI-слоты `N×1`. Относительно **первого импульса** (`FirstImpulseTime`): `Expected = [0, ISI_1, ISI_1+ISI_2, …]` (пример `0.01,0.08,0.16,0.24` → `[0, 0.08, 0.24, 0.48]`).
- После роста: tip-only link; proximal `Input` отсоединяется.

## Фазы

| Phase | Имя | Действие |
|-------|-----|----------|
| 0 | Joint train | Длина активного дендрита + синапсы всех сом |
| 1 | (legacy) | Не выставляется |
| 2 | Done | `TrainingPattern` / индексы на нейроне |

`EndOfLearning` → Done при `AllDendritesSynced() ∧ AllSynapsesNormalized()` (без Sync→Normalize).

**Два контура:**

1. **Length settle (sync):** `|sync_dt| ≤ SyncTolerance` (или best-effort) → `DendStatus=0`, длины больше не меняются. Sample `[49,41,25,1]` — штатная cable-цель при `EstDelayPerSeg≈0.01` и `Expected=[0,0.08,0.24,0.48]`.
2. **Amp normalize:** после settle — parametric R (damped-P). Опора `N−1` **не** участвует в R-tune и **не** блокирует `AllSynapsesNormalized` (как в `AllDendritesSynced`).

Feedforward `r_model` — ориентир, не hard floor: при `amp < Initial` feedback может снижать R ниже модели до `ResistanceMin`.

## Итерация

1. `EffectiveIterationGap = max(IterationGap, span+settle+slack)`.
2. `BeginTrainingIteration` — cumsum ISI.
3. `MeasureMaxPotentialAndTime`: для `i < N−1` окно ±margin вокруг `Expected[i]+(L_i−1)·EstDelayPerSeg`, не заходя в зону пика следующего импульса; эталон — `pattern_end+settle`.
4. `FinishTrainingIteration`:
   - bootstrap, пока нет **valid ref peak** (`HasPrevPeakSnapshot` только при `PrevPeakValid[ref]`) — **без роста**;
   - иначе `ChangeDendriteStatus(active)` → `RefreshDendLastAbsDtFromPrevAnchor` → `ChangeSynapseStatus` для всех;
   - apply: длина, затем синапсы на новом tip;
   - `CommitPrevPeakSnapshot` (Prev копируется всегда; флаг HasPrev — только если ref valid).

## Критерий длины

```
needed[k] = PrevPeakRel[ref] - Expected[k]
delay_len = (L-1)·EstDelayPerSeg
delay_use = DelayFromPulse  если согласован с delay_len / peak_model (±margin)
          иначе delay_len
dt = needed - delay_use
```

**Гейты:** нет `peakValid` у активного дендрита → `DendStatus=0` (не ΔL). Нет valid Prev ref → не ΔL. Invalid/dead tip: только accept/best-effort при `|needed−delay_len|≤tol` или amp-collapse@cap — **без** `DendStatus=±1`.

`ApplyPending`: `ΔL ≈ |dt|/EstDelayPerSeg`, cap `kMaxLengthStep`, **anti-overshoot**; при провале tip-link — один `Build`+Relink retry.

Ожидание sample: `L0 > L1 > L2 > L3=1` (~49 / ~41 / ~25 / 1).

## Нормализация синапсов

Цель: `MaxIterSomaAmp[i] → InitialSomaPotential[i]` (захват **только при L==1** на полном пике).

### Режимы (`NormalizationMode`)

| Mode | Имя | `NumSynapse` | Механизм | Done |
|------|-----|--------------|----------|------|
| 0 | Structural | 1…128 | ±`NumSynapse`, extra `R = SynapseResistanceStep` | amp≈Initial или best-effort@128 |
| 1 | Parametric | всегда 1 | feedforward `R *= exp(-γ·ΔL)` + damped-P feedback на tip `ExcSynapse1` | amp≈Initial или best-effort@oscillation/`ResistanceMin` |

**Structural (0):**

- Пока `Initial<=0` — синапсы не меняются (`SynapseStatus=0`).
- `kMaxSynapsesPerDend = 128` (экспериментальный потолок).
- `AllSynapsesNormalized`: amp в ε от Initial **или** best-effort@cap **или** dead tip (`amp < 1e-6`) при уже синхронизированной длине.

**Parametric (1, по умолчанию в `ADefault`):**

- `TipSynapseResistance[i]` — сопротивление tip-синапса; сохраняется в `Parameters_00.xml`.
- **Sync-first:** пока длина дендрита не синхронизирована (`lastAbsDt > SyncTolerance` или `DendStatus≠0`), feedback по R **не применяется**; только feedforward при росте L.
- Feedforward при росте длины: `R_new = R_old · exp(-γ·ΔL)`; `AttenuationGamma <= 0` → авто-оценка из `amp/Initial`, fallback `0.05`.
- **Damped-P feedback** (после sync длины): `step_ratio = 1 + gain·(amp/Initial − 1)`, где `gain = ResistanceAdjustGain` (default **0.4**). Adaptive gain: sign-flip → `×0.5`, недобор ×2 → `×1.5`. **Не PID** — один параметр Kp, без I/D (задержка 1 burst). При `amp < Initial` шаг может идти **ниже** feedforward `r_model` (пол — только `ResistanceMin`). Пока `|ampDt| > ε` feedback продолжается (не останавливается на частичном улучшении); маленький `|ΔR|/R` всё равно применяется к tip.
- `ResistanceStatus=0` (settle) при `|ΔR|/R < 1e-3`.
- `AllSynapsesNormalized`: только дендриты `0..N-2` (опора исключена). amp в ε **и** `length_ok` **или** best-effort@`ResistanceMin` **или** oscillation band (`|dt| < 0.005`, 3 iter без улучшения) **или** dead tip — все пути требуют синхронизированную длину.
- Переключение structural→parametric mid-train (большой `NumSynapse`) требует rebuild; **рекомендуется** `ResetToUntrainedState=1`.

Параметры parametric: `SynapseResistanceBase` (8.6e7), `ResistanceMin` (1e6), `ResistanceMax` (1e11), `AttenuationGamma` (-1 = auto), `ResistanceAdjustGain` (0.4).

- `AllDendritesSynced`: dead tip + `|needed−delay_len|≤tol` / best-effort — без требования `peakValid`.
- На более длинных дендритах в structural обычно больше синапсов; полный cap может потребовать `-t 120+`. Parametric обычно сходится быстрее (<80 iter).

## Параметры sample

| Параметр | Значение |
|----------|----------|
| `NumInputDendrite` | 4 |
| `InputPattern` | `0.01, 0.08, 0.16, 0.24` |
| `IterationGap` / `Delay` | 1.5 s |
| `SyncTolerance` | 0.02 s |
| `NeuronClassName` | `NSPNeuronGen` |

Прогон обучения: `NeuroModelerConsole -c …/Project.ini -s -t 160 -x` (warm на settled L; cold-рост L — отдельный сценарий).

Осциллограммы / ход нормализации: `UStatisticDoubleMatrix` → `StatisticLog/<timestamp>/`:

- `NeuronTimeLearner.SomaNeuronAmplitude.txt`
- `NeuronTimeLearner.AmpDtTrace.txt`, `TipSynapseResistanceTrace.txt`
- `ResistanceStatusTrace.txt`, `NoImproveResistanceTrace.txt`, `EffectiveGainTrace.txt`
- `DendriteLengthTrace.txt`, `LastAbsDtTrace.txt`, `StimulusIterTrace.txt`

Debug: `DampedResistance`, `ResistanceFloor` (шаг ниже `r_model`), `phase -> Done`.

## Known limitations

- При сильной attenuation даже 128 tip-синапсов могут не дотянуть amp до Initial → best-effort Done.
- Fan-out на все дендриты даёт кросс-пики на других ISI; критерий H1 — отсутствие пары пиков sync с Δt≈0.08 (L0≈L1), а не отсутствие любых вторичных пиков.
- Warning `PrepareDataset rejected data on Dataset` — файловый `NDataset`, не `DatasetMatrix` sample.
