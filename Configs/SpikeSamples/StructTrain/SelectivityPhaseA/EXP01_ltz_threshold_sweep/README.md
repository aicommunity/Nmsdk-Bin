# EXP01 — Sweep FixedLTZThreshold

## Гипотеза
Поднятие порога LTZ отсечёт FP при сохранении trained response.

## Метод
- Offline sweep по `ltz_potential_max` из EXP00 (`scripts/ltz_sweep_offline.py`)
- Confirm-прогоны: `Test_thr0115`, `Test_thr0120`, …

## Конфиги
Подпапки `Test_thr*/Project.ini` — веса из EXP00 Train, меняется только `FixedLTZThreshold` / `LTZThreshold`.

## Результаты (confirm)
| thr | accuracy |
|-----|:--------:|
| 0.0115 | 4/8 |
| 0.0120 | 4/8 |
| 0.0125 | 4/8 |
| 0.0130 | 5/8 |
| 0.0135 | **6/8** (лучшее в фазе A) |

