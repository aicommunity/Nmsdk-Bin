# EXP_480_gen_posttune

Рабочий soft_cold-клон для posttune_verify; не PHASE12 VALIDATED_CLONE. Case: phase6_480.

| Уровень | Статус |
|---|---|
| Follow-up разработчика 2026-09-23 | **FAIL** |
| Независимая проверка 2026-09-24 | Свежий cold-result не подтверждён полным run-bundle |
| Reference | [Gold EXP_480_gen_tiprmin](../EXP_480_gen_tiprmin/Test/Parameters_00.xml) |

Источник заявленного verdict: [POSTTUNE_VERIFY_RESULT.md](../../../_repro/POSTTUNE_VERIFY_RESULT.md). Сохранённые Model/Parameters/CSV/flags не обновлялись этим follow-up; их нельзя выдавать за свежий полный run. Gold PASS относится к reference, а не автоматически к этому клону.

Ограничения протокола и план: [повторный аудит](../../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md), [исправления и контроли](../../../../../../../Docs/Audit/TimeLearner-2026-09-24-review/PLAN.ru.md).

Текущее expectation в CASES: fires=10000010 (регрессия с одним foil FP); строгая цель 10000000 имеет отдельный verdict.
