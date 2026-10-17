# PHASE10 Mid TipR note — br480 preinh250

Parent `EXP_br480_preinh250_tiprmin` remains **7/8** `ok_audit` registry entry.

Clone: `EXP_br480_preinh250_tiprmin_phase10_tipr`

| Mode | TipR | silent gap | gate |
|------|------|------------|------|
| `done` (PreInh250 Train skew) | `3.996e6 … 2.095e9` | +0.00098 (but foil trials > tgt) | `ok_audit=0` per_stim, fires `10000010` |
| `partial` (Rmin×3 + Done tip3) | `2e7×3 + 2.095e9` | +0.00028 | `ok_audit=0` per_stim, `partial_FA` |

Verdict: TipR Done/partial **не** закрывает FP trial4 / morphology; mid-only insufficient. Keep parent 7/8.
