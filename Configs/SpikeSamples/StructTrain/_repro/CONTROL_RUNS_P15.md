# Control runs after R01–R07 fixes (PLAN P1.5)

Protocol for Branch25 gold / soft_cold and Asym50 isolation. Use **one** Console build
and `posttune_verify.prepare_clean_case` (default). Do not mutate EXP_* archives.

## Prerequisites

1. Rebuild Linux `NeuroModelerConsole` against PulseLib with R01–R07.
2. Write `build_manifest.json` next to the binary (or under `_repro/`):

```json
{
  "console_sha256": "...",
  "root_git": "...",
  "gitlinks": {"PulseLib": "...", "Bin": "...", "Rdk": "..."},
  "compiler": "g++ ...",
  "utc": "..."
}
```

## Commands

```bash
# 1) Branch25 gold weights — skip soft_cold; overlay gold Train TipR/L then calibrate
#    (implement via --skip-train after copying gold weights into clean workdir)
python3 -B Bin/Configs/SpikeSamples/StructTrain/scripts/posttune_verify.py \
  --case br25_on --skip-train

# Prefer full cold soft_cold path:
python3 -B Bin/Configs/SpikeSamples/StructTrain/scripts/posttune_verify.py \
  --case br25_on

# 2) Asym50: archive flag must not leak (clean workdir default)
python3 -B Bin/Configs/SpikeSamples/StructTrain/scripts/posttune_verify.py \
  --case asym50
```

## Per-run artifacts

Save under `_repro/runs/<case>_<utc>/`:

- `provenance.json`, `inputs_manifest.json`
- Train/Test `posttune_complete.flag`, TipR, L, residuals
- `PostTuneResult`, SampleState (metrics finite flags in flag when available)
- target + foil metrics, threshold, EventsLog (before prune)
- `child_rc`, train_status

## Pass criteria

| Case | Expect |
|------|--------|
| Branch25 gold | fires=`10000000`, cpp mid, Result Success or explicit NonSeparable |
| Branch25 soft_cold | same gate protocol; compare only declared inputs vs gold |
| Asym50 + stale archive flag | workdir has no Test flag; mid not `.0116458` from archive |
| Asym50 cold | full provenance even on model FAIL |

Do **not** weaken `LandscapeOk`. Negative landscape → `NonSeparable`, not PASS.

## Actual T2 bundles (2026-09-24)

| Case | Bundle |
|------|--------|
| br25 gold skip | `_repro/runs/br25_on_20260924T165949Z` (+ `_work`) |
| br25 soft_cold | `_repro/runs/br25_on_20260924T170503Z` (+ `_work`) |
| asym50 cold | `_repro/runs/asym50_20260924T171141Z` (+ `_work`) |

Batch: `_repro/runs/T2_control_batch.sh`. After H2, cold path may set `params_source=flag_flush` when Need stayed 1 with a current Train flag.

## Interpretation

Inherited gold PASS + soft_cold FAIL does **not** localize to morphogenesis alone
until R02/R03/R06 are excluded by these bundles. Developer 2/7 cold report is not
independent acceptance.
