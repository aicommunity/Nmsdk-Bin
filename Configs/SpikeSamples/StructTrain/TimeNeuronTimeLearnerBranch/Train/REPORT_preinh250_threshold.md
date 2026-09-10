# PreInh250: порог CalibrateLtz vs recognition

Date: 2026-08-21  
Конфиги: [`TimeNeuronTimeLearnerBranch_PreInh250`](../TimeNeuronTimeLearnerBranch_PreInh250/) → [`TimeNeuronTimeLearnerBranchTest_PreInh250`](../TimeNeuronTimeLearnerBranchTest_PreInh250/)  
Сводный контекст: [`REPORT_ampeq_nextseginh.md`](REPORT_ampeq_nextseginh.md)

---

## Исходный симптом

После cold train + неполного sync Train→Test:

- CalibrateLtz: `peak≈0.1147` → `FixedLTZ≈0.1136` (`×0.99`)
- Test CSV: **fn на target**, `soma≈0.060` (~52% thr), `neuron_fired=0` на всех 8 trials
- Match **7/8** за счёт тишины nontarget (fp=0), но целевой паттерн не детектируется

---

## Гипотезы

| ID | Суть | Итог |
|----|------|------|
| H1 | Parallel-peak калибровки не воспроизводится на recognition | **Отклонена** при корректном sync: Done Train peak ≈0.114 ≈ FixedLTZ |
| H2 | PSI×amp-eq даёт краткий overshoot | Частично: tip0 (`R≈4e6`) доминирует по `C=4k/R`; tip3 ослаблен amp-eq — но пик стабилен на Done |
| H3 | `IterMaxSomaPotential` берёт транзиент | **Отклонена** (E7): CalibrateLtz ждёт `last_pulse+settle`, не early `all_locked` |
| H4 | Рассинхрон Test vs Train | **Подтверждена** — главный рычаг FN |
| H5 | Fraction 0.99 слишком жёсткий | **Не нужен** для FN: при sync target soma≈thr; E6 fraction-retrain не делали |

---

## Эксперименты

### E1 / E3 — ratio FixedLTZ vs target soma

| Эксп. | FixedLTZ | tgt soma (CSV) | ratio | fired |
|-------|---------:|---------------:|------:|------:|
| baseline | 0.0728 | 0.0728 | 1.00 | 1 |
| NextSegInh | 0.0650 | 0.0650 | 1.00 | 1 |
| PreInh250 (битый sync) | 0.1136 | 0.0599 | **0.53** | 0 |
| PreInh250 (полный sync) | 0.1136 | **0.1137** | **1.00** | 1 |

### E2 — FixedLTZ sweep (на **битом** Test, soma≈0.060)

Артефакт: `thr_sweep/summary.csv`. Рабочего окна «target fire + fp≈0» нет: при thr≤0.055 target огонь + лавина late_fp/fp; при thr≥0.10 снова только FN. **Не использовать как operational thr** — измерение на half-amplitude EPSP.

### E4 — Post-Done parallel re-measure (Train, `IsNeedToTrain=0`)

StatisticLog `SomaNeuronAmplitude` sum: burst peaks **≈0.1137** (совпадает с CalibrateLtz).  
Тот же Train + Test MatrixData (8 samples) → первый sample снова **≈0.114**.

### E5 — PSI tip probe (после amp-eq)

| tip | L | R | `4k/R` (k=2.5) |
|----:|--:|--:|---------------:|
| 0 | 97 | 4.00e6 | 2.50e-6 |
| 1 | 50 | 9.83e7 | 1.02e-7 |
| 2 | 25 | 8.20e7 | 1.22e-7 |
| 3 | 1 | 2.09e9 | 4.77e-9 |

Дистальный tip0 ≫ по проводимости; якорь tip3 после `R×N×(I/I_ref)` почти выключен.

### E7 — Code audit `CalibrateFixedLTZThresholdFromParallelPeak`

- Peak: `max(IterMaxSomaPotential, IterMaxLTZPotential, MaxIterSomaAmp[*])`
- Закрытие CalibrateLtz: полный `settle` (`SettleMarginSec`), **не** early `all_locked`
- Перед фазой: `ScaleTipResistancesForParallelActivation` + `ApplyPulseGeneratorMute` all_on
- Fraction: `peak × CalibrateLTZThresholdFraction` (0.99)

---

## Корневая причина FN

**Неполный sync Train→Test** после PreInh Done:

1. Generator tip-links одно время указывали на baseline сегменты `85/46` при `L=[97,50,25,1]` (починено → `97/50/25/1`).
2. Test `Parameters_00.xml` не содержал полный набор Train-якорей (`MembraneClassName=NPMembraneBioPreinh2_5`, PSI, `AttenuationGamma`, …) — копировались в основном Neuron/TipR/FixedLTZ.
3. После **полного** копирования Train `Model_00.xml` + learner-параметров (с Test Dataset + Analyzer) recognition peak снова **≈0.114**, target **fired**.

На битом Test StatisticLog/analyzer стабильно показывали soma≈0.060 при том же `FixedLTZ` — отсюда ложный вывод «калибровка завышена».

### E6

Fraction-retrain **не выполнялся**: FN закрывается sync’ом, не `CalibrateLTZThresholdFraction`.

---

## Результат после полного sync (2026-08-21)

| | baseline | NextSegInh | PreInh250 (sync fixed) |
|--|:---:|:---:|:---:|
| acc (match) | 6/8 | 7/8 | **7/8** |
| fn | 0 | 0 | **0** |
| fp | 2 | 1 | **1** (trial 6) |
| late_fp | 2 | 4 | **3** (1,2,7) |

Target: `fire=1`, `soma≈0.1137` ≈ FixedLTZ.

---

## Рекомендации

1. **Sync checklist** Train→Test: `Neuron` + `DendriteLength` + `TipSynapseResistance` + `InitialSomaPotential` + `FixedLTZ` + **`AttenuationGamma`** + **`MembraneClassName` / PSI class fields** + **Generator→tip links** на актуальные `L[i]` (+ Inh links если NextSegInh) + Dataset/Analyzer отдельно.
2. Не крутить fraction / FixedLTZ по CSV, пока StatisticLog Done-peak на Test не совпадает с Train (~ratio 1.0).
3. Постоянный learner-fix порога **не требуется** для PreInh FN; дальнейшая работа — снизить late_fp/fp (как у NextSegInh), не поднимать thr.
4. Watch (Часть A): верхний график — Pattern / Dendritic / Soma / `LTZone.Potential` (см. `Interface.xml`).

---

## Артефакты

- Sweep (битый sync): `TimeNeuronTimeLearnerBranchTest_PreInh250/thr_sweep/`
- Этот отчёт; ссылка в [`REPORT_ampeq_nextseginh.md`](REPORT_ampeq_nextseginh.md)
