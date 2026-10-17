# Next lever: Pack C gen pathological TipR reset (2026-09-08)

## Outcome: EXECUTED — FAIL (no Done regression)

`finish_packC_gen_tip_reset_amp.sh` + `reset_pathological_tip.py` (H1 from `PACKC_GEN_DIAGNOSIS.md`).

- Reset span50 d1/d2 and span100 d1 TipR; amp `80 160` + hard-OSC abort.
- Both gen still Need=1 / FixedLTZ cold; TipR re-hit Rmax; span50 d2 `amp_dt≈-5.9e4`.
- `done_fingerprint.py --diff` vs `done_fingerprint_pre_tip_reset_amp.json`: **16 Done unchanged**.

## Do not re-run tip-reset / TipR-copy amp without new C++/peak evidence

See `SCALE_DEFERRED.md`.
