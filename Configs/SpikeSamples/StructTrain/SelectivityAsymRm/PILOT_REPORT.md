# Pilot / scale status (2026-09-08)

## Grid: 16/18 train Done

| EXP | Need | UseFixed | FixedLTZ | L |
|-----|------|----------|----------|---|
| EXP_span25ms_packA_gen | 0 | 1 | ≈0.0869 | `6 5 4 1` |
| EXP_span25ms_packA_preinh | 0 | 1 | ≈0.0516 | `6 5 4 1` |
| EXP_span25ms_packB_gen | 0 | 1 | 0.100 | `6 5 4 1` |
| EXP_span25ms_packB_preinh | 0 | 1 | ≈0.0575 | `6 5 4 1` |
| EXP_span25ms_packC_gen | 0 | 1 | ≈0.0863 | `6 5 4 1` |
| EXP_span25ms_packC_preinh | 0 | 1 | ≈0.0369 | `6 5 4 1` |
| EXP_span50ms_packA_gen | 0 | 1 | 0.100 | `11 9 7 1` |
| EXP_span50ms_packA_preinh | 0 | 1 | ≈0.0681 | `11 9 6 1` |
| EXP_span50ms_packB_gen | 0 | 1 | ≈0.0899 | `11 9 7 1` |
| EXP_span50ms_packB_preinh | 0 | 1 | ≈0.0570 | `11 9 6 1` |
| EXP_span50ms_packC_gen | **1** | **0** | **0.0115 cold** | `11 9 7 1` |
| EXP_span50ms_packC_preinh | 0 | 1 | ≈0.0346 | `11 9 6 1` |
| EXP_span100ms_packA_gen | 0 | 1 | 0.100 | `21 17 11 1` |
| EXP_span100ms_packA_preinh | 0 | 1 | ≈0.0537 | `21 17 11 1` |
| EXP_span100ms_packB_gen | 0 | 1 | 0.100 | `20 17 10 1` |
| EXP_span100ms_packB_preinh | 0 | 1 | ≈0.0767 | `20 17 10 1` |
| EXP_span100ms_packC_gen | **1** | **0** | **0.0115 cold** | `20 17 10 1` |
| EXP_span100ms_packC_preinh | 0 | 1 | 0.100 | `20 17 10 1` |

Done gate (unchanged): `verify_train_done.py --require-calibrated --require-sync-ok`.

**Test selectivity (2026-09-08):** first systematic 8-trial gate on 16 Done — see [`SELECTIVITY_REPORT.md`](SELECTIVITY_REPORT.md). **Gate PASS 1/16** (`EXP_span25ms_packA_gen` 6/8 selective); majority fire_all; one silent. Fingerprint unchanged.

**Anti-regression:** preinh amp postflight `done_fingerprint.py --diff` → **OK, 16 Done unchanged**. Pack C preinh sources still Need=0 (read-only).

## Preinh TipR lever (2026-09-08) — FAILED (no Done regression)

`scripts/finish_packC_gen_preinh_amp.sh` finished `2026-09-08T12:20:37+03:00`, `fail=1`.

Pipeline: fingerprint → backup grid reports → TipR+Initial(d0–2) from Pack C **preinh** → `AMP 80 160 320` + hard-OSC abort → renudge `80 160` → fingerprint OK → restore/regen full-grid peak/stall.

| EXP | Amp path | Post-stall (non-ref) |
|-----|----------|----------------------|
| span50 packC gen | ABORT hard OSC @T=80 (×2 renudge) | d0 amp_ok; d1 OSC `no_improve≈44`; d2 PENDING TipR=**Rmax**, `amp_dt≈-35` (pathological) |
| span100 packC gen | 80→160; ABORT @T=240 renudge | d0 PENDING TipR≈2.2e6; d1 OSC `no_improve≈99`; d2 amp_ok |

Sync non-ref still OK; FixedLTZ never left cold. Initial≈0.042 from preinh applied. TipR drifted off preinh seed during amp (span50 d2 → Rmax).

## Prior: Fast Pack B TipR amp (2026-09-07) — FAILED

`finish_packC_gen_fast_amp.sh`: TipR←Pack B + `160 320 640` + renudge — also fail=1. See log `finish_packC_gen_fast_amp.log`.

## Tooling

- `scripts/done_fingerprint.py` — Done EXP hash pre/post
- `scripts/seed_from_done_preinh.py` — TipR+Initial from preinh, `--surgical`
- `scripts/seed_tipr_from_done_sibling.py` — TipR Pack B→C (superseded for this lever)
- `scripts/finish_packC_gen_preinh_amp.sh` / `finish_packC_gen_fast_amp.sh` / `finish_packC_gen_tip_reset_amp.sh`
- `scripts/reset_pathological_tip.py` — H1 TipR reset (failed under amp)
- `run_asymrm.sh`: `AMP_ABORT_HARD_OSC` (default 0)

## Next (deferred)

H1 tip-reset amp **FAILED** (TipR→Rmax again). See [`PACKC_GEN_DIAGNOSIS.md`](PACKC_GEN_DIAGNOSIS.md) / [`NEXT_LEVER_PACKC.md`](NEXT_LEVER_PACKC.md). Do **not** touch the 16 Done EXP.

```bash
python3 scripts/done_fingerprint.py --diff done_fingerprint_pre_tip_reset_amp.json
python3 ../SelectivityLtzCalibrate/scripts/verify_train_done.py \
  --require-calibrated --require-sync-ok --L-reference l_reference.json \
  EXP_*/Train/Parameters_00.xml
```
