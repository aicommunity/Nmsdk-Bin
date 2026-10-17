# PHASE9 P4 — foil trial6 note

Source PASS: `EXP_480_gen_tiprmin` (7/8, FP trial6, fires=`10000010`).

Silent thr≈0.05 (`results_silent_thr05.csv`):

| trial | ltz_potential_max | soma_amp_sum |
|------:|------------------:|-------------:|
| 0 (target) | 0.0173325 | 0.0693301 |
| 6 (foil) | **0.0182371** | **0.0729485** |

**foil6 > target** — amp inversion. Gate thr≈0.016894 fires trial0+trial6.

Mid-thr alone cannot reach 8/8 without foil-matrix change. Pack B/C @480 **deferred** (no Matrix packs). Parent PASS retained; this clone is diagnostic only.

## PHASE11 R1

Gate via `phase9_preinh_bc_gate.py --silent-thr 0.05 --metric ltz_potential_max`: CSV complete n=8, thr≈0.0168941, fires=`10000010`, acc=7/8 selective, last-pulse ok. Confirms foil6 unreachable; audit gap closed (no missing CSV).
