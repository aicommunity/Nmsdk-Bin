# Cold Train reproducibility harness

Canonical cold = **soft-cold** (links→tip-1, fat Model kept). Optional `--cold strip` for A/B.

Stop Train on **`IsNeedToTrain=0`**. Post: TipR@Rmin (+ tip Exc); Branch uses full `phase8_tiprmin_gate` prepare.

## Gold (do not overwrite)

| Family | Gold | `-t` | Mid |
|--------|------|------|-----|
| FastSpan | `SelectivityFastSpan/EXP_span25ms_fast_C1e9` | 160 | `ltz_potential_max` |
| Branch | `SelectivityBranch/EXP_br_span25_packA_gen_C1e9` | 320 | `soma_amp_sum` |

## CLI

```bash
ROOT=Bin/Configs/SpikeSamples/StructTrain
python3 "$ROOT/scripts/repro_cold_harness.py" prepare --all --cold soft
python3 "$ROOT/scripts/repro_cold_harness.py" run --all --cold soft
python3 "$ROOT/scripts/repro_cold_harness.py" compare
# A/B invest
python3 "$ROOT/scripts/repro_cold_harness.py" invest --job A1
```

Disk: Avail ≥80G before Train; pack ≥200M after. One NM.

- Result: [`REPRO_COLD_RESULT.md`](REPRO_COLD_RESULT.md)
- Investigation: [`REPRO_COLD_INVESTIGATION.md`](REPRO_COLD_INVESTIGATION.md)
