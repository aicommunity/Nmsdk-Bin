# Запуск полной матрицы TimeLearner на сервере

## Что подготовлено

`matrix.json` — авторитетный реестр из 312 отдельных обучающих опытов в 47 волнах, не более восьми опытов в одной волне. Полный запуск в рамках подготовки не выполнялся. Перед запуском сначала изучите [EXPERIMENTS.md](../EXPERIMENTS.md), [план волн](../../../../../Docs/Audit/TimeLearner-2026-09-26-review/plans/TimeLearner-full-matrix-waves-20261010.ru.md) и историческое покрытие.

Для каждого опыта созданы отдельные пользовательские `Train` и `Test` конфиги с `Project.ini`, моделью, параметрами, паттернами, `Interface.xml` и SHA-манифестом. В `Interface.xml` сохранены настройки графиков из исторических конфигов: валидация проверяет оба графических блока и заголовки `Pattern and Trigger`, `Soma Amplitudes`, `Dendrite Amplitudes`, `Neuron Sums` (некоторые исторические конфиги содержат дополнительные графики). Эти каталоги предназначены для ручного открытия в GUI и не должны использоваться как рабочие директории запуска.

Восемь случаев W07/W08 — отдельные конфиги Branch с одновременной проверкой `EnableNextSegmentInhibition` и пресинаптического торможения PSI. Для PSI-on сохранена отдельная привязка каждого класса синапса к совместимому классу-прототипу; генератор проверяет эту карту и материализует конфиги, а не имитирует обучение.

Вся логика обучения и изменение состояния тренеров находятся в C++. Скрипты только готовят копии конфигов, запускают C++ Console, сохраняют результаты и обновляют отчётность.

## Подготовка удалённого окружения

Подключитесь к выделенному серверу `.17` и используйте основной каталог проекта:

```bash
ssh user@10.245.1.17
cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
```

Убедитесь, что корневой репозиторий, Bin и PulseLib обновлены до согласованного коммита и подмодульные gitlink указывают на ожидаемые коммиты. Соберите Linux Console на `.17` из этого среза и сохраните её SHA-256 в provenance запуска. Перед первой волной проверьте доступное место и убедитесь, что старых процессов Console нет:

```bash
git -C /home/user/Nmsdk status --short --branch
git -C /home/user/Nmsdk/Bin status --short --branch
git -C /home/user/Nmsdk/Libraries/Nmsdk-PulseLib status --short --branch
sha256sum /home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
tmux ls
pgrep -af '[N]euroModelerConsole' || true
df -h /home/user/Nmsdk
```

Сборка выполняется в корне проекта на `.17`; локальная машина для сборки и экспериментов не используется:

```bash
cd /home/user/Nmsdk
cmake --preset linux-gcc-release-local
cmake --build build/linux-gcc-release-local \
  --target Nmsdk-PulseLib.core NeuroModelerConsole -j"$(nproc)"
sha256sum Bin/Platform/Linux/NeuroModelerConsole
git rev-parse HEAD
git -C Bin rev-parse HEAD
git -C Libraries/Nmsdk-PulseLib rev-parse HEAD
```

Не очищайте существующие исторические или грязные каталоги через `git clean` или `git reset`. Каталог `_repro/TimeLearnerMatrixRuns/<RUN_ID>` создаёт очередь атомарно; не создавайте его заранее. Повторное использование `RUN_ID` без `--resume` отклоняется. Явное возобновление разрешается только при полном совпадении исходников, gitlink-коммитов, Console, входных манифестов, состава случаев и параметров запуска. Новый запуск с теми же условиями тоже отклоняется, если не указан `--allow-repeat` с новым ID. Попытки каждого случая получают отдельные каталоги `attempt-NNNN`, поэтому логи и частичные результаты не перезаписываются. Перед пропуском ранее завершённой волны runner сверяет её provenance с текущим кодом и входами.

Не запускайте две очереди одновременно в одном checkout: общий lock сериализует регистрации и новые запуски. Проверьте, что дискового места хватит на одну волну и резерв для логов; после каждой волны просматривайте фактический расход. Не удаляйте входы, историю попыток или рабочие каталоги.

До запуска просмотрите `git status --short` в корне и в `Bin`. Очередь откажется начинать волну при заранее staged изменениях или незакоммиченных изменениях файлов отчёта этой волны; это предотвращает попадание чужих правок в wave-коммит. Остальные грязные файлы не очищаются и не добавляются.

Сохранённые W01–W04 содержат 28 случаев с `Need=1` и четыре с `Need=0`; Console SHA и исходные SHA записаны в каждой строке `results.json`. Один из 28 — явный `abort_tipr_rmax_stall` (`W02_CL480_N1_PSIoff`), остальные 27 остановились без доказанной причины отказа. Два из четырёх Need=0 имеют провал качества после обучения; у двух других оценщик завершился ошибкой. Перед запуском новых волн изучите [аудит сходимости и provenance](../../../../Docs/Audit/TimeLearner-2026-09-26-review/HISTORICAL_CONVERGENCE_INVESTIGATION_2026-10-11.ru.md). Неполная текущая матрица не доказывает математическую невозможность обучения.

## Запуск одной волны в tmux

Запускайте ровно одну волну за вызов. `--jobs` задаёт верхний предел; фактический параллелизм автоматически ограничен числом логических CPU минус одно ядро и числом уже работающих Console. При загрузке CPU выше 85% очередь приостанавливает выдачу новых случаев и возобновляет её после двух замеров подряд ниже 70%. После волны скрипт сохраняет результаты и provenance, обновляет документы и коммитит результат в Bin и корневой репозиторий. Следующую волну запускайте после анализа текущей. Для нового запуска используйте свежий Run ID:

Для больших логов задайте абсолютный корень на диске с достаточным местом. Очередь, её дочерний runner и отчётчик используют одну переменную `TIMELEARNER_MATRIX_RUNS_ROOT`. Пример для `.17`:

```bash
RUNS_ROOT="/media/user/Data/NmsdkStructTrainArchive/TimeLearnerAudit-<идентификатор>"
export TIMELEARNER_MATRIX_RUNS_ROOT="$RUNS_ROOT/runs"
mkdir -p "$TIMELEARNER_MATRIX_RUNS_ROOT"
```

```bash
cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
RUN_ID="run-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
RUNS="$TIMELEARNER_MATRIX_RUNS_ROOT"
SESSION="tl-$RUN_ID"
mkdir -p "$RUNS"
tmux new-session -d -s "$SESSION" \
  "cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain; python3 -u scripts/run_timelearner_matrix_queue.py --run-id '$RUN_ID' --waves W01 --jobs 8 > '$RUNS/$RUN_ID.launch.log' 2>&1; rc=\$?; printf '%s\\n' \"\$rc\" > '$RUNS/$RUN_ID.launch.exit'; if [ -d '$RUNS/$RUN_ID' ]; then printf '%s\\n' \"\$rc\" > '$RUNS/$RUN_ID/queue.exit'; mv -n '$RUNS/$RUN_ID.launch.log' '$RUNS/$RUN_ID/queue.log'; fi"
printf 'Session: %s\\nRun ID: %s\\nLog: %s/%s.launch.log\\n' "$SESSION" "$RUN_ID" "$RUNS" "$RUN_ID"
```

`--waves W01` обязателен: runner не допускает несколько волн в одном вызове. Для следующей волны создайте новый Run ID. Автоматическая остановка срабатывает при отказе/несходимости C++-тренера, ошибке оценщика, неполном результате или инфраструктурной ошибке. Если обучение завершилось, но качество разделения слабое или цель не детектируется, это фиксируется в отчёте, однако не блокирует следующие волны.

## Наблюдение

```bash
RUN_ID="вставьте Run ID, напечатанный при запуске"
tmux ls
tail -F "$TIMELEARNER_MATRIX_RUNS_ROOT/$RUN_ID/queue.log"
cat "$TIMELEARNER_MATRIX_RUNS_ROOT/$RUN_ID/queue_status.json"
```

Для подключения к сессии возьмите её имя из `tmux ls`:

```bash
tmux attach -t ИМЯ_СЕССИИ
```

Отсоединиться, оставив процесс работать: нажмите `Ctrl-B`, затем `D`. Потеря SSH или выключение рабочей станции не останавливает удалённую сессию.

## Запуск одного диагностического случая

Для отдельного диагностического опыта назначьте ему свой новый Run ID:

```bash
RUN_ID="single-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
export TIMELEARNER_MATRIX_RUNS_ROOT="/media/user/Data/NmsdkStructTrainArchive/TimeLearnerAudit-<идентификатор>/runs"
python3 scripts/run_timelearner_matrix_queue.py --run-id "$RUN_ID" \
  --waves W07 --case W07_BR25_N1_PSI25_NEXT --jobs 1 --no-commit
```

Используйте ID из `TimeLearnerMatrix/matrix.json`. Результат и Console provenance будут в `_repro/TimeLearnerMatrixRuns/<RUN_ID>/<wave>/<case>/attempt-0001/`. Одиночный диагностический запуск не обновляет сводный документ всей волны; для отчётного результата запускайте волну целиком через queue. Файлы рабочего клона лежат отдельно от эталонных `inputs/`. Прямой запуск `timelearner_matrix.py --case/--run` отключён, чтобы не обходить fingerprint и изоляцию попыток.

Несколько заранее выбранных случаев одной волны можно запустить параллельно в одном безопасном запуске. Для неполного набора обязателен `--no-commit`; его результаты сохраняются по отдельным каталогам попыток и не публикуются как завершённая волна:

```bash
RUN_ID="diag-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
python3 scripts/run_timelearner_matrix_queue.py --run-id "$RUN_ID" \
  --waves W04 --cases W04_BR100_N1_PSIoff W04_BR480_N1_PSIoff \
  --jobs 8 --no-commit
```

Фактический параллелизм автоматически ограничивается числом Console, свободными логическими CPU и текущей загрузкой; RUN_ID и case ID должны быть новыми либо пройти строгую проверку повтора/возобновления.

Пользовательские конфиги для ручного открытия в GUI находятся, например, здесь:

- `TimeLearnerMatrix/W07/inputs/W07_BR25_N1_PSI25_NEXT/Train/Project.ini`
- `TimeLearnerMatrix/W07/inputs/W07_BR25_N1_PSI25_NEXT/Test/Project.ini`

## Остановка и возобновление

Если нужно остановить активный запуск, отправьте `Ctrl-C` только нужной сессии и проверьте список процессов:

```bash
tmux send-keys -t ИМЯ_СЕССИИ C-c
pgrep -af '[N]euroModelerConsole' || true
```

Перед возобновлением сначала разберите остановивший очередь результат и зафиксируйте решение. Укажите тот же Run ID и добавьте `--resume`, сохранив исходные `--waves`, `--case` (если был), `--jobs`, `--max-polls` и остальные параметры. Очередь проверит точный fingerprint, пропустит только случаи с полным совпадающим provenance, а для остальных создаст следующий `attempt-NNNN`. Если изменились исходники, Console, входы или условия, возобновление будет отклонено: используйте новый Run ID. Для намеренного повтора завершённого идентичного условия используйте новый ID и явный `--allow-repeat`. Перед запуском сверьте `run_manifest.json`, `queue_status.json`, историю `queue_status_attempts/` и результаты попыток. Не удаляйте входы, исторические результаты или рабочие каталоги.
