# Mid rootcause: C++ PostTune vs Python phase8/phase9

## Итог

| Кейс | TipR | Silent mid | Gate | fires |
|------|------|------------|------|-------|
| Branch25 CanonRmin | Train PostTune `2e7×3+8.6e7` | Test inference soma≈`0.07180` | `phase8 --skip-tipr-mid` | `10000000` |
| Branch25 off | CalibrateLtz ScaleTipR | FixedLTZ≈`0.0163` | force-python-hygiene | `10000000` |
| AsymRm25 FlatLastR | `8.6e7×4` | Test inference LTZ≈`0.037589` (=gold) | `phase9 --skip-tipr-mid` | `10000000` |

## Почему mid нельзя в Train-процессе (Branch)

In-learner free-run после Sync/Normalize даёт soma≈**0.066** и инверсии foils.  
Тот же TipR/L на **свежем Test** (Matrix pack A, без `Neuron->Reset` перед зондами) →≈**0.07186**.

## Архитектура mid (полный C++, Branch + TL)

1. **Train PostTune:** TipR (+ Exc); если Train free-run landscape плохой → `FixedLTZ=1.0` (silent), `Need=0`.
2. **Test ABuild:** при `FixedLTZ≥0.9` держит `Dataset.StateGeneration=0`.
3. **Test ACalculate:** `MaybeStartInferenceMidProbes` — играет **текущую Matrix** (pack A), пишет mid в FixedLTZ + `posttune_complete.flag`.
4. **Gate `--skip-tipr-mid`:** если thr silent → pass1 до flag, flush mid в XML, pass2 gate.

Analyzer на время mid выключается (`Enable=false`), CSV mid-проб не попадает в gate.

Метрика: Branch — soma; TL Auto — LTZ (`PostTrainMidMetric`).
