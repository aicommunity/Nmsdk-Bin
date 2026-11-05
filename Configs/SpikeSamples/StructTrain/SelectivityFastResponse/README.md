# SelectivityFastResponse — DissociationTC × Capacity

Сетка ускорения EPSP/мембраны для `NNeuronTimeLearner` (этап 1: только C и DissociationTC, без Rm/Rsyn).

## Ячейки

| | C=1e-9 | C=5e-10 | C=2.5e-10 |
|--|:---:|:---:|:---:|
| **D=0.005** | `EXP00CtrlExp04` → `NSPNeuronGen` | `EXPD005C5e10` | `EXPD005C25e11` |
| **D=0.002** | `EXPD002C1e9` | `EXPD002C5e10` | `EXPD002C25e11` |
| **D=0.001** | `EXPD001C1e9` | `EXPD001C5e10` | `EXPD001C25e11` |

Фон как EXP04: `SyncTolerance=0.01`, `ResistanceAdjustGain=0.4`, `Delay=1.5`, `FixedLTZThreshold=0.0115`, `TrainingLTZThreshold=100`, `UseAverageLTZonePotential=1`.

## Текущий статус

Исторические запускатели удалены. Для каждого из шести файлов точная версия доступна через `git -C Bin show 500764df8ae41604e03bdecdfd5531c7bc16f49b:Configs/SpikeSamples/StructTrain/SelectivityFastResponse/scripts/<имя>` из корня SDK; полный реестр с blob/SHA256 — `Docs/StructTrain/TimeLearner/script_migration.json`. Копии и wrappers на старом месте отсутствуют.

Прежний `train_ok` проверял первую строку Test; это не свидетельство сходимости Train. Историческая сводка сохраняется со своим критерием. Новые оценки требуют ID/меток, полного окна и отдельного training outcome. Новые запуски — через корневой пакет `Scripts/StructTrain/TimeLearner`, после соответствующих проверок режима/physics/storage.

Итоги исходного протокола: [REPORT.md](REPORT.md), сохранённая сводка: `grid_summary.csv`.
