# Cold Train reproducibility harness

Canonical cold = **soft-cold** (links→tip-1, fat Model kept). Optional `--cold strip` for A/B.

Stop Train on **`IsNeedToTrain=0`**. Post: TipR@Rmin (+ tip Exc); Branch uses full `phase8_tiprmin_gate` prepare.

**PHASE12 multi-EXP:** [`scripts/phase12_validate.py`](../scripts/phase12_validate.py) — Wave1 packA cold; Wave2 `list-wave2` / `run-clones-wave2` / `run-br480-all`; Wave3 `list-wave3` / `run-fs` / `run-asym-packa-all` / `run-asym-clones` / `sync-ltzcal-all`; Wave4 `run-phase6-all`; Wave5 `list-tails` + [`scripts/phase12_wave5_run.sh`](../scripts/phase12_wave5_run.sh) (`--phase6-only|--ltzcal-only|--fs-only|--asym-only|--branch-fail-only`). Manifest: [`PHASE12_VALIDATION.md`](../PHASE12_VALIDATION.md). Legacy harness stays for FS/Branch25 invest A/B.

## Gold (do not overwrite)

| Family | Gold | `-t` | Mid |
|--------|------|------|-----|
| FastSpan | `SelectivityFastSpan/EXP_span25ms_fast_C1e9` | 160 | `ltz_potential_max` |
| Branch | `SelectivityBranch/EXP_br_span25_packA_gen_C1e9` | 320 | `soma_amp_sum` |

## CLI

```bash
ROOT=Bin/Configs/SpikeSamples/StructTrain
# PHASE12 Wave1 (preferred for packA roots)
python3 "$ROOT/scripts/phase12_validate.py" list
python3 "$ROOT/scripts/phase12_validate.py" stamp-from-repro --exp EXP_br_span25_packA_gen_C1e9
python3 "$ROOT/scripts/phase12_validate.py" run-all-wave1 --exp EXP_br_span50_packA_gen_C1e9

```bash
# PHASE12 Wave2
python3 "$ROOT/scripts/phase12_validate.py" list-wave2
python3 "$ROOT/scripts/phase12_validate.py" run-clones-wave2
python3 "$ROOT/scripts/phase12_validate.py" run-br480-all --force-prepare

# PHASE12 Wave3+
python3 "$ROOT/scripts/phase12_validate.py" list-wave3
python3 "$ROOT/scripts/phase12_validate.py" run-fs --exp EXP_span25ms_fast_C1e9 --force-prepare
# bash "$ROOT/scripts/phase12_wave3_run.sh"          # full W3
# bash "$ROOT/scripts/phase12_wave3_run.sh" --with-wave4

# PHASE12 Wave5 tails
python3 "$ROOT/scripts/phase12_validate.py" list-tails
# bash "$ROOT/scripts/phase12_wave5_run.sh" --ltzcal-only
```
# Legacy two-family harness
python3 "$ROOT/scripts/repro_cold_harness.py" prepare --all --cold soft
python3 "$ROOT/scripts/repro_cold_harness.py" run --all --cold soft
python3 "$ROOT/scripts/repro_cold_harness.py" compare
python3 "$ROOT/scripts/repro_cold_harness.py" invest --job A1
```

Disk: Avail ≥80G before Train; pack ≥200M after. One NM.

- Result: [`REPRO_COLD_RESULT.md`](REPRO_COLD_RESULT.md)
- Investigation: [`REPRO_COLD_INVESTIGATION.md`](REPRO_COLD_INVESTIGATION.md)
