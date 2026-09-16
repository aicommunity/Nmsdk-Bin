# Cold Train investigation (soft vs strip)

## Goal

Stable from-scratch cold → TipR@Rmin + mid with `ok_audit=1`, `acc≥8`, r1≡r2.
Exact gold match optional.

## A/B results (2026-09-16)

See [`COMPARE.md`](COMPARE.md).

| ID | cold | Need | L | acc | fires | vs gold |
|----|------|------|---|-----|-------|---------|
| A1 | soft | 1 | 7 5 4 1 | 3 | 11110101 | FAIL |
| A2 | strip | 1 | 7 5 4 1 | 3 | 11110101 | FAIL (≡ A1) |
| B1 | soft | 0 | 13 11 7 1 | 8 | 10000000 | **EXACT** |
| B2 | strip | 0 | 13 11 7 1 | 8 | 10000000 | **EXACT** |

## Root cause (C3)

### Branch — resolved

Prior `_repro` FAIL was **protocol**, not cold mode:

1. Missing **`ResetToUntrainedState`** on gold Done XML (injected when absent).
2. Early SIGTERM before **`Need=0`** (poll L≠cold, not Done).
3. Gate **`--skip-prepare`** → no `patch_tip_exc_r` on Test Model.

With soft-cold + Need=0 wait + full phase8 prepare: **B1≡B2≡gold** (InitSoma, thr, fires).

Strip Model is **not required** for Branch25; soft-cold is canonical.

### FastSpan — open (phase 2)

A1≡A2: strip vs soft **does not explain** FS gap.

- Train grows L in trace (`6 5 4 1`+) but **`Parameters` often stale L=1 1 1 1** until late save.
- NM exits at `-t 160` with **`Need=1`** (no delayed `Need=0` within 180s wait) → gate on incomplete Done.
- Gate thr≈0.103 vs gold≈0.033 → `partial_FA` acc=3.
- L settles **7 5 4 1** vs gold **6 5 4 1** (L-policy edge on dend0; PulseLib `6f12f04` already in gold binary).

**Not** PulseLib regression after gold (pin `780ffc7` unchanged).

Follow-up: FS delayed-save poll; optional `-t` extension; debug `peak_synced` on dend0 at L=6 vs 7.

## Canon

- **Branch25:** soft-cold + Need=0 + full phase8 gate.
- **FastSpan25:** same protocol; FS quality still failing until Need=0 / L/thr fixed.

## Checkpoints

C0–C2.* done in Bin. C3=this file. C4 after soft canon re-run.
