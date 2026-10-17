# SelectivityFastResponse — DissociationTC × Capacity

Сетка ускорения EPSP/мембраны для `NNeuronTimeLearner` (этап 1: только C и DissociationTC, без Rm/Rsyn).

## Ячейки

| | C=1e-9 | C=5e-10 | C=2.5e-10 |
|--|:---:|:---:|:---:|
| **D=0.005** | `EXP00CtrlExp04` → `NSPNeuronGen` | `EXPD005C5e10` | `EXPD005C25e11` |
| **D=0.002** | `EXPD002C1e9` | `EXPD002C5e10` | `EXPD002C25e11` |
| **D=0.001** | `EXPD001C1e9` | `EXPD001C5e10` | `EXPD001C25e11` |

Фон как EXP04: `SyncTolerance=0.01`, `ResistanceAdjustGain=0.4`, `Delay=1.5`, `FixedLTZThreshold=0.0115`, `TrainingLTZThreshold=100`, `UseAverageLTZonePotential=1`.

## Команды

```bash
./scripts/setup_grid.sh   # cold Parameters+Model (NeuronClassName в Model обязателен)
./scripts/run_grid.sh     # Train 160 + sync + Test 20 → grid_summary.csv
TRAIN_T=240 ./scripts/run_grid.sh
```

## Gate

`train_ok=1` только если trial0 (`target_class=1`) дал `neuron_fired=1`.

Итоги: [REPORT.md](REPORT.md), сводка: `grid_summary.csv`.
