> Historical AsymRm XML patch tools retired06.11.2026: cold_patch_dspan.py, warm_start_l.py, patch_test_model.py, inject_analyzer.py and merge_train_weights.py. Exact sources: Bin commit `f12f09ae1f7fc0a9af1d99be86d3a4002a3cf4aa`, `Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/`. Commands in the original text below describe the old campaign only. New work uses root Scripts/StructTrain/TimeLearner native model export/import and explicit storage profiles. Original configurations, measurements and report body are preserved. See root Docs/StructTrain/TimeLearner/AsymRmOverlayRetirement.ru.md; migration metadata acceptance is pending.

> Историческая процедура AsymRm. Оставшиеся10 shell-драйверов удалены из текущего дерева; исходники доступны в Bin commit `34387285116ee96bb09f99cb2ee95881fd3b9e0a`, путь `Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/`. Полный retrieval manifest: корневой `Docs/StructTrain/TimeLearner/script_migration.json`; область и проверки: `AsymRmDriverRetirement.ru.md`. Старые команды ниже описывают прежнюю кампанию. Конфиги, модели, измерения и исходное тело отчёта сохранены; удаление скриптов не выполняет очистку логов и не пересматривает исторические результаты. Новые задания — через корневой `Scripts/StructTrain/TimeLearner`. Оставшиеся Python-анализаторы ещё требуют отдельного review.

> Исторический документ кампании AsymRm. Упомянутые pilot/finish/scale/sweep shell запускатели удалены из текущего дерева; их исходники доступны в [снимке Bin 14a88195](https://github.com/aicommunity/Nmsdk-Bin/tree/14a88195a8a5538d3a2f5c0657981488e38829b7/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts). Команды ниже описывают прежний протокол и не являются инструкцией запуска текущего pipeline. Сохранённые измерения не пересчитаны. [Миграция и ограничения](https://github.com/aicommunity/Nmsdk/blob/develop/Docs/StructTrain/TimeLearner/AsymRmLauncherRetirement.ru.md).

# Span100 dend0 protocol (scale + Done Unblock)

## Problem

`EXP_span100ms_packA_preinh` stalls at `L=[9, 17, 12, 1]` vs formula/`l_reference` target `[20, 17, 10, 1]`.
dend0 `last_abs_dt≈0.061` (~14× SyncTol≈0.00417). Blind `+5120` wastes wall clock.

`EXP_span100ms_packA_gen` at `L=[9, 17, 1, 1]` — dend2 still cold; post-est EstDelay from partial L is misleading (`≈0.0125`); **use L_reference**, not formula-from-L.

## Root cause (tooling)

- `l_reference.json` previously imported LtzCal **Test** Done with `L=[1,1,1,1]` → broken effective target.
- Fix: hardcode formula floors in `scripts/patch_l_reference.py` (`REFERENCE_L` span100 = `[20,17,10,1]`); reject trivial `[1,1,1,*]` from LtzCal fallback.
- Pack B/C seed/L_ref: `pack_a_alias` → same span+kind Pack A.

## Protocol (in-place, no cold reset Pack A)

1. **Do not** cold-reset — keep current L / Initial.
2. Export L_ref: `python3 scripts/patch_l_reference.py --export l_reference.json`
3. Seed `InitialSomaPotential` from LtzCal ([`scripts/seed_initial_from_ltzcal.py`](https://github.com/aicommunity/Nmsdk-Bin/blob/b4f66eb137d3e1c19539890dbdee06faa3e1020b/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/seed_initial_from_ltzcal.py)) before floor/amp.
4. **Primary path:** `L_REFERENCE=ltzcal` → `l_guard_floor` raises to `[20,17,10,1]` → amp (`AMP_TRAIN_STEPS=320 640 1280`). This bypasses hopeless LENGTH_STALL growth on dend0.
5. Length schedule only if still below ref after floor attempt: `LENGTH_STEPS_SPAN100="80 160 320 640 1280 2560"`, `LENGTH_MAX_STEP=2560` — never 5120.
6. If floor+amp leaves residual sync: raise `SyncTolerance` from measured `last_abs_dt` (span50 gen used **0.005**); then `AMP_ONLY=1`.
7. Optional warm-start (partial raise without full jump): `python3 scripts/warm_start_l.py Train/Parameters_00.xml --target "15 17 12 1" --dendrites 0`
8. **Not a gate blocker** for span25/50 Pack A Done or Pack B/C span25/50 waves.

## Commands

```bash
export SKIP_COLD_RESET=1 SEED_INITIAL=1 L_REFERENCE=ltzcal MAX_JOBS=6
bash scripts/run_pilot_span100.sh
# amp-only continue:
PILOT_EXPS="EXP_span100ms_packA_gen EXP_span100ms_packA_preinh" AMP_ONLY=1 \
  L_REFERENCE=ltzcal SEED_INITIAL=1 MAX_JOBS=2 bash scripts/run_asymrm.sh
```

## Success / stop

- Success: `verify_train_done.py --require-calibrated --require-sync-ok` + FixedLTZ ≠ 0.0115; L ≥ `[20,17,10,1]`.
- Stop: guard abort / persistent TIMING_MISMATCH after SyncTol bump — document in `PILOT_SPAN100_REPORT.md`; do not block Pack B/C span25/50.


Historical script retrieval (2026-11-08): the four AsymRm seed/reset tools were retired from the current tree. Their original source is preserved in Bin commit `b4f66eb137d3e1c19539890dbdee06faa3e1020b`, under `Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/`. This changes availability of launch tools, not the historical observations or criteria. Full native model import/export replaces partial XML overlays for new work; numerical equivalence is not claimed.
