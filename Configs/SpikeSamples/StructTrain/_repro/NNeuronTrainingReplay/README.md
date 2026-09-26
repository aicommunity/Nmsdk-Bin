# Воспроизведение структурного обучения NNeuron

Эти проекты — отдельные копии примеров для проверки. Исходные конфигурации в `Bakhshiev/TestTrain` и `SpikeSamples/Classifier/SpikeIrisClassifier` не редактировались.

## Состав

| Копия | База | Назначение |
|---|---|---|
| `TestTrain_Baseline` | `Bin/Configs/Bakhshiev/TestTrain` | Обучение нового `NNeuronLearner` и `NNeuronTrainer` в одном проекте; проверка пары на одинаковом входном сценарии. |
| `TestTrain_AutoPreset` | `Bin/Configs/Bakhshiev/TestTrain` | Тот же проект, но `UseAutoPreset=1` только у `NNeuronLearner`. |
| `SpikeIrisClassifier_Baseline` | `Bin/Configs/SpikeSamples/Classifier/SpikeIrisClassifier` | Три классифицирующих `NNeuronTrainer` с исходными режимами и параметрами. |
| `TestTrain_Baseline_Fresh120` | `Bin/Configs/Bakhshiev/TestTrain` | Чистый прогон пары на 120 модельных секундах с исходным `ResetAfterLoadFlag=1`. |
| `TestTrain_Baseline_Fresh240` | `Bin/Configs/Bakhshiev/TestTrain` | Проверочный combined-клон. После сужения работ до Learner длительный запуск отложен. |
| `TestTrain_AutoPreset_Fresh240` | `Bin/Configs/Bakhshiev/TestTrain` | Проверочный combined-клон, процесс остановлен до финального сохранения при сужении работ до Learner. |
| `TestTrain_LearnerOnly_Fresh240` | `Bin/Configs/Bakhshiev/TestTrain` | Только `NNeuronLearner`, `UseAutoPreset=0`; чистый baseline-клон. Запуск без интервальных снимков остановлен через 2 ч 20 мин без итогового сохранения. |
| `TestTrain_AutoPreset_LearnerOnly_Fresh240` | `Bin/Configs/Bakhshiev/TestTrain` | Только `NNeuronLearner`, `UseAutoPreset=1`; компонент Trainer и его связи исключены из клона. Прогон сошёлся. |
| `TestTrain_LearnerOnly_AutoSaveFresh` | `Bin/Configs/Bakhshiev/TestTrain` | Чистая копия baseline Learner с `ProjectAutoSaveModelTimeInterval=2`, готовая к повторному запуску. |
| `TestTrain_LearnerOnly_AutoSaveProbe` | `Bin/Configs/Bakhshiev/TestTrain` | Снимки двух запусков с интервалом 2 секунды; журнал и временные метки подтверждают промежуточную запись `Model_00.xml` и `Parameters_00.xml`. Не чистый стартовый результат. |
| `TestTrain_AutoPreset_DebugLogCheck` | `Bin/Configs/Bakhshiev/TestTrain` | Короткая проверка записи AutoPreset с подробным журналом; не использовать для оценки скорости. |
| `SpikeIrisClassifier_Fresh240` | `Bin/Configs/SpikeSamples/Classifier/SpikeIrisClassifier` | Чистый классификационный прогон на 240 модельных секундах. |
| `SpikeIrisClassifier_Fresh1000` | `Bin/Configs/SpikeSamples/Classifier/SpikeIrisClassifier` | Клон на исходном пределе проекта 1000 модельных секунд; остановлен до финального сохранения при сужении работ до Learner. |

В клонах включены необходимые флаги обучения; режимы и численные параметры нейронов оставлены такими, как в источниках. Для длительных прогонов в `Project.ini` отключён подробный журнал (`DebugModeFlag=0`): он многократно пишет события создания компонентов и заметно замедляет расчёт. В `Project.ini` сохранён `TimeStep=2000`, а `CalculationMode=3` использует быстрый цикл с теми же временными шагами модели. Пример запуска `TestTrain` из каталога клона:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' `
  -c '.\project.ini' -s -t 240 -x -S *> '.\training-run.log'
```

Для Iris используйте `Project.ini` с заглавной `P`; в исходном проекте установлен предел 1000 модельных секунд, поэтому для проверки сходимости запускайте `-t 1000`. `-t` задаёт максимальное модельное время расчёта, `-x` завершает расчёт по его достижении, `-S` сохраняет `Model_00.xml` и `Parameters_00.xml` в копии. В консольном режиме запись `Interface.xml` пропускается, поскольку GUI-контроллеры не созданы. По фактическим прогонам интервалы 120 секунд для baseline `TestTrain` и 240 секунд для Iris не обеспечили сходимость.

Для периодического сохранения в консоли добавьте в `Project/General` проекта тег `<ProjectAutoSaveModelTimeInterval>N</ProjectAutoSaveModelTimeInterval>`, где `N` — число секунд модельного времени, `0` отключает функцию. Чистая копия `TestTrain_LearnerOnly_AutoSaveFresh` использует интервал 2 секунды; результаты сохранены в `TestTrain_LearnerOnly_AutoSaveProbe`. Конфигурация прошла `--check-config` как `VALID`. В Release-прогоне `-t 12 -x -S` журнал зафиксировал промежуточные сохранения канала 0 на модельном времени 3, 6, 9 и 12 секунд, а наблюдатель файлов увидел обновления `Model_00.xml` и `Parameters_00.xml` до заключительного `Project saved.` Это подтверждает, что снимки появляются во время расчёта; фактический порог запаздывает из-за периода опроса и ожидания движка. Запуск с `-s` без `-x` оставляет процесс работающим для наблюдения. Реализация включена только в NeuroModelerConsole; подробности и ограничения `SaveProject()` описаны в [документации консоли](../../../../../../Rdk/Docs/Console-Application.md).

Тестовый каталог запускали дважды: второй процесс продолжил структуру первого промежуточного снимка, поэтому его финальная сходимость не считается отдельным чистым сравнением baseline. Самая поздняя запись показала `IsNeedToTrain=0`, `DendriteLength=[4,3,2,1]`, `NumSynapse=[19,7,4,1]` и четыре строки обоих обучающих журналов. Короткий опыт фиксирует работу автосохранения и показывает наблюдаемый тренд, но не заменяет сравнение свежих конфигов.

Консоль собрана в `Release` (`/O2`, `NDEBUG`). Модель всё равно рассчитывает по 2000 шагов на каждую модельную секунду при исходном `TimeStep=2000`; `CalculationMode=3` ускоряет цикл исполнения, но не прореживает временные шаги. Поэтому длительный wall-clock для этих примеров ожидаем. `TimeStep` в проверочных копиях не менялся.

## Критерии разбора

- Расчёт должен дойти до заданного модельного времени и сохранить копию проекта. После сохранения консоль в этой сборке иногда завершается с известной ошибкой закрытия `UEngineControl::PauseChannel`; она не мешает анализировать сохранённую копию.
- В `NNeuronLearner` обучение считается завершённым, когда статусы изменения длин и числа синапсов обнулены; в режиме 0 при этом сбрасывается `IsNeedToTrain`.
- Для `NNeuronTrainer` основная ветка — режим 6; критерии — завершённые статусы роста и нормализации. Значения 4/5 также попадают в эту ветку по текущему fall-through.
- После обучения сравнивайте `DendriteLength`, `NumSynapse`, `TrainingDendIndexes` и `TrainingSynapsisNum`. Параметры мембран/каналов и существующих синапсов должны сохраниться. Новые синапсы получают начальное сопротивление `SynapseResistanceStep`; пока обучение активно, `LTZThreshold` может быть равен `TrainingLTZThreshold`.
- В режиме AutoPreset журнал должен содержать `Auto_Preset initial DendriteLength=[...]` либо предупреждение о fallback. Последний дендрит обязан остаться длиной 1; числа синапсов остаются начальными до дальнейшей обычной структурной процедуры Learner.
- Для классификатора проверяйте штатную работу трёх обучаемых нейронов и сохранённое распознавание исходных примеров по выходам/статистике проекта.

## Зафиксированные результаты

- `TestTrain_Baseline` на 60 модельных секундах сохранился, но оба класса ещё обучались. У `NNeuronLearner` были `DendriteLength=[4,3,2,1]`, `NumSynapse=[89,89,89,1]`, `IsNeedToTrain=1`; у `NNeuronTrainer` массивы `TrainingDendIndexes` и `TrainingSynapsisNum` оставались пустыми. Это контрольная точка, не результат сходимости.
- Чистый прогон AutoPreset с `-t 1` и подробным журналом записал `Auto_Preset initial DendriteLength=[4,3,2,1] (NumSynapse unchanged).` В сохранённом снимке числа синапсов остались `[1,1,1,1]`. Подробный журнал включён только в `TestTrain_AutoPreset_DebugLogCheck`.
- `TestTrain_AutoPreset` на 120 модельных секундах сошёлся у `NNeuronLearner`: `DendriteLength=[4,3,2,1]`, `NumSynapse=[1,1,1,1]`, заполнены четыре строки `TrainingDendIndexes` и `TrainingSynapsisNum`; `IsNeedToTrain=0`. Парный `NNeuronTrainer` ещё активен. Повторный combined-прогон на 240 секундах остановлен без финального сохранения; текущая проверка AutoPreset изолирована от Trainer.
- `TestTrain_AutoPreset_LearnerOnly_Fresh240` завершился на заданном интервале примерно за 4 минуты настенного времени, без активного `NNeuronTrainer`: `IsNeedToTrain=0`, `DendriteLength=[4,3,2,1]`, `NumSynapse=[1,1,1,1]`, матрицы `TrainingDendIndexes` и `TrainingSynapsisNum` имеют по четыре строки. Это подтверждает сходимость Learner с начальной автооценкой на данном примере.
- `TestTrain_Baseline_Fresh120` завершился примерно за 59 минут настенного времени, сохранив `IsNeedToTrain=1` у обоих классов. Learner имел `DendriteLength=[4,3,2,1]`, `NumSynapse=[179,179,179,1]`; матрицы Trainer остались пустыми. Это незавершённая контрольная точка. Чистый клон `TestTrain_Baseline_Fresh240` создан и прошёл проверку конфигурации.
- `SpikeIrisClassifier_Fresh240` достиг 240 модельных секунд примерно за 70 минут, но не сошёлся: у всех трёх `NNeuronTrainer` сохранён `IsNeedToTrain=1`, матрицы обученной структуры пусты. При этом исходный `NumDendriteMembranePartsVec=[1,1,1,1,1]` у каждого тренера изменился соответственно на `[18,9,21,19,1]`, `[13,17,11,12,1]`, `[9,13,5,4,1]`. Это подтверждает рост дендритной структуры, но не завершение Trainer. Чистый прогон на 1000 секундах остановлен без финального сохранения при сужении работ до `NNeuronLearner`.
- По уточнению пользователя последующие проверки сосредоточены на `NNeuronLearner`. Созданы и прошли `--check-config` два клона `TestTrain` с одним компонентом Learner — с `UseAutoPreset=0` и `UseAutoPreset=1`; автооценка сошлась. Чистый baseline без AutoPreset был остановлен через 2 ч 20 мин без финального снимка; файлы остались исходными.
- Эксперимент `TestTrain_Baseline_Continuation120` после сохранения промежуточного состояния исключён из результатов: при перезапуске с `ResetAfterLoadFlag=0` runtime-счётчики обучения не восстанавливаются, и у `NNeuronTrainer` записанные входные индексы расходятся с полной структурой дендритов. Для достоверного сравнения используйте свежие запуски с `ResetAfterLoadFlag=1`.
- Все шесть исходных конфигураций и новые клоны `TestTrain_*_Fresh240`, `TestTrain_*_LearnerOnly_Fresh240` и `SpikeIrisClassifier_Fresh1000` прошли `--check-config` как `VALID`. Старые проекты выдают предупреждение о `Description.rtf`. После достижения интервала консоль сохраняет снимки, затем может завершиться с кодом `-1073741819`; журнал фиксирует timeout `UEngineControl::PauseChannel`. Ошибка воспроизводится и без обучения и не относится к алгоритмам классов.
- Численное сравнение 1545 общих параметров в исходном `TestTrain` и baseline-снимке, 2393 параметров в Iris и 701 в изолированном `TestTrain_AutoPreset_LearnerOnly_Fresh240` не выявило изменений модельных значений вне структурного/временного состояния. У незавершённого baseline `TestTrain` порог `LTZone` был `0.0117` в источнике и `100` во время обучения — это установленный `TrainingLTZThreshold`, а не оптимизация параметра. `InputPattern` совпадает после нормализации XML-форматирования. Новые синапсы получают настроенный `SynapseResistanceStep`.

Все итоговые сравнения используют клоны исходных `Model_00.xml` и `Parameters_00.xml`; продолжение сохранённого промежуточного обучения не используется. Для baseline `TestTrain` 120 секунд недостаточно; изолированный Learner с AutoPreset сошёлся на 240 секундах. Контрольный baseline без AutoPreset на 240 секундах остановлен через 2 ч 20 мин без снимка; отдельный короткий autosave-прогон подтвердил периодическую запись, но не заменяет сравнение чистых долгих прогонов. Текущий объём воспроизведения сфокусирован на `NNeuronLearner`, исходном `TimeStep=2000` и выключенном обучении Trainer.

## Ограничения источников

Историческая таблица по 10 Iris-примерам показывает совпадение длин дендритов в 9 из 10 случаев; число синапсов совпадало либо отличалось на 1–2 на вход. В среднем `NNeuronLearner` завершал пример за 28,8 итерации, `NNeuronTrainer` — за 44,2 (отношение 1,53). В отчёте малые различия связываются с критериями остановки. Это ориентир конкретной выборки, а не гарантия.

Сохранённые `InputPattern` в архивных проектах `relearning_1/2` повреждены и похожи на неинициализированные значения. Для опыта с произвольной начальной структурой нужно воспроизвести паттерн из исходных файлов/протокола, а не использовать значения архива.

Полный аудит и публикации: [NNeuronStructuralTrainingAudit.md](../../../../../../Libraries/Nmsdk-PulseLib/Docs/Analysis/NNeuronStructuralTrainingAudit.md).
