# EXP03 — SyncTolerance 0.015

## Гипотеза
Более точная синхронизация длин → меньше случайных совпадений.

## Изменения
| Параметр | Baseline | EXP03 |
|----------|----------|-------|
| SyncTolerance | 0.02 | 0.015 |
| ResetToUntrainedState | 0 | 1 (cold train) |
| IsNeedToTrain | 0 | 1 |

Train: `-s -t 160 -x -S` → sync → Test.

## Результаты
После Save: L=`[49,41,27,1]`. Accuracy **3/8** (хуже baseline: late cluster стал FP).

