# Morphogenesis research (PLAN P2) — gated on P1.5 FAIL

Run **only if** control cases still FAIL after R01–R07 measurement fixes.

Start with `br25_on`. One hypothesis per run.

| Hypothesis | Control | Status |
|---|---|---|
| Incomplete soft_cold reset | soft vs strip (`T3_H3_soft_vs_strip.py`) | **H3 done** — no_material_diff |
| Interval → residual activity | AutoScale 0/1 (`T3_H4_autoscale.py`) | **H4 done** — no differs; overlay skipped |
| Canon hurts landscape of new L | same L; Canon vs Keep | **H1 done** — Keep also NonSeparable |
| TipR Save lag / Need | flag_flush | **H2 done** |
| Train→Test overlay error | load final Train vs overlay | skipped (H3/H4 did not localize) |
| Best-effort early stop | termination reason + residuals | — |

Then same protocol: `br25_off`, `br100_keep`, `asym25`, `asym50`, `br100_search`, `phase6_480` (D4 matrix).

- Search: vs **own** snapshot; `applied_best` / `reverted`; Δgap. Fallback ≠ search improvement.
- phase6: regression expect `10000010` vs strict `10000000` — separate verdicts.

Negative gap on the correct metric may be inseparable parameterization (heuristic), not a code bug.
Change learning algorithms only after localization + gold regression.
