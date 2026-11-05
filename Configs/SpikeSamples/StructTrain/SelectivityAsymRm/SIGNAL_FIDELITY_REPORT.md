> Историческая процедура AsymRm. Оставшиеся10 shell-драйверов удалены из текущего дерева; исходники доступны в Bin commit `34387285116ee96bb09f99cb2ee95881fd3b9e0a`, путь `Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/`. Полный retrieval manifest: корневой `Docs/StructTrain/TimeLearner/script_migration.json`; область и проверки: `AsymRmDriverRetirement.ru.md`. Старые команды ниже описывают прежнюю кампанию. Конфиги, модели, измерения и исходное тело отчёта сохранены; удаление скриптов не выполняет очистку логов и не пересматривает исторические результаты. Новые задания — через корневой `Scripts/StructTrain/TimeLearner`. Оставшиеся Python-анализаторы ещё требуют отдельного review.

> Исторический документ кампании AsymRm. Упомянутые pilot/finish/scale/sweep shell запускатели удалены из текущего дерева; их исходники доступны в [снимке Bin 14a88195](https://github.com/aicommunity/Nmsdk-Bin/tree/14a88195a8a5538d3a2f5c0657981488e38829b7/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts). Команды ниже описывают прежний протокол и не являются инструкцией запуска текущего pipeline. Сохранённые измерения не пересчитаны. [Миграция и ограничения](https://github.com/aicommunity/Nmsdk/blob/develop/Docs/StructTrain/TimeLearner/AsymRmLauncherRetirement.ru.md).

# Signal Fidelity Report

Generated during pilot v4 infrastructure setup.

## Reference (LtzCal Done)

Source: `AsymRmLtzCal/EXP_span25ms_packA_gen`  
Config: `signal_reference_span25.json`

- L: `6 5 4 1`
- `all_non_ref_sync_ok`: true
- `IsNeedToTrain`: 0

## Preinh integrity (phase 4a)

Verdict: **CORRUPT** — см. `PREINH_INTEGRITY_REPORT.md`

- Sentinel `last_abs_dt=1.501` на всех дендритах
- `peak_valid=false`, traces повреждены (disk-full era)
- **Рекомендация:** cold reset + `run_pilot_v4_preinh.sh`

## Интеграция

- `analyze_signal_fidelity.py` — метрики и gate vs reference JSON
- `run_asymrm.sh` — snapshot после length steps, gate перед amp
