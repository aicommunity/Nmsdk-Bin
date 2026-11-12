# EXP00 — Baseline (репродукция 4/8)

## Гипотеза
Контрольный прогон с расширенными метриками analyzer (`ltz_potential_max`, soma amps).

## Изменённые параметры
| Параметр | Baseline | EXP00 |
|----------|----------|-------|
| — | — | без изменений |

## Конфиги
| Роль | Путь |
|------|------|
| Train | `SelectivityPhaseA/EXP00_baseline/Train/Project.ini` |
| Test | `SelectivityPhaseA/EXP00_baseline/Test/Project.ini` |

## Результаты
- CSV: `Test/SelectivityLog/results.csv`
- Accuracy: **4/8**
- `ltz` gap trained−max(FP) = 6e-6 (не separable)
