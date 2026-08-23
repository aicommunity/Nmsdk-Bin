# Regression verification

## EXP_baseline_gen (EXP00_baseline_margprops) — **FAIL**
- Train L: `49 41 25 1` | FixedLTZ: `0.01281123537910517` | Calibrated: `None`
- Test acc: 1/8 fires `11111111` target_hit=1
- FAIL: acc=1/8 expected 5/8
- FAIL: fires=11111111 expected 10100101

## EXP_baseline_preinh25 (EXP04_preinh_250_margprops) — **FAIL**
- Train L: `100 85 53 1` | FixedLTZ: `0.0115` | Calibrated: `None`
- Test acc: 1/8 fires `11111111` target_hit=1
- FAIL: train not Done (TrainingPhase=None, IsNeedToTrain='1')
- FAIL: L='100 85 53 1' vs golden '49 41 25 1'
- FAIL: AutoCalibrate=1 but FixedLTZ still cold default 0.0115
- FAIL: FixedLTZ=0.0115 vs golden 0.0301736 (>20%)
- FAIL: acc=1/8 expected 6/8
- FAIL: fires=11111111 expected 10001000
