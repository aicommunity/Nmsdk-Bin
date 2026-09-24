# Morphogenesis research (PLAN P2) — gated on P1.5 FAIL

Run **only if** control cases still FAIL after R01–R07 measurement fixes.

Start with `br25_on`. One hypothesis per run.

| Hypothesis | Control | Distinguishes |
|---|---|---|
| Incomplete soft_cold reset | soft_cold vs full init, same params | L/R, anchors, potentials, FixedLTZ |
| Interval → residual activity | AutoScale 0/1, logged gap/delay | same weights, different timing |
| Canon hurts landscape of new L | same L; Canon vs Keep | target/max(foils), global gap |
| Train→Test overlay error | load final Train vs overlay | XML before/after each step |
| Best-effort early stop | termination reason + residuals | sync/amp, not only Need=0 |

Then same protocol: `br25_off`, `br100_keep`, `asym25`, `asym50`, `br100_search`, `phase6_480`.

- Search: vs **own** snapshot; `applied_best` / `reverted`; Δgap. Fallback ≠ search improvement.
- phase6: regression expect `10000010` vs strict `10000000` — separate verdicts.

Negative gap on the correct metric may be inseparable parameterization (heuristic), not a code bug.
Change learning algorithms only after localization + gold regression.
