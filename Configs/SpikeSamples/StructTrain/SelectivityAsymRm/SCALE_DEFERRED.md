# Scale deferred / notes (2026-09-08)

## Status

**16/18** AsymRm EXP train Done. Remaining:

- `EXP_span50ms_packC_gen`
- `EXP_span100ms_packC_gen`

Both: L at `l_reference`, sync_ok, FixedLTZ **cold 0.0115**, Need=1.  
**Done fingerprint unchanged** after tip-reset amp (`done_fingerprint_pre/post_tip_reset_amp.json`).

## Attempts that failed (do not repeat blindly)

| Attempt | Result |
|---------|--------|
| Blind amp `640 1280 2560` + refresh | ~22 h; hard OSC; no FixedLTZ |
| TipR←**Pack B gen** + `160 320 640` + renudge | fail=1; TipR drifts |
| TipR+Initial←**Pack C preinh** + `80 160 320` + renudge + fingerprint | fail=1; **16 Done OK**; span50 d2 → Rmax + pathological `amp_dt` |
| Pathological TipR reset (H1) + `80 160` + hard-OSC | fail=1; TipR re-hit Rmax; `amp_dt≈-5.9e4`; see `PACKC_GEN_DIAGNOSIS.md` |

Manual FixedLTZ/UseFixed=1 — forbidden (fakes calibrated Done).

## Safety tooling (keep)

- Whitelist PILOT only `EXP_span{50,100}ms_packC_gen`
- `done_fingerprint.py` pre/post
- Backup/restore grid `PEAK_SYNC_*` / `stall_latest*` / `grid_summary.csv`
- Never cold-reset without explicit EXP list
- Never write Pack C preinh XML

## Span membrane params (see PARAM_SPAN_COMPARE.md)

D=`0.001`, C/Rm pack-fixed — **same for 25/50/100**. Only ISI + Peak/SyncTol scale with span. Hypothesis for fire_all on Done 50/100: EPSP tuned for ~25 ms.

## Pilots completed (copies only)

| Pilot | Result |
|-------|--------|
| AmpDtAudit on `*_ampaudit` | span50: ≥66 `AmpDtAudit` (amp≈5.9e4 → TipR Rmax); span100: 0 events / NM hang after Done. Fix: skip TipR update if `|dt|>5`. |
| D∝span `*_Dspan` | span100 D=0.004 → Done but **fire_all** 1/8; span50 D=0.002 → Need=1 pathological amp (abort). |

Do **not** re-run TipR transplant / tip-reset amp; do **not** cold-reset originals. Next: peak-window invalidation / empty-window PeakSeen; not another Dissoc-only scale.

```bash
python3 scripts/done_fingerprint.py --diff done_fingerprint_pre_dspan.json
python3 scripts/analyze_train_stall.py --json \
  EXP_span50ms_packC_gen/Train EXP_span100ms_packC_gen/Train
```

Global NeuroModelerConsole budget: **≤6**.

## Waves

| Phase | Status |
|-------|--------|
| Pack A/B/C span25–100 except C gen 50/100 | **Done** (fingerprint protected); test gate 1/16 PASS |
| Pack C gen 50/100 | **blocked**; AmpDtAudit on copies + TipR `|dt|>5` guard shipped |
| Dspan packA gen 50/100 | span100 Done/fire_all; span50 stuck amp — D∝span alone insufficient |