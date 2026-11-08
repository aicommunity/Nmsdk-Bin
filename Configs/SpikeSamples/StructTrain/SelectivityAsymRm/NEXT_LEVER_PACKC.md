> Исторический документ кампании AsymRm. Упомянутые pilot/finish/scale/sweep shell запускатели удалены из текущего дерева; их исходники доступны в [снимке Bin 14a88195](https://github.com/aicommunity/Nmsdk-Bin/tree/14a88195a8a5538d3a2f5c0657981488e38829b7/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts). Команды ниже описывают прежний протокол и не являются инструкцией запуска текущего pipeline. Сохранённые измерения не пересчитаны. [Миграция и ограничения](https://github.com/aicommunity/Nmsdk/blob/develop/Docs/StructTrain/TimeLearner/AsymRmLauncherRetirement.ru.md).

# Next lever: Pack C gen pathological TipR reset (2026-09-08)

## Outcome: EXECUTED — FAIL (no Done regression)

`finish_packC_gen_tip_reset_amp.sh` + [`reset_pathological_tip.py`](https://github.com/aicommunity/Nmsdk-Bin/blob/b4f66eb137d3e1c19539890dbdee06faa3e1020b/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/reset_pathological_tip.py) (H1 from `PACKC_GEN_DIAGNOSIS.md`).

- Reset span50 d1/d2 and span100 d1 TipR; amp `80 160` + hard-OSC abort.
- Both gen still Need=1 / FixedLTZ cold; TipR re-hit Rmax; span50 d2 `amp_dt≈-5.9e4`.
- `done_fingerprint.py --diff` vs `done_fingerprint_pre_tip_reset_amp.json`: **16 Done unchanged**.

## Do not re-run tip-reset / TipR-copy amp without new C++/peak evidence

See `SCALE_DEFERRED.md`.


Historical script retrieval (2026-11-08): the four AsymRm seed/reset tools were retired from the current tree. Their original source is preserved in Bin commit `b4f66eb137d3e1c19539890dbdee06faa3e1020b`, under `Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/`. This changes availability of launch tools, not the historical observations or criteria. Full native model import/export replaces partial XML overlays for new work; numerical equivalence is not claimed.
