# FS25 soft-cold unblock (PHASE12 W3a) — FAIL_ROOTCAUSE

Date: 2026-09-18 · PulseLib pin `780ffc7` · **no PulseLib patch** (needs explicit approve).

## Attempt

```bash
python3 scripts/phase12_validate.py run-fs --exp EXP_span25ms_fast_C1e9 --force-prepare
```

- soft-cold prepare r1 OK (`tips_max=6`, Reset inject, Need=1, TipR cold)
- Train `-t`180 + 2 extends (cap)
- Window1: L stuck `1 1 1 1` Need=1 until `-t` exit
- Windows 2–3: L=`6 5 4 1` (gold L) but **Need stuck at 1** through extend cap
- TipR remained cold `86e6×4` (train never finished → no TipR@Rmin hygiene)

## Verdict

`FAIL_ROOTCAUSE` — soft-cold alone does not reach Need=0 on FS25 under pin `780ffc7`.  
Candidate (deferred, needs approve): L-policy dend0 (6↔7) PulseLib change — see `_repro/REPRO_COLD_INVESTIGATION.md`.

## Follow-on (plan)

- FS×5 cold registry **blocked** until unblock or approve-to-proceed
- AsymRm packA cold **allowed** after this FAIL_ROOTCAUSE closeout
