# PHASE10 Done TipR note — Phase6 foil trial6

Clone of `EXP_480_gen_tiprmin` with TipR from `EXP_480_gen_thr_only`
(`25.8e6 27.2e6 21.9e6 86e6`), silent FixedLTZ=`0.05`, mid on `ltz_potential_max`.

Silent ltz (8 trials):

`[0.0146773, 0.0107782, 0.0133442, 0.0107556, 0.014095, 0.0126778, 0.014735, 0.011231]`

- target = 0.0146773
- **foil trial6 = 0.014735 ≥ target** → mid cannot separate trial6 (hard FAIL for 8/8)
- mid thr = 0.01438615 → gate **7/8** `ok_audit=1` fires `10000010` (same quality as parent tiprmin / thr_only)

Parent `EXP_480_gen_tiprmin` **7/8** retained. No pack B/C @480.
