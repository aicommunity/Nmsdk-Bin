# PSI Anchor Recheck (test-only)

Date: 2026-08-16T20:30:40+03:00

Протокол: NeuroModelerConsole Test `-t 20 -x` (без cold retrain).

| Конфиг | expect Acc | Acc | fires | mode | target_hit | fire_all | OK |
|--|--:|--:|--|--|--:|--:|--|
| EXP00_baseline_autothr | 4/8 | 4/8 | `10101110` | partial_FA | 1 | 0 | **OK** |
| EXP00_baseline | 4/8 | 4/8 | `10101110` | partial_FA | 1 | 0 | **OK** |
| EXP04_preinh_250 | 6/8 | 6/8 | `10001010` | selective | 1 | 0 | **OK** |
| EXP00_baseline_margprops | 5/8 | 5/8 | `10101010` | partial_FA | 1 | 0 | **OK** |
| EXP04_preinh_250_margprops | 6/8 | 6/8 | `10001010` | selective | 1 | 0 | **OK** |
| EXP21_span100ms_preinh250 | 5/8 | 5/8 | `11110000` | partial_FA | 1 | 0 | **OK** |

**Итог: все якоря OK.**
