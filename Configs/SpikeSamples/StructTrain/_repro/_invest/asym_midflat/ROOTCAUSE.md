# AsymRm span50/100 mid-flat — ROOTCAUSE (W5.5 + W6.3)

> **RU:** [`ROOTCAUSE.ru.md`](ROOTCAUSE.ru.md)

## Facts

| Artifact | TipR | Need | L | ltz (8) | soma_amp_sum |
|----------|------|------|---|---------|--------------|
| Gold packA_gen50 | tiprmin | 0 | 25 23 15 1 | ~0.0117 **gap** | 0 |
| Soft r1 TipR86e6 | 86e6×4 | 0 | ≡gold | ≈0.0379 **flat** | 0 |
| **W6.3 overlay tiprmin** on soft weights (no retrain) | tiprmin | 0 | ≡gold | ≈0.0379 **flat** | — |

## Ruled out
1. TipR recipe alone (W3 tiprmin soft + W6 overlay tiprmin on soft weights).
2. Need/L mismatch.
3. Gate metric soma_amp_sum (0 on gold and soft).

## Conclusion
Soft-cold amp/weight state does not reproduce ltz mid hierarchy for span≥50. Span25 TipR86e6 VALIDATED — span-dependent.

## § Wave6 close
packA 50/100 + B/C + LtzCal 50/100 → ARTIFACT_KEEP. C++ TipR/ampDt proposals in QUALITY_BACKLOG_PROPOSALS.md.
