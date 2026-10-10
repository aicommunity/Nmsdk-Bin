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

Не очищайте существующие исторические или грязные каталоги через `git clean` или `git reset`. Запуски используют отдельные `_repro/runs` и `_repro/TimeLearnerMatrixRuns` каталоги с идентификаторами. Проверьте, что дискового места хватит на размер первой волны и резерв для логов; после каждой волны просматривайте фактический расход и архивируйте подтверждённые артефакты до продолжения.

## Полная очередь в tmux

Одна волна содержит максимум восемь независимых обучений. Очередь последовательно готовит волну, запускает до восьми экземпляров Console, собирает каждый результат, обновляет документы и фиксирует изменения отдельными коммитами в Bin и корневом репозитории. Полный запуск занимает много времени, поэтому выполняйте его в удалённой `tmux` сессии:

```bash
mkdir -p _repro/TimeLearnerMatrixRuns
export PYTHONUNBUFFERED=1
SESSION="timelearner-matrix-$(date -u +%Y%m%dT%H%M%SZ)"
tmux new-session -d -s "$SESSION" \
  "cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain && export PYTHONUNBUFFERED=1 && python3 -u scripts/run_timelearner_matrix_queue.py --jobs 8 > _repro/TimeLearnerMatrixRuns/queue.log 2>&1; rc=\$?; printf '%s\\n' \"\$rc\" > _repro/TimeLearnerMatrixRuns/queue.exit"
printf 'Session: %s\n' "$SESSION"
```

Скрипт автоматически останавливает очередь после первой волны, где есть незаписанный/инфраструктурно неполный результат, отказ или несходимость C++ обучения, провал метрик качества либо отсутствие детекции цели. Уже завершённая волна перед остановкой попадает в отчёт и отдельные коммиты. Не обходите остановку параметром продолжения, пока причина не классифицирована, решение не записано, а следующая волна не подтверждена.

## Наблюдение

```bash
tmux ls
tail -F /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/queue.log
cat /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/queue_status.json
```

Для подключения к сессии возьмите её имя из `tmux ls`:

```bash
tmux attach -t ИМЯ_СЕССИИ
```

Отсоединиться, оставив процесс работать: нажмите `Ctrl-B`, затем `D`. Потеря SSH или выключение рабочей станции не останавливает удалённую сессию.

## Запуск одного случая после разбора предыдущей волны

После того как причина остановки расследована и зафиксирована, один случай можно подготовить и запустить отдельно:

```bash
python3 scripts/timelearner_matrix.py --prepare W07
python3 scripts/timelearner_matrix.py --case W07 W07_BR25_N1_PSI25_NEXT
```

Используйте ID из `TimeLearnerMatrix/matrix.json`. Результат будет в `_repro/TimeLearnerMatrixRuns/<wave>/<case>/matrix_result.json`; файлы рабочего клона лежат отдельно от эталонных `inputs/`.

Пользовательские конфиги для ручного открытия в GUI находятся, например, здесь:

- `TimeLearnerMatrix/W07/inputs/W07_BR25_N1_PSI25_NEXT/Train/Project.ini`
- `TimeLearnerMatrix/W07/inputs/W07_BR25_N1_PSI25_NEXT/Test/Project.ini`

## Остановка и возобновление

Если нужно остановить активный запуск, отправьте `Ctrl-C` только нужной сессии и проверьте список процессов:

```bash
tmux send-keys -t ИМЯ_СЕССИИ C-c
pgrep -af '[N]euroModelerConsole' || true
```

Перед возобновлением сначала разберите остановивший очередь результат и зафиксируйте решение. После этого запустите очередь с первой ещё не выполненной волны через `--from-wave Wxx`, предварительно сверив `queue_status.json`, сохранённые case results и git-коммиты. Не удаляйте матрицу входов, исторические результаты или рабочие каталоги, пока не установлено, что они относятся к остановленному запуску и больше не нужны.
