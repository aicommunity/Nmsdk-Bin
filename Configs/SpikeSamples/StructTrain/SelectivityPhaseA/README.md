# SelectivityPhaseA — индекс экспериментов

Фаза A: конфигурационные эксперименты избирательности `NNeuronTimeLearner` без изменения алгоритма обучения.

Итоговый отчёт: **[REPORT.md](REPORT.md)**

Baseline reference: [`TimeNeuronTimeLearner/Test`](../TimeNeuronTimeLearner/Test/) — 4/8.

| EXP | Train | Test | Изменение | Retrain? | Accuracy |
|-----|-------|------|-----------|:--------:|:--------:|
| EXP00_baseline | `Train/` | `Test/` | контроль | нет | **4/8** |
| EXP01_ltz_threshold_sweep | веса EXP00 | `Test/` (+ `Test_thr*`) | `FixedLTZThreshold` | нет | **6/8** (0.0135) |
| EXP02_ltzone_average_mode | веса EXP00 | `Test/` (+ `Test_avg*`) | `UseAverageLTZonePotential` | нет | 4/8 |
| EXP03_sync_tolerance_015 | `Train/` (`-S`) | `Test/` | `SyncTolerance=0.015` | да | **3/8** |
| EXP04_sync_tolerance_010 | `Train/` (`-S`) | `Test/` | `SyncTolerance=0.010` | да | 4/8 |
| EXP05_resistance_gain_025 | `Train/` (`-S`) | `Test/` | `ResistanceAdjustGain=0.25` | да | 4/8 |
| EXP06_ltzone_integration | веса EXP00 | `Test/` (+ `Test_tc*` / `Test_npltzone_*`) | тип компонента LTZone (`NPLTZone`) / τ / порог | нет | **6/8** (= EXP01) |

Лучший конфиг: [`EXP01_ltz_threshold_sweep/Test`](EXP01_ltz_threshold_sweep/Test/) (канон = бывший `Test_thr00135`).

## Команды

```bash
./Bin/Platform/Linux/NeuroModelerConsole -c .../Test/Project.ini -s -t 20 -x
./Bin/Platform/Linux/NeuroModelerConsole -c .../Train/Project.ini -s -t 160 -x -S
scripts/copy_config.sh sync Train/ Test/
```

Скрипты: [scripts/](scripts/)
