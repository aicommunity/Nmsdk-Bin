# PHASE9 P4 — br480 preinh250 mid retry
Clone of `EXP_br480_preinh250_tiprmin` (parent 7/8, FP trial4).
Silent thr=1.0 soma: [0.112161, 0.0957808, 0.105838, 0.0839142, 0.116478, 0.110111, 0.102592, 0.092139]
target=0.112161 max_foil=0.116478 → gap=-0.004317 (**negative**: trial4 foil > target).
Gate after naive mid: ok_audit=0 acc=6 fires=00001000 mode=miss_target.

Conclusion: mid-only cannot close FP without TipR/Done fallback or foil change. **Document FAIL**; keep parent 7/8 in SUCCESSFUL. No cold-reset PreInh250 template.
