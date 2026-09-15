# REPRO_COLD_RESULT

Generated: 2026-09-15T19:26:32Z

Identical cold Train harness (clean tip-1 Model, TipR cold→@Rmin, mid gate).

| family | role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse |
|--------|------|---|------|-----|-------|-----|------|----------|------------|
| fastspan | gold | `6 5 4 1` | `20000000 20000000 20000000 86000000` | 0.0328372 | `10000000` | 8 | selective | 1 | 1 |
| fastspan | r1 | `7 5 4 1` | `20000000 20000000 20000000 86000000` | 0.1034165 | `11110101` | 3 | partial_FA | 0 | 1 |
| fastspan | r2 | `7 5 4 1` | `20000000 20000000 20000000 86000000` | 0.1034165 | `11110101` | 3 | partial_FA | 0 | 1 |
| branch | gold | `13 11 7 1` | `20000000 20000000 20000000 86000000` | 0.07179975 | `10000000` | 8 | selective | 1 | 1 |
| branch | r1 | `13 11 7 1` | `20000000 20000000 20000000 86000000` | 0.120739 | `10010000` | 7 | selective | 1 | 1 |
| branch | r2 | `13 11 7 1` | `20000000 20000000 20000000 86000000` | 0.120739 | `10010000` | 7 | selective | 1 | 1 |

## Verdicts

- **fastspan**: `REPRO_FAIL`
- **branch**: `REPRO_FAIL`

## Notes

- **r1 ≡ r2** on both families (same `L`, `fires`, `thr`) → not `NONDET`; cold Train is deterministic under this harness.
- FastSpan: L drifted (`7 5 4 1` vs gold `6 5 4 1`); mid `ltz_potential_max` nearly flat → thr≈0.103 vs gold≈0.033; `ok_audit=0`.
- Branch: L matches gold `13 11 7 1`; selective `ok_audit=1` acc=7 but fires `10010000` ≠ gold `10000000` (one FA) → still `REPRO_FAIL` by fires criterion; thr≈0.121 vs gold≈0.072.
- Follow-up (out of scope): seed / BuildStructure diagnostics — not mass retrain.

## Criteria

- `REPRO_OK` — both reps: ok_audit=1, fires==gold, L==gold, last_pulse_ok
- `REPRO_SOFT` — both PASS-like (acc≥7) but L/thr drift
- `REPRO_FAIL` — ok_audit=0 or fires≠gold
- `NONDET` — r1 vs r2 disagree on fires or L

