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
cmake --preset linux-gcc-debug-local
cmake --build build/linux-gcc-debug-local \
  --target Nmsdk-PulseLib.core NeuroModelerConsole -j"$(nproc)"
sha256sum Bin/Platform/Linux/NeuroModelerConsole
git rev-parse HEAD
git -C Bin rev-parse HEAD
git -C Libraries/Nmsdk-PulseLib rev-parse HEAD
```

Не очищайте существующие исторические или грязные каталоги через `git clean` или `git reset`. У каждого запуска должна быть отдельная папка `_repro/TimeLearnerMatrixRuns/<RUN_ID>`; скрипт отклоняет пустой или небезопасный ID и не подхватывает результаты предыдущих запусков. Проверьте, что дискового места хватит на одну волну и резерв для логов; после каждой волны просматривайте фактический расход и архивируйте подтверждённые артефакты до продолжения.

До запуска просмотрите `git status --short` в корне и в `Bin`. Очередь откажется начинать волну при заранее staged изменениях или незакоммиченных изменениях файлов отчёта этой волны; это предотвращает попадание чужих правок в wave-коммит. Остальные грязные файлы не очищаются и не добавляются.

Сохранённые W01–W04 содержат 30 исходов `not_converged_at_stop` из 32. У этих результатов нет точного Console SHA, поэтому это предварительный, но сильный сигнал систематической проблемы. Первым повторите W01 из зафиксированных входов с текущей сборкой и полным runtime provenance. Если новая волна покажет несходимость, не запускайте следующую до анализа её причин. После подтверждённого завершения обучения низкая метрика разделения или отсутствие детекции записываются отдельно и сами по себе не останавливают матрицу.

## Запуск одной волны в tmux

Запускайте ровно одну волну за вызов, максимум восемь Console. После её завершения скрипт сохраняет отдельные результаты и provenance, обновляет сводные документы и коммитит результат в Bin и корневой репозиторий. Следующую волну запускайте отдельной командой только после анализа текущей. Для первого повтора используйте W01:

```bash
cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
RUN_ID="run-$(date -u +%Y%m%dT%H%M%SZ)-$$"
RUN_DIR="_repro/TimeLearnerMatrixRuns/$RUN_ID"
SESSION="tl-$RUN_ID"
mkdir -p "$RUN_DIR"
tmux new-session -d -s "$SESSION" \
  "cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain && export PYTHONUNBUFFERED=1 TIMELEARNER_MATRIX_RUN_ID='$RUN_ID' && python3 -u scripts/run_timelearner_matrix_queue.py --run-id '$RUN_ID' --waves W01 --jobs 8 > '$RUN_DIR/queue.log' 2>&1; rc=\$?; printf '%s\\n' \"\$rc\" > '$RUN_DIR/queue.exit'"
printf 'Session: %s\nRun ID: %s\nLog: %s/queue.log\n' "$SESSION" "$RUN_ID" "$RUN_DIR"
```

`--waves W01` обязателен: runner не допускает несколько волн в одном вызове. Для следующей волны замените ID, например на `--waves W02`, и создайте новый Run ID. Автоматическая пауза срабатывает при отказе/несходимости C++-тренера, ошибке оценщика, неполном результате или инфраструктурной ошибке. Если обучение завершилось, но качество разделения слабое или цель не детектируется, это фиксируется в отчёте, однако не блокирует следующие волны.

## Наблюдение

```bash
RUN_ID="вставьте Run ID, напечатанный при запуске"
tmux ls
tail -F "/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/$RUN_ID/queue.log"
cat "/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/$RUN_ID/queue_status.json"
```

Для подключения к сессии возьмите её имя из `tmux ls`:

```bash
tmux attach -t ИМЯ_СЕССИИ
```

Отсоединиться, оставив процесс работать: нажмите `Ctrl-B`, затем `D`. Потеря SSH или выключение рабочей станции не останавливает удалённую сессию.

## Запуск одного диагностического случая

Для отдельного диагностического опыта назначьте ему свой новый Run ID:

```bash
export TIMELEARNER_MATRIX_RUN_ID="single-$(date -u +%Y%m%dT%H%M%SZ)-$$"
python3 scripts/timelearner_matrix.py --prepare W07
python3 scripts/timelearner_matrix.py --case W07 W07_BR25_N1_PSI25_NEXT
```

Используйте ID из `TimeLearnerMatrix/matrix.json`. Результат и Console provenance будут в `_repro/TimeLearnerMatrixRuns/<RUN_ID>/<wave>/<case>/matrix_result.json`. Одиночный диагностический запуск не обновляет сводный документ всей волны; для отчётного результата запускайте волну целиком через queue. Файлы рабочего клона лежат отдельно от эталонных `inputs/`.

Пользовательские конфиги для ручного открытия в GUI находятся, например, здесь:

- `TimeLearnerMatrix/W07/inputs/W07_BR25_N1_PSI25_NEXT/Train/Project.ini`
- `TimeLearnerMatrix/W07/inputs/W07_BR25_N1_PSI25_NEXT/Test/Project.ini`

## Остановка и возобновление

Если нужно остановить активный запуск, отправьте `Ctrl-C` только нужной сессии и проверьте список процессов:

```bash
tmux send-keys -t ИМЯ_СЕССИИ C-c
pgrep -af '[N]euroModelerConsole' || true
```

Перед возобновлением сначала разберите остановивший очередь результат и зафиксируйте решение. Для незавершённой волны используйте тот же Run ID и тот же `--waves Wxx`: уже сохранённые случаи будут пропущены, остальные продолжатся. Для новой волны создайте новый Run ID. Перед запуском сверьте `queue_status.json`, case results и git-коммиты. Не удаляйте матрицу входов, исторические результаты или рабочие каталоги, пока не установлено, что они относятся к остановленному запуску и больше не нужны.
