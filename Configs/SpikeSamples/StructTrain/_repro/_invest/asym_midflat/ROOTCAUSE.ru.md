# AsymRm span50/100 mid-flat — ROOTCAUSE (W5.5 + W6.3) — RU

**EN:** [`ROOTCAUSE.md`](ROOTCAUSE.md)

## Факты

| Артефакт | TipR | Need | L | ltz (8) | soma_amp_sum |
|----------|------|------|---|---------|--------------|
| Gold packA_gen50 | tiprmin | 0 | 25 23 15 1 | ~0.0117 **с зазором** | 0 |
| Soft r1 TipR86e6 | 86e6×4 | 0 | ≡gold | ≈0.0379 **flat** | 0 |
| **W6.3 overlay tiprmin** на soft-веса (без retrain) | tiprmin | 0 | ≡gold | ≈0.0379 **flat** | — |

## Исключено
1. Один только рецепт TipR (W3 tiprmin soft + W6 overlay tiprmin).
2. Расхождение Need/L.
3. Метрика gate `soma_amp_sum` (0 на gold и soft).

## Вывод
Soft-cold не воспроизводит amp-иерархию для `ltz_potential_max` mid при span≥50. Span25 TipR86e6 — VALIDATED (зависимость от span).

## Закрытие Wave6
packA 50/100 + B/C + LtzCal 50/100 → `ARTIFACT_KEEP`. C++ TipR/ampDt — в [`QUALITY_BACKLOG_PROPOSALS.ru.md`](../../../QUALITY_BACKLOG_PROPOSALS.ru.md) §B.
