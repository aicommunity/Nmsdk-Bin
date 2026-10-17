# EXP_span25ms_packA_gen_posttune

Рабочий soft_cold-клон для posttune_verify; не PHASE12 VALIDATED_CLONE. Case: asym25.

| Уровень | Статус |
|---|---|
| Follow-up разработчика 2026-09-23 | **FAIL** |
| Независимая проверка 2026-09-24 | Свежий cold-result не подтверждён полным run-bundle |
| Reference | [Gold EXP_span25ms_packA_gen](../EXP_span25ms_packA_gen/Test/Parameters_00.xml) |

Источник заявленного verdict: [POSTTUNE_VERIFY_RESULT.md](../../_repro/POSTTUNE_VERIFY_RESULT.md). Сохранённые Model/Parameters/CSV/flags не обновлялись этим follow-up; их нельзя выдавать за свежий полный run. Gold PASS относится к reference, а не автоматически к этому клону.

Ограничения протокола и план: [повторный аудит](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md), [исправления и контроли](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/PLAN.ru.md).

**Workspace:** `posttune_verify` по умолчанию копирует allowlist в `_repro/runs/*_work` и **не** использует этот EXP_* как исполняемый dirty tree. Current cold verdict — только после свежего run-bundle; inherited gold baseline — отдельно.

Remediation R01–R07: см. [REMEDIATION_NOTES.ru.md](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/REMEDIATION_NOTES.ru.md), [CONTROL_RUNS_P15.md](../../_repro/CONTROL_RUNS_P15.md).

**Current D4/T3 verdict (2026-09-25):** D4 `asym25_20260924T214120Z` rc=1 (gate FAIL, tipr flat). Matrix: [D4_matrix_summary.json](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/D4_matrix_summary.json).
