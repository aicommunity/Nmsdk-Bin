# Cold Train reproducibility harness

Identical cold Train: clone gold PASS → strip Model to tip-1 → TipR `8.6e7×4` / L=`1 1 1 1` → Train → TipR@Rmin + mid gate → compare vs gold and r1↔r2.

## Gold (do not overwrite)

| Family | Gold | `-t` | Mid |
|--------|------|------|-----|
| FastSpan | `SelectivityFastSpan/EXP_span25ms_fast_C1e9` | 160 | `ltz_potential_max` |
| Branch | `SelectivityBranch/EXP_br_span25_packA_gen_C1e9` | 320 | `soma_amp_sum` |

## CLI

```bash
ROOT=Bin/Configs/SpikeSamples/StructTrain
python3 "$ROOT/scripts/repro_cold_harness.py" prepare --all
python3 "$ROOT/scripts/repro_cold_harness.py" run --all
python3 "$ROOT/scripts/repro_cold_harness.py" compare
```

Disk: Avail ≥80G before each Train; pack StatisticLog ≥200M after. One NM at a time.

Result: [`REPRO_COLD_RESULT.md`](REPRO_COLD_RESULT.md).
