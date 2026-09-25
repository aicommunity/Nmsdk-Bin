# EXP_br_span25_packA_gen_C1e9_posttune

Рабочий soft_cold-клон для posttune_verify; не PHASE12 VALIDATED_CLONE. Case: br25_on.

| Уровень | Статус |
|---|---|
| Follow-up разработчика 2026-09-23 | **FAIL** |
| Независимая проверка 2026-09-24 | Свежий cold-result не подтверждён полным run-bundle |
| Reference | [Gold EXP_br_span25_packA_gen_C1e9](../EXP_br_span25_packA_gen_C1e9/README.md) |

Источник заявленного verdict: [POSTTUNE_VERIFY_RESULT.md](../../_repro/POSTTUNE_VERIFY_RESULT.md). Сохранённые Model/Parameters/CSV/flags не обновлялись этим follow-up; их нельзя выдавать за свежий полный run. Gold PASS относится к reference, а не автоматически к этому клону.

Ограничения протокола и план: [повторный аудит](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md), [исправления и контроли](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/PLAN.ru.md), [remediation notes](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/REMEDIATION_NOTES.ru.md).

**Workspace:** `posttune_verify` по умолчанию копирует allowlist в `_repro/runs/*_work` и **не** использует этот EXP_* как исполняемый dirty tree. Current cold verdict — только после свежего run-bundle; inherited gold baseline — отдельно.

**Current D4/T3 verdict (2026-09-25):** br25_on T2 soft_cold FAIL (NonSeparable); H3/H4 no_material_diff — see evidence/tails/T3_H3_soft_vs_strip.json. Matrix: [D4_matrix_summary.json](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/D4_matrix_summary.json).
