# Локальная проверка сходимости TimeLearner — 2026-10-12

Промежуточные результаты ограниченной исследовательской серии. Полная матрица не запускалась. Логика обучения и изменение состояния выполнялись C++-тренером; временный C++-вариант использовался только для диагностической проверки границы Rs.

## Происхождение

| Сборка | Исходники | Console SHA-256 |
|---|---|---|
| Чистая актуальная Windows Release | root `15d0e581`, PulseLib `2bb72a3`, Bin `67d4173` | `A27AEA59586D23ED0E585B0B01BE8CB29A0A90FF739A86B2B55651D9356039E8` |
| Диагностический Branch-вариант | те же gitlinks; Branch временно сохраняет заданный `ResistanceMin` и выводит только верхнюю границу Rs/Rm | `B048A7E0AEC1FC359A618BCC4DF4BF06FC3239752F6CA01DCDF424E4592A65DE` |

Диагностический прогон использовал один и тот же архив PHASE8 Branch100 и Sep-16 SoftCold reset. Входные хэши: `Train/Parameters_00.xml` `ae91fb50277dcd1d03e567027c281a65a0c09bdd0438ddaa0218d0b7f1f46e87`, `Train/Project.ini` `9a6ea4db7532d48bf9a97eeab968eb9eec394b915d3daa5db392626489ab4349`. Все raw logs и временные workdirs находятся в локальной папке `temp/historical_view`, в репозиторий не добавляются.

## Разделение C++ сходимости и качества

| Условие | C++ обучение | Качество после обучения |
|---|---|---|
| PHASE8 Branch25, историческая сборка | `Need=0`, `L=13 11 7 1` | Повторный gate не прошёл Windows-подготовку; исторический отчёт описывает качество отдельно |
| PHASE8 Branch25, текущая сборка | `Need=0`, `L=7 6 4 1` | Повторный gate не прошёл Windows-подготовку; качество этого replay не измерено |
| PHASE8 Branch100, историческая сборка | `Need=0`, `L=25 21 11 1` | Повторный gate не прошёл Windows-подготовку; качество этого replay не измерено |
| PHASE8 Branch100, текущая нижняя граница Rs | `Need=1` при административной остановке на iter131; C++ failure не зарегистрирован | Не оценено |
| PHASE8 Branch100, временный C++-вариант с `ResistanceMin=20M` | `Need=0` на poll#8, обычные итерации до 16; phase 2; оба EOL-предиката 1; все пики валидны; `L=25 21 11 1`; `Rs≈73.99, 88.93, 133.36, 517.29M`; `Rmax=10G` | Один полный пробный ряд записан: target class 1 не сработал (`false negative`). Полная матрица/Acc/FP не измерены |
| PHASE8 Branch25, текущий C++ с диагностическим `ResistanceMin=20M` | `Need=0` на poll#7; phase 2; оба EOL=1; все пики валидны; `L=7 6 4 1`; `Rs≈50.72, 91.92, 204.55, 375.15M`; `Rmax=10G`; `failure_reason=0` | Gate завершился ошибкой до полного Test; метрики отсутствуют |
| W04 `BR100_N1_PSIoff`, официальный вход матрицы, штатный `Rmin=10k` | Административная остановка с `Need=1` на iter131; `L=25 21 11 1`; `Rs≈0.336M, 0.728M, 34.61M, 86M`; `failure_reason=0` | Не оценено |
| Тот же W04 вход, диагностический `Rmin=10M`, `Rmax=10G` | `Need=0`; максимум обычной итерации 17; phase 2, оба EOL=1, все пики валидны; `L=25 21 11 1`; `Rs≈36.996M, 44.467M, 133.362M, 521.899M`; `failure_reason=0` | Gate завершился ошибкой до полного Test; метрики не получены |
| Тот же W04 вход, диагностический C++-вариант с `Rmin=20M`, `Rmax=10G` | `Need=0`; максимальная обычная итерация 16; phase 2; оба EOL=1; пики `[1,1,1,1]`; `L=25 21 11 1`; `Rs≈73.99M, 88.93M, 133.36M, 517.29M`; `failure_reason=0` | Gate завершился ошибкой до полного Test; одна строка `target class 1` — false negative; агрегатные метрики отсутствуют |

Для W04 сравнений совпадает SHA-256 исходного `matrix_input_manifest`: `c5926b5c6c44abf18304e82b908d1c2fff832c7657344e2a4276e3641cebcdd7`. Вход содержит `ResistanceMin=20M`; текущий C++ выводит вместо него `10k` при `Rs/Rm limit=1000`. Диагностическая сборка сохраняет заданный входом floor; отдельный runtime overlay задавал `10M`; `Rmax` оставался вычисленным (`10G`). Floor 10M и 20M оба довели W04 до `Need=0` (обычные итерации максимум 17 и 16). Новый штатный low-floor replay на 10:05 MSK ещё активен: `Need=1`, iter63, `L=1 21 11 1`, `Rs≈86M, 0.718M, 34.61M, 86M`, пики `[0,1,1,1]`, оба EOL=0, `failure_reason=0`. До завершения это не классифицируется как отказ. Полученные пары поддерживают нижнюю границу порядка `Rm` для этого Branch100 примера; для всех конфигов и тренеров правило ещё не доказано.

Аудит итераций и исходник подтверждают, что Branch `phase=0` — совместное обучение длины и сопротивления. На iter1 обоих W04 вариантов, пока `eol_sync=0`, активный TipR снизился с `86M` примерно до `57.65M`. `FinishTrainingIteration` вызывает `ChangeDendriteStatus`, затем `ChangeSynapseStatus`, который в параметрическом режиме меняет сопротивление. Значит, нет отдельного этапа полной синхронизации до начала подстройки Rs: эти изменения могут идти совместно. PHASE8 Branch25 достигает `Need=0` и с low-floor current, и с диагностическим floor 20M; отрицательный эффект низкой границы пока наблюдается только на двух Branch100 условиях.

В low-floor PHASE8 Branch25 audit минимум TipR был `14.53M` при `Rmin=10k`, затем C++ завершил обучение с `Need=0`. В парном диагностическом запуске `Rmin=20M` также получен `Need=0`. Это дополнительный контроль, показывающий, что пересечение Rs уровня 20M само по себе не объясняет все случаи.

### Near-target stall в W04 low-floor

В актуальном C++ при штатном `Rmin=10k` на итерациях 50–80 активный TipR W04 чередуется около `717.43k/718.16k`, а `amp_dt` — `+1.1e-5/-3.4e-5`. Эти значения пересекают `AmpNormEps=1e-5`, но остаются в `kAmpOscillationBand=0.005`. `NoImproveResistanceCount` при этом повторяет 0/1 вместо достижения требуемых трёх near-target событий.

Исходник задаёт `kResistanceSettleRatio=1e-3`; когда damped-P шаг становится меньше, fallback принудительно делает шаг 0.1%, что поддерживает двухточечную осцилляцию. EOL разрешает near-target осцилляцию лишь после достижения счётчика, который сбрасывается на каждой второй итерации при частичном уменьшении ошибки. Это подтверждённый для W04 дефект сходимости/счётчика. Диагностические floors 10M и 20M доходят до `Need=0`, обходя этот участок; изменение нижней границы не является доказательством исправления механизма.

На 10:05 MSK Classic50 N0 (`W01_CL50_N0_PSIoff`) сохранил `IsNeedToTrain=0` с `L=27 22 15 1`; все пики валидны. Последняя audit-строка ещё `phase=0;need=1;eol_sync=1;eol_amp=1`, поскольку C++ вызывает `EndOfLearning` после записи audit и сохраняет Done позже. Для Classic100 N0 пока `Need=1`, iter103, `L=55 43 27 1`, `eol_sync=0`, `eol_amp=0`, все пики валидны. Длинный диагностический Branch480 с `Rmin=20M` на iter232 остаётся `Need=1`, `L=1 61 89 1`, первый пик невалиден, `eol_sync=0`, `eol_amp=1`, без C++ failure; запуск продолжается до `-t=900`.

Quality-gate в Windows имеет две platform-зависимые операции: прямой запуск `copy_config_branch.sh` и проверку длительности процесса через Unix `ps`. После обхода только подготовки Train→Test одна полная строка `results.csv` показала FN; контроллер упал на `ps`, а неполный Test был остановлен. Это не меняет подтверждённый `Need=0` C++ Train. Качество остаётся частично измеренным.

## Чистые текущие повторы

Снимок на 2026-10-12, 09:24 местного времени; оба процесса ещё работали.

| Условие | Итерация / длины | Peaks / EOL / failure | Статус |
|---|---|---|---|
| Classic 50 N0 PSI off | iter105; `L=29 22 15 1`; `Need=1` | все пики валидны; фаза 0; `failure_reason=0` | В процессе; длина менялась |
| Classic 100 N0 PSI off | iter74; `L=52 46 27 1`; `Need=1` | все пики валидны; фаза 0; `failure_reason=0` | В процессе; длина менялась |

Ранее остановленные чистые диагностические случаи сохраняются как неполные наблюдения: Classic25 N1 дошёл до заданного `-t=160` с `Need=1`; Classic100 N1 (PSI off и PSI25) имел чередование валидности пиков и аномально больших амплитуд; Branch100 N0/N1 и Branch480 N1 были административно остановлены при `Need=1`. Ни один из этих остановленных процессов не даёт основания заявлять математическую невозможность решения. Подробная трасса и хронология — в root-аудите `HISTORICAL_CONVERGENCE_INVESTIGATION_2026-10-12.ru.md`.

## Следующие проверки

1. Довести два чистых Classic структурных контроля до `Need=0` или естественного завершения `-t`, сохранив причины остановки.
2. Повторить диагностический высокий `ResistanceMin` на одном коротком и одном длинном проблемном Branch/Classic случае, чтобы проверить, ограничен ли эффект PHASE8 Branch100.
3. Только после сопоставления этих трасс выбрать реализацию параметра нижней границы Rs. Не менять метрики классификации и не выдавать отсутствие полной оценки качества за PASS.

### Branch480: диагностика порядка сегментов и первого импульса

Вопрос о «первом дендрите, который не растёт» требует учитывать обратный порядок Branch: SelectActiveDendrite() начинает с последнего импульса, а после Done для индекса k переключается на k-1. Поэтому индекс 0 должен оставаться длины 1, пока не завершится индекс 1. В парном W04 Branch480 прогоне с исправлением порядка именно индекс 1 остановился до перехода к индексу 0.

В C++ исправлен отдельный переход: если активный и опорный пики валидны, но L[k] <= L[k+1] (либо длина активного сегмента не больше anchor), Branch запрашивает рост независимо от локального dt. При достижении максимальной длины с неустранимым нарушением записывается failure_reason=2. Без валидного пика длина не меняется. Проверки перехода и сопротивлений прошли 11/11.

Сопоставленный диагностический replay W04 BR480_N1_PSIoff сохранил конфиговый Rmin=20M, Rmax=10G; входной matrix manifest SHA-256 98804501259455fd8815cdb05e85924a00b68bff143a89617275e6194893d340; Console SHA-256 21ba9e9e798d0177f67ceaa65b7fb041fd9c39eeb7f21017ec767a2d94c92da8. После reset длины были [1,1,1,1]. Активный индекс 1 вырос 6→10 на iter9 и восстановил порядок относительно индекса 2 (L=6). На iter10 его пик упал до ≈2.44e-8 и стал невалидным; TipR обоих внутренних сегментов был на Rmin=20M. До iter218 включительно состояние не менялось: Need=1, active index 1, phase=0, оба EOL=0, failure_reason=0. Остановка выполнена вручную после 14 последовательных autosave без изменения состояния; результат — not_converged_at_stop, качество не оценивалось.

Итог по гипотезе: первый индекс не нарушает порядок запуска сам по себе, поскольку алгоритм обходит импульсы справа налево. Но наблюдаемый стоп у индекса 1 блокирует обучение первого импульса. Порядок длины был исправлен; потеря пика после роста осталась отдельной проблемой. Она наблюдалась также на low-floor W04 Branch480, поэтому не объясняется только Rmin=20M. Пока нельзя определить, является ли дальнейшая остановка объективным пределом данной модели или пропущенным C++-переходом; нужен отдельный разбор критерия валидности пика и действий тренера при потере измерения. См. полный разбор в [аудите сходимости](../../../../../Docs/Audit/TimeLearner-2026-09-26-review/HISTORICAL_CONVERGENCE_INVESTIGATION_2026-10-12.ru.md).

Артефакты replay сохранены локально в Bin, но исключены из обычного коммита: результат и provenance — Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/investigation-20261012-branch-order-fix-rmin20m/W04/W04_BR480_N1_PSIoff/{matrix_result.json,provenance.json}; исходная трасса — Configs/SpikeSamples/StructTrain/_repro/runs/W04_BR480_N1_PSIoff_20261012T090437Z_44844_105f4f2a_work/Train/TimeLearnerTrainingAudit.log (SHA-256 a5a50ec1c3b8656989759aaa75667f9e7ff362ba1b5ea655d42171c5ee4eb2a0); sidecar ручной остановки — Configs/SpikeSamples/StructTrain/_repro/runs/manual_stop_snapshots/W04_BR480_N1_PSIoff_20261012T090437Z_44844_manual_stop_note.json. Матрица пометила запуск not_converged_at_stop; C++ отказ и качество не подтверждены.

## Парная C++-абляция: фиксация Rs после первого общего sync

На одном PHASE6 EXP_480_gen_posttune/Train сравнили обычный Classic Parametric с C++ диагностическим режимом FreezeTipResistanceAfterFirstSync. Флаг выключен по умолчанию. При первом AllDendritesSynced()==true C++ перестаёт применять дальнейшие AmpNorm- и length-feedforward изменения TipR. Скрипт только устанавливает флаг в экспериментальном XML и наблюдает за C++ audit.

Условия пары одинаковы: gamma=0.05, автооценка gamma off, EstDelayPerSeg=0.01, IterationGap=1.5, SyncTolerance=20ms, Rmin=1k, Rmax=100G, исходный TipR 86M, MaxLen=100, W3 off. Итерации 0–19 совпали по EOL, gamma, Rs, AmpDt, timing, длинам и статусам длины: различий 0. Фиксация сработала на итерации 20 при первом eol_sync=1.

| Режим | Состояние на iter23 | Итог окна |
|---|---|---|
| Обычные изменения Rs | eol_sync=0, длины [51,41,25,1], первый abs(dt)=20.5ms; Rs к этому времени рос до сотен МОм и ГΩ | 40 мин наблюдения, итерация 37: Need=1, failure_reason=0, eol_sync=0; второй TipR достиг 100G |
| Rs заморожен после первого sync | eol_sync=1, те же длины, первый abs(dt)=16.5ms; Rs=[7.06M,255.82M,1k,86M] осталось неизменным | Зафиксировано шесть итераций после sync, до iter26 включительно: eol_sync=1; Need=1, eol_amp=0, failure_reason=0. Остановлено внешним лимитом, это не отказ C++ и не Done |

В данной конфигурации изменение сопротивления синапса после sync способно сдвинуть измеренный timing за границу SyncTolerance; длины в момент расхождения ещё одинаковы. Это подтверждает влияние сопротивления на синхронизацию, но не доказывает причину всех незавершённых обучений. Замороженный прогон намеренно остановил AmpNorm, поэтому его Need=1 ожидаем и не сравнивается с метрикой сходимости. Результат говорит об алгоритмическом взаимодействии регулятора амплитуды с временным критерием, а не о доказанном дефекте кода.

Сборка Console SHA-256: baseline 048FF11EE26E18F838BE6D6CDB1F0FA847ADE3587B88D2392A1D18FF9AA5F9F8, диагностическая 1B6006554728555C25C6398128947EC46751B0E78E4617A7CD0109FB7105864B. PulseLib_StorageComponents прошёл 1/1. Полный provenance и iteration audit: diagnostics/phase6_first_sync_rs_freeze_provenance_2026-10-12.json, diagnostics/phase6_first_sync_rs_freeze_iteration_audit_2026-10-12.csv.

Следующий шаг — точный повтор исторического PHASE6 Need=0 с восстановленными Train/границами сопротивления и максимально точным C++ provenance; затем отдельно проверить исторический EstDelayPerSeg=0.005 на актуальной сборке. Результат Classic не переносить на Branch без отдельного Branch-контроля. Качество классификации продолжать фиксировать отдельно, но не оптимизировать.

## Исторический PHASE6: повтор на сентябрьском и октябрьском исходниках

Сохранённая запись `Bin@b8cef720` от `2026-09-21T21:56Z` для `phase6_480` сообщает `done_canon`, `Need=0`, `mid_source=cpp`, маску `10000010` и `acc=7/8`. По историческому harness, перед запуском Train выполнялся SoftCold reset с `Need=1`, а запуск принимался как завершённый при `Need=0` или C++ Train PostTune-флаге; helper мог сбросить Need только при наличии такого Train-флага или прочитанного из него порога. Финальный Train XML в Git имеет `Need=0`, поэтому это сильное, но не полностью независимо аудируемое свидетельство C++ Done. Поле `mid_source=cpp` относится к Test: в Git сохранён `Test/posttune_complete.flag` с `inference=1` и `mid=0.0168963`; Train PostTune-флаг и исходный Console SHA не сохранены.

Один и тот же архивный `EXP_480_gen_posttune/Train`, одинаковый SoftCold reset и PostTrain Mode 1 повторены с двумя источниками:

| Источник | Итог наблюдения |
|---|---|
| Root `94094ad7` + PulseLib `fb3a41f5`, Console SHA-256 `4c903c3d…d55b935` | Внешняя остановка через 67.5 мин, iter53 / model time 106.135 с. `Need=1`, C++ flag отсутствует, `failure_reason=0`; `L=[97,81,49,1]`; три TipR на `100G`; AmpDt примерно `[-63.645,-63.913,-51.090]` мВ; `|dt|` внутри 20 мс. Не C++ отказ и не Done. |
| Root `59d2100c` + PulseLib `b32d7158` от 6 октября, Console SHA-256 `bc161351…dcbf0f` | Внешняя остановка через 68.26 мин, iter50 / model time 102.662 с (последний sample модели — 104.0865 с). `Need=1`, C++ flag отсутствует; `L=[97,81,49,1]`; три TipR на `100G`; AmpDt примерно `[-63.645,-63.896,-48.437]` мВ; `|dt|=[16,16,14.5]` мс. Не C++ отказ и не Done. |

На обоих источниках виден близкий плато-исход: Rmax достигнут при сильном overshoot амплитуды. В `b32d715` код удерживает сопротивление на Rmax при overshoot и не компенсирует его ростом длины. Это объясняет наблюдаемое поведение данного пути, но исторический Console от 21 сентября не идентифицирован; результаты повторов цензурированы примерно через час при `-t=900`. Поэтому категория расхождения — недостаточно точный provenance/неполное наблюдение, не доказанный отказ и не доказательство невозможности обучения.

Provenance и полные iteration audit сохранены в `diagnostics/phase6_historical_positive_replay_pre_oct_{provenance,iteration_audit}_2026-10-12.*` и `diagnostics/phase6_historical_positive_replay_oct06_{provenance,iteration_audit}_2026-10-12.*`. Следом нужно искать исходный Linux Console/SHA или, если его нет, сравнить на восстановленном `94094/fb3a41f5` старый `EstDelayPerSeg=0.005` и выключенный поздний AutoScale в контролируемой паре. W3 пока не менять.

### Historical SoftCold reset and active PHASE6 replays (12 Oct, 23:50 MSK)

The Bin history shows that PHASE6 comparisons also cross a reset-protocol change. The helper in `Bin@b8cef720` (blob `5004d741b3503a78b4603b4e2e800d42e7fe6cb3`) set `StructureBuildMode=1`, retained Model cable segments above tip-1, and reset length tags to `1 1 1 1`. Bin commit `0bb8125d` on 30 Sep changed this to set all `StructureBuildMode=2`, strip Model to tip-1, and align scalar `NumDendriteMembraneParts=1`. Its comment records the reason: fat Model with L=1 produced `DelayLenOf=0`/`TIMING_SPAN_MISMATCH`, and a leftover `StructureBuildMode=0` blocked rebuild. This is an input-reset protocol change, separate from the C++ learner transitions, and a confounder in September versus October comparisons.

Two full-window replays now explicitly use the exact b8 helper. Both have matching input SHA-256 values: Model `c5871e2c…e37faa5`, Parameters `8922e92b…e77ac2`, Project `b31f69e8…214cc69`, Interface `c5f90131…635124`; prelaunch `Need=1`, L=`1 1 1 1`, TipR=`86M` on all inputs, PostTrain Mode 1. Both use `-t=900`.

| Variant | Root / PulseLib / Bin | Console SHA-256 | Status at 23:50 MSK |
|---|---|---|---|
| Reconstructed September source | `94094ad7` / `fb3a41f5` / `0701d205` | `4c903c3d…d55b935` | PID 45080 alive after about 10 minutes; StatisticLog growing; no final status. |
| PulseLib parent before W3 change | `59d2100c` / `9b63613e` / `6633b357` | `7addef68…8b46006` | PID 53376 alive after about 3 minutes; StatisticLog growing; no final status. |

Both runs are censored observations so far, not refusals or Done. The second uses PulseLib parent `9b63613e` before `b32d7158`, which changed the Rmax-dwell response to amplitude overshoot. The existing `b32d7158` replay used the same Root `59d2100c`, Bin `6633b357`, reset, and inputs, but was stopped externally after about 68 minutes at model-time about 104 seconds. The new parent replay is still running, so a complete W3 comparison is not yet available. Replay logs live in local `temp/historical_view/runs/` and are not committed.

See the root audit for detailed provenance and interpretation: `Docs/Audit/TimeLearner-2026-09-26-review/HISTORICAL_CONVERGENCE_INVESTIGATION_2026-10-12.ru.md`.

### Reset XML detail and AutoScale control (13 Oct, 00:06 MSK)

The post-reset XML was checked in all three run directories. Both `Parameters_00.xml` and `Model_00.xml` contain `StructureBuildMode=[1,2]`; `NumDendriteMembraneParts` is absent. The old b8 helper changed only the first matching StructureBuildMode tag, so it did not set one value for every tag.

Source `94094/fb3a41f5` defaults `EstDelayPerSeg` to 0.005 s per segment and predates `AutoScaleIterationGap`. PulseLib commit `fd79b0f` (22 Sep) added autoscaling. At `9b63613e`, autoscaling defaults on while EstDelayPerSeg still defaults to 0.005. The `9b63613e` replay therefore includes the later inter-iteration timing protocol.

A third control, `phase6_positive_replay_9b63613_autoscale0_full900_20261013`, now runs on the same `9b63613e` Console and old reset. Its only effective difference from the full autoscale-on run is `AutoScaleIterationGap=0`; EstDelayPerSeg is explicitly 0.005 in both Model and Parameters. Console SHA-256 `7addef68…8b46006`; PID 39520.

Latest trace snapshot at 00:06 MSK (all processes alive; no C++ completion flag):

| Source / mode | model time | L | TipR (ohm) | Status |
|---|---:|---|---|---|
| `94094/fb3a41f5` | 25.053 s | `[33,33,33,1]` | `[20M,20M,20M,86M]` | Lengths still grow; not Done. |
| `9b63613e`, autoscale default | 17.334 s | `[25,25,9,1]` | `[20M,20M,52.46M,86M]` | In progress; not Done. |
| `9b63613e`, autoscale off | 3.227 s | `[9,1,1,1]` | `[57.65M,86M,86M,86M]` | Recently started; compare at equal model time. |

These snapshots show progress at unequal model times and do not establish which variant converges faster. All three use `-t=900`; none has reached natural limit or C++ Done/refusal. Provenance is in the local run directories; full StatisticLog files are not in Git.

### First trajectory divergence isolated with a 1.50 s delay control (13 Oct, 01:03 MSK)

The first differing state between the September reconstruction (`94094/fb3a41f5`) and the October pre-W3 source (`9b63613e`) occurs at iteration 6. To test whether the 50 ms cadence shift was causal, a short fourth run used the same `9b63613e` source, b8 reset, input XML, `AutoScaleIterationGap=0`, and `EstDelayPerSeg=0.005` as the preceding autoscale-off run. A temporary PulseLib build changed only `EffectiveDatasetDelaySec()`'s `late_bound` from `1.5 + 0.05` to `1.5`; no production source was edited.

The trace shows the following transition (times are relative to iteration 0):

| Run | Iteration cadence | State at iteration 5 | State at iteration 6 |
|---|---:|---|---|
| September `94094/fb3a41f5` | 1.991 s | `L=[17,17,9,1]`, `Rs3=52.4568MΩ` | `L=[17,17,17,1]`, `Rs3=20MΩ` |
| October `9b63613e`, AutoScale on | 2.041 s | `L=[17,17,9,1]`, `Rs3=52.4568MΩ` | `L=[17,17,9,1]`, `Rs3=52.4568MΩ` |
| October `9b63613e`, AutoScale off | 2.041 s | `L=[17,17,9,1]`, `Rs3=52.4568MΩ` | `L=[17,17,9,1]`, `Rs3=52.4568MΩ` |
| October `9b63613e`, only `late_bound=1.5` | 1.991 s | `L=[17,17,9,1]`, `Rs3=52.4568MΩ` | `L=[17,17,17,1]`, `Rs3=20MΩ` |

Across iterations 0–6, the historical source and the delay-control run match in all recorded vectors (`L`, tip resistance, `LastAbsDt`, `AmpDt`); the absolute sample clocks differ only by their initial offset and a 0.5 ms tick quantization at later rows. Turning AutoScale off alone leaves the October trajectory unchanged through iteration 6. Lowering only the new 50 ms floor restores both the 1.991 s cadence and the historical third-dendrite growth/R update. For this PHASE6 case, the delay-floor change is therefore sufficient to explain the first trajectory divergence; this is a timing/protocol regression in the current source path, not evidence that the structural algorithm cannot grow that dendrite.

The short control stopped at model time 14 s with `Need=1`, `failure_reason=0`, and no C++ completion flag. It proves neither full convergence nor historical `Need=0`. The exact internal predicate affected by the timing change is not identified because the saved traces do not include `DendStatus` and `DelayFromPulse`. The temporary build already emits some debug messages through the RDK logger, but its file logger failed to create a log (`No such file or directory`); the next diagnostic should make those C++ decisions persist in the run bundle, or add a read-only per-iteration trace keyed to the stimulus sample.

At 01:03 MSK, the three `-t=900` matched-input runs were still active and censored: `94094/fb3a41f5` at model time 64.033 s (`L=[89,81,49,1]`), `9b63613e` AutoScale-on at 55.131 s (`L=[73,73,49,1]`), and AutoScale-off at 42.571 s (`L=[57,57,41,1]`). A separate new-reset replay remains active but is excluded from this matched-reset comparison. These differing-time snapshots are not convergence outcomes.

The compact row-level comparison and complete provenance are in `diagnostics/phase6_first_divergence_delay_control_2026-10-13.csv` and `diagnostics/phase6_first_divergence_delay_control_provenance_2026-10-13.json`. Raw run logs and the temporary one-line source overlay remain in local `temp/historical_view/runs/` and are not committed. The alternate Console linked and ran (SHA-256 `e252b0156852956acd9bf00951189c932bd6c2f04354e94066e5d0d8c396c86f`); the post-build runtime-DLL copy step failed because `glog.dll` was locked by the concurrent runs. The source overlay was restored after building.

### C++ decision at the first divergent iteration: near-zero delay rejected (13 Oct, 01:36 MSK)

A debug-enabled short replay used the same `9b63613e` Console (`7addef68…8b46006`), old b8 reset, `AutoScaleIterationGap=0`, and exact pre-run input hashes recorded for the matched October run. It ended at `model time=13.9995 s`, the `-t=14` cap, with `Need=1`, `failure_reason=0`, no C++ Done, and `L=[17,17,9,1]`. The native RDK JSON sink persisted the C++ decision; the compact six-event excerpt and finalized run provenance are in `diagnostics/phase6_delay_roundoff_gate_events_2026-10-13.jsonl` and `diagnostics/phase6_delay_roundoff_gate_provenance_2026-10-13.json`.

At iteration 6, the third input dendrite (zero-based index 2) is active. Its peak is valid, and both expected and measured peak-relative times are 0.24 s. Subtracting those double-precision timestamps yields `DelayFromPulse=-1.7763568394002505e-15 s`, effectively zero. The Classic C++ code checks `delay_k < 0.0` with no tolerance. That sends the measurement to the invalid-delay path, where growth is re-enabled only if the active dendrite is no longer than the last-pulse reference dendrite. Here the active cable is length 9 and the reference is length 1, so `DendStatus` remains 0 and the iteration performs no length update. All four peaks are valid; the issue is the strict sign check at a floating-point boundary, not absence of a measured peak.

This narrows the earlier timing result: the 50 ms floor changes the cadence from 1.991 to 2.041 s and is sufficient to change the iteration-6 outcome, while the immediate C++ branch is a numerical boundary condition that treats a roundoff-negative zero as physically invalid. The 1.50 s control grows the same dendrite to length 17 and sets its TipR to 20 MΩ on iteration 6. Its detailed `DelayFromPulse` was not logged, so the cadence-dependent sign flip is strongly supported by the paired state transition but still needs a tolerance-only C++ control. The strict guard dates to PulseLib commit `88ac2f4` (12 Aug) and is present in the tested `9b63613e` source.

**Classification:** confirmed narrow Classic implementation defect in the handling of near-zero measured delay, with a demonstrated skipped growth decision in this PHASE6 trajectory. It does not explain every `D_algo_open` result, does not establish a final refusal or convergence, and does not address the separate report that the first dendrite stops growing. The run reached its external model-time cap with `Need=1`, so the training outcome remains censored.

**Next diagnostic:** test a small zero-boundary tolerance in Classic C++ on a restored input whose hashes match the recorded replay, then verify separately whether Branch has the same contract and behavior. Do not infer that fixing the boundary restores full convergence; first compare the iteration-6 state, then continue a bounded replay and record C++ termination separately from classification quality. The original pre-run XML bytes were not retained in this run directory; only their hashes are in provenance, and current Git Train sources plus the historical reset helper did not reproduce both recorded hashes. Recover or explicitly rebuild the exact input before the tolerance-only control.

### First dendrite length versus `MaxDendriteLength` (13 Oct, 02:15 MSK)

The latest statistic traces were checked for three still-running long PHASE6 replays with the historical b8 reset: September reconstruction `94094/fb3a41f5`, October `9b63613e` with AutoScale, and the same October source with AutoScale disabled. At 02:14:42 all three show `L=[97,81,49,1]` and `LastAbsDt=[16,16,14.5] ms` for the first three inputs. Their saved Train XML has `MaxDendriteLength=100` and `SyncTolerance=20 ms`; this source uses the C++ default `EstDelayPerSeg=5 ms/segment`. The first trained dendrite is indeed the longest, but it does not need to reach exactly 100: at L=97 its modeled cable delay is `(97−1)×5=480 ms`, leaving about 15–16 ms residual, already within the 20 ms synchronization tolerance. These traces disprove “the first dendrite does not grow” for this PHASE6 case and explain why it stops below the configured maximum.

This is not training completion. All three processes are still active with `-t=900`; no final status or C++ Done has been observed. Their first two TipR values are at `100 GΩ`, the third is at `85–100 GΩ`, and `AmpDt` remains about `[-63.645,-63.913,-48.437…-51.090] mV`. Thus the timing values for the three cables are within the observed sync tolerance while amplitude normalization is visibly unresolved; the remaining `Need` should be confirmed by final C++ diagnostics.

A separate replay with the new reset shows `L=[81,81,49,1]`, `LastAbsDt=[94.5,54.5,14.5] ms` at the same wall-clock snapshot and continues to grow; the first two inputs are not yet within sync tolerance. That reset protocol is different, and this is a censored in-progress snapshot, not a counterexample to the matched-reset state above. The conclusion is specific to these PHASE6 conditions: the first dendrite is longest in the matched-reset traces, while reaching `MaxDendriteLength` is not required by the configured sync gate.

### Exact-input control for the near-zero delay guard (13 Oct, 03:10 MSK)

The missing matched-input control is now complete. The archived baseline run and a tolerance-only Classic build used byte-identical Model, Parameters, Interface, and Project inputs; their SHA-256 values are recorded in `diagnostics/phase6_delay_roundoff_tolerance_pair_2026-10-13.json`. Both use root `59d2100c`, Bin `6633b357`, the same reset helper blob, and the same pre-W3 PulseLib base `9b63613e`. The Console differs only because the control changes Classic's lower delay guard from `< 0.0` to `< -1e-12 s`.

At iteration 6, both runs measured the same valid peak and raw delay `−1.7763568394002505e−15 s`. The baseline rejected this floating-point residue and kept the active dendrite at length 9 (`DendStatus=0`). The tolerance-only control treated it as zero, selected the estimated cable delay, and applied the requested update from length 9 to 17 while TipR moved from `52.4568 MΩ` to `20 MΩ`. This exact-input pair confirms that the strict zero boundary caused the missed Classic growth transition; the earlier 1.50 s cadence comparison was not the only evidence.

The production Classic fix now clamps only negative values within four machine epsilons at the absolute peak/pulse timestamp scale. It preserves the raw measurement in the C++ audit and records whether the decision value was clamped. A C++ regression test covers this PHASE6-scale roundoff and verifies that a meaningful `−1e−9 s` delay remains invalid. Branch remains unchanged because no corresponding Branch event has been found in the available traces.

This is a confirmed, narrow implementation defect in one Classic iteration, not proof that the PHASE6 training converges after the correction. The tolerance-only run reached the external model-time cap at `13.9995 s` with `Need=1`, `failure_reason=0`, both EOL flags false, and no C++ Done/refusal. The baseline was likewise censored at the cap with `Need=1`. Thus only the iteration-6 state transition is established; overall convergence and classification quality remain unresolved. Both modified C++ translation units compiled with VS2022. The `Test_PulseLib_StorageComponents` integration executable linked and passed: CTest 1/1, with all 23 GoogleTest cases passing. The Windows Console target was also rebuilt from the patched source in the local test configuration (`RDK_USE_LLM=OFF`; SHA-256 `CD6D8AE8B157C1D00A0319251C2BBB3D91C7360C16E5E3299C512A2B5D5D78B5`). It has not yet been used for a post-fix PHASE6 replay; these results verify compilation and focused C++ regression tests, not end-to-end convergence. Full provenance and final vectors are in the JSON artifact cited above; the compact original event excerpt remains in `diagnostics/phase6_delay_roundoff_gate_events_2026-10-13.jsonl`.

### Production-fix PHASE6 replay (13 Oct 2026)

The patched Windows Console was run against a fresh copy of the exact four pre-run inputs used by the archived strict-guard/tolerance-only pair (all four SHA-256 values matched). On iteration 6 it recorded `raw_delay=-1.77636e-15`, `roundoff_clamped=1`, a valid peak, and `DendStatus=1`; by the `-t 14` model-time cap the lengths were `[17,17,17,1]`. This confirms the production scale-aware clamp makes the intended transition in the simulator, not only in the regression harness. The run ended with `Need=1`, phase 0, `failure_reason=0`, both EOL predicates false; it is not a convergence result. Runtime vectors and hashes: `diagnostics/phase6_delay_roundoff_production_runtime_2026-10-13.json`; raw output remains under local `temp/historical_view/runs/phase6_production_fix_exact_inputs_t14_20261013/`.

A fresh run from the same pre-run inputs with the patched Console and `-t 900` was started as `phase6_production_fix_exact_inputs_t900_20261013` (PID 41696). At the report snapshot it was active; its status and artifacts are in the local `temp/historical_view/runs/` directory. The earlier sentence above saying a post-fix PHASE6 replay had not yet been run is superseded by this result. This replay uses the current branch Console; source and binary provenance are in the JSON record.
