# PostTune verify result

Generated: 2026-09-22T16:47:46Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

**Новый срез из Bin 2d1d0214:** одна строка br100_search ниже. В преамбуле upstream заявлены Train silent, search_reverted=1 и wall около 4050 s (poll#135). Сама таблица не содержит search_reverted; diff сравнивает с отдельным keep-клоном и не подтверждает и не опровергает откат к snapshot текущего Train.

Файлы Train/Test Parameters и Test/results.csv этого клона совпадают с исходным срезом e63cdcd7 после нормализации CRLF. Новые flag/полные логи и binary hash в локальном checkout отсутствуют; поэтому свежий cold-run по этим файлам независимо не подтверждён. Это не доказательство отсутствия заявленного запуска.

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_keep | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|--------------|---------|
| br100_search | done_search_diff | 0 | search | `7.42148e+07 8.9215e+07 1.33473e+08 5.2067e+08` | 0.00714187 | 0.007181835 | `10000000` | cpp | diff | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |


## Предыдущий срез 2026-09-22T11:33:05Z

Строки сохранены для истории; это skip_train smoke, а не результаты нового cold-run.

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_keep | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|--------------|---------|
| br25_on | skip_train | 0 | canon | `20000000 20000000 20000000 86000000` | 0.0717851 | 0.07179975 | `10000000` | cpp | — | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| asym25 | skip_train | 0 | flat | `86000000 86000000 86000000 86000000` | 0.037589 | 0.03758895 | `10000000` | cpp | — | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

Полный план V1–V6 этим отчётом не подтверждён. mid_source=cpp обозначает способ получения mid по эвристике verifier, а не успешную проверку landscape. [Обновлённый аудит](../AUDIT_2026-09-22.md).
