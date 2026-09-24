# EXP_br_span100_packA_gen_C1e9_posttune_search

Рабочий soft_cold-клон для posttune_verify; не PHASE12 VALIDATED_CLONE. Case: br100_search.

| Уровень | Статус |
|---|---|
| Follow-up разработчика 2026-09-23 | **PASS (search_reverted)** |
| Независимая проверка 2026-09-24 | Свежий cold-result не подтверждён полным run-bundle |
| Reference | [Gold EXP_br_span100_packA_gen_C1e9](../EXP_br_span100_packA_gen_C1e9/README.md) |

Источник заявленного verdict: [POSTTUNE_VERIFY_RESULT.md](../../_repro/POSTTUNE_VERIFY_RESULT.md). Сохранённые Model/Parameters/CSV/flags не обновлялись этим follow-up; их нельзя выдавать за свежий полный run. Gold PASS относится к reference, а не автоматически к этому клону.

Ограничения протокола и план: [повторный аудит](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md), [исправления и контроли](../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/PLAN.ru.md).

search_reverted означает fallback к собственному snapshot; PASS fallback не доказывает улучшение Search.
