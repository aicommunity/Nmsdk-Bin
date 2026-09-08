# Next lever: Pack C gen via preinh TipR/Initial (2026-09-08)

## Outcome: EXECUTED — FAIL (no Done regression)

`finish_packC_gen_preinh_amp.sh` completed `2026-09-08T12:20:37+03:00`.

- TipR+Initial(d0–2) from Pack C preinh applied; amp `80 160 320` + renudge `80 160`.
- Both gen still Need=1 / FixedLTZ cold.
- `done_fingerprint.py --diff`: **16 Done unchanged**; preinh sources still Need=0.

### Post-stall

- span50: d1 OSC; d2 TipR=Rmax, `amp_dt≈-35` (pathological)
- span100: d1 OSC `no_improve≈99`; d0 PENDING

## Do not re-run this lever without new evidence

Next work: EnableDebug PulseSynced audit only on the two gen (see `SCALE_DEFERRED.md`).
