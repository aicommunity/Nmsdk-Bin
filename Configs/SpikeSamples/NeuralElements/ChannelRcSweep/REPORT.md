# ChannelRcSweep — REPORT

`NPGenerator` → `NPSynapseBio` → `NPExcChannelBio` (standalone, без мембраны-owner).  
Каталог: `Bin/Configs/SpikeSamples/NeuralElements/ChannelRcSweep/`.  
Ячейки: `cells/3a_*` (Dissoc=Bio 5 мс), `cells/3b_*` (Dissoc=1 мс).

## Общий протокол

| Параметр | Значение |
|----------|----------|
| Канал | `NPExcChannelBio` |
| `FBResistance` | **1e7** Ω |
| Синапс | `NPSynapseBio`, `SecretionTC=0.001` |
| Стимул | pulse @ `Delay=0.05`, `Frequency=2` Hz |
| `GlobalTimeStep` | **2000** |
| Primary metric | **τ распада** Output после Reset (окно 0…40 мс до импульса) |
| Теория (G≈0) | `τ ≈ C · FBResistance` |

## Каталог ячеек

### Серия 3a — фиксированный Dissoc = 0.005 с

| cell | Путь | Capacity | DissociationTC | Описание |
|------|------|----------|----------------|----------|
| `3a_C1e9` | `cells/3a_C1e9/` | **1e-9** | 0.005 | Bio default C |
| `3a_C5e10` | `cells/3a_C5e10/` | **5e-10** | 0.005 | |
| `3a_C25e11` | `cells/3a_C25e11/` | **2.5e-10** | 0.005 | целевой τ≲2.5 мс |
| `3a_C1e10` | `cells/3a_C1e10/` | **1e-10** | 0.005 | очень быстрый RC |

### Серия 3b — фиксированный Dissoc = 0.001 с

| cell | Путь | Capacity | DissociationTC | Описание |
|------|------|----------|----------------|----------|
| `3b_C1e9` | `cells/3b_C1e9/` | **1e-9** | 0.001 | контроль: Dissoc не должен менять τ |
| `3b_C5e10` | `cells/3b_C5e10/` | **5e-10** | 0.001 | |
| `3b_C25e11` | `cells/3b_C25e11/` | **2.5e-10** | 0.001 | |
| `3b_C1e10` | `cells/3b_C1e10/` | **1e-10** | 0.001 | |
| `3b_C25e12` | `cells/3b_C25e12/` | **2.5e-11** | 0.001 | AsymRm Pack A fact (τ≈0.25 мс) |

Общее: `FBResistance=1e7`, `SecretionTC=0.001`, `Frequency=2`, `Delay=0.05`, GlobalTimeStep=2000.

## Результаты

| cell | D | C | τ_fit (мс) | τ_theory (мс) | ratio |
|------|---|---|------------|---------------|-------|
| `3a/3b_C1e9` | * | 1e-9 | 9.75 | 10.0 | 0.98 |
| `3a/3b_C5e10` | * | 5e-10 | 4.75 | 5.0 | 0.95 |
| `3a/3b_C25e11` | * | 2.5e-10 | **2.24** | 2.5 | 0.90 |
| `3a/3b_C1e10` | * | 1e-10 | 0.72 | 1.0 | 0.72 |
| `3b_C25e12` | 0.001 | 2.5e-11 | *(theory)* **0.25** | 0.25 | 1.0 |

Dissoc (3a vs 3b) на τ распада **не влияет** (как ожидалось до импульса).  
`3b_C25e12`: ячейка добавлена 2026-09-11 под AsymRm Pack A; τ_theory=0.25 мс — для полного τ_fit прогнать StatisticLog как у соседних cells.

## Gate для span 25 мс (ISI≈4.2 мс, EstDelayPerSeg≈5 мс)

После правки analyzer (in-window fire только post-last-stim) last-pulse crown требует, чтобы τ не была пренебрежимо мала относительно ошибки квантования L (~2.5 мс).

Выбранный gate: **`τ_fit ≥ 0.3 · EstDelayPerSeg` ≈ 1.5 мс** (совместимость с ошибкой ~1 сегмента при SyncTol).

| C | τ_theory | gate 1.5 мс |
|---|----------|-------------|
| 2.5e-11 (Pack A / C25e12) | 0.25 мс | **FAIL** |
| 1e-10 | 1.0 мс | FAIL |
| **2.5e-10 (C25e11)** | **2.5 мс** | **PASS** |
| 5e-10 | 5.0 мс | PASS (шире ISI) |

## Вывод (2026-09-11)

Для мембранного вклада ≲ 2.1 мс нужно **C ≤ 2.5e-10**. C=1e-9 (Bio default) даёт ~10 мс — несовместимо с ISI(25 мс).

Для **AsymRm span25 last-pulse**: не использовать Pack A C=2.5e-11. Рабочая точка:

- **`(D,C,RmExc)=(0.001, 2.5e-10, 1e7)`** → класс `NSPNeuronGenAsymRmD001C25e11`
- альтернатива FastResponse-стиль: `(0.002, 2.5e-10)` (`NSPNeuronGenD002C25e11`) без AsymRm

Синапс D=0.001 оставить (SynapseBioTcSweep).

Watch: AxisY на Channel −0.01…0.05; фактический сигнал −1→0 — rescale до −1.1…0.1 при GUI-просмотре (зафиксировано в journal).
