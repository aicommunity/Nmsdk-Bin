# Scale deferred / notes (2026-09-08)

## Status

**16/18** AsymRm EXP train Done. Remaining:

- `EXP_span50ms_packC_gen`
- `EXP_span100ms_packC_gen`

Both: L at `l_reference`, sync_ok, FixedLTZ **cold 0.0115**, Need=1.  
**Done fingerprint unchanged** after preinh lever (`done_fingerprint_pre/post_preinh_amp.json`).

## Attempts that failed (do not repeat blindly)

| Attempt | Result |
|---------|--------|
| Blind amp `640 1280 2560` + refresh | ~22 h; hard OSC; no FixedLTZ |
| TipR←**Pack B gen** + `160 320 640` + renudge | fail=1; TipR drifts |
| TipR+Initial←**Pack C preinh** + `80 160 320` + renudge + fingerprint | fail=1; **16 Done OK**; span50 d2 → Rmax + pathological `amp_dt`; span100 d1 hard OSC |

Manual FixedLTZ/UseFixed=1 — forbidden (fakes calibrated Done).

## Safety tooling (keep)

- Whitelist PILOT only `EXP_span{50,100}ms_packC_gen`
- `done_fingerprint.py` pre/post
- Backup/restore grid `PEAK_SYNC_*` / `stall_latest*` / `grid_summary.csv`
- Never cold-reset without explicit EXP list
- Never write Pack C preinh XML

## Next (deferred — needs new diagnosis)

Not another TipR copy amp. Prefer:

1. EnableDebug NM on the two gen: `PulseSynced` / `ActivePulseIndex` / why EndOfLearning never fires with Initial=0.042.
2. Investigate span50 d2 `amp_dt≈-35` + TipR at Rmax (measurement/peak anomaly vs real amp).
3. Only then design a targeted fix (possibly C++ or pattern/Initial interaction for gen vs preinh).

## Waves

| Phase | Status |
|-------|--------|
| Pack A/B/C span25–100 except C gen 50/100 | **Done** (fingerprint protected) |
| Pack C gen 50/100 | **blocked** after preinh lever |

```bash
python3 scripts/done_fingerprint.py --diff done_fingerprint_pre_preinh_amp.json
python3 scripts/analyze_train_stall.py --json \
  EXP_span50ms_packC_gen/Train EXP_span100ms_packC_gen/Train
```

Global NeuroModelerConsole budget: **≤6**.
