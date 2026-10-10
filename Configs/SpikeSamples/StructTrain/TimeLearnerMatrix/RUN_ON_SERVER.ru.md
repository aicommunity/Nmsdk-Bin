# Запуск TimeLearner Matrix на сервере

## Что подготовлено

В `TimeLearnerMatrix/W01`–`W04/inputs/<case>/` сохранены независимые входы каждого случая: папки `Train` и `Test`, XML/INI и `matrix_input_manifest.json` с SHA-256 конфигов. Эти исходные входы не изменяются при эксперименте. Текущая исполняемая очередь включает 32 случая (4 волны по 8); дальнейшие факторные проверки W05–W42 описаны в плане аудита, но пока не зарегистрированы в `matrix.json`.

Логика обучения остаётся в C++-тренерах, запускаемых `NeuroModelerConsole`. Python-скрипты только готовят рабочие копии, управляют процессами и собирают результаты.

## Перед запуском

Подключитесь к машине с экспериментами и перейдите в каталог:

```bash
ssh user@10.245.1.17
cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
```

Проверьте ветки и наличие Console. Для текущего закреплённого среза ожидаемый SHA-256 Console: `63c348252618ba0d05ed29bdf422c60f58cda5be5a83087f2d8c1367ff83e4ff`. Если код или бинарник обновлялись, сначала согласуйте их версии и пересоберите на сервере (на Ubuntu 24.04 может понадобиться `LD_LIBRARY_PATH` с `libglog.so.0` / boost 1.74 рядом с Console).

```bash
git -C /home/user/Nmsdk branch --show-current
git -C /home/user/Nmsdk/Bin branch --show-current
git -C /home/user/Nmsdk/Libraries/Nmsdk-PulseLib branch --show-current
sha256sum /home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
```

Проверьте, что прежняя очередь не запущена и на сервере есть место:

```bash
tmux ls
pgrep -af '[N]euroModelerConsole' || true
df -h /home/user/Nmsdk
```

Не очищайте грязные рабочие каталоги через `git clean` или `git reset`: в них есть исторические исследовательские данные. Скрипт очереди добавляет в Git только пути матрицы и отчётные файлы.

## Гибридный запуск (local + 10.245.1.17)

Рекомендуемое распределение для текущего среза:

- локально: `python3 scripts/run_timelearner_matrix_queue.py --jobs 8 --waves W01 W02` (отчёты и git-коммиты на этой машине);
- на `user@10.245.1.17` (12 ядер): только compute, без git — `python3 -u scripts/timelearner_matrix.py --prepare/--run` для W03 затем W04 с `--jobs 12` и `PYTHONUNBUFFERED=1` / при необходимости `LD_LIBRARY_PATH=.../Bin/Platform/Linux/lib`;
- после remote: `rsync` каталогов `_repro/TimeLearnerMatrixRuns/W03` и `W04`, затем локально `python3 scripts/update_timelearner_matrix_report.py W0x` и коммиты Bin/root в том же стиле, что у очереди.

Не вызывайте `run_timelearner_matrix_queue.py` на remote — он делает автокоммиты.

## Запуск всех подготовленных волн на одной машине

Команда ниже создаёт отдельную tmux-сессию с уникальным именем. Очередь выполняет W01, затем W02–W04, используя до восьми параллельных экземпляров Console. Потеря SSH-соединения или выключение рабочей станции её не прерывает.

```bash
mkdir -p _repro/TimeLearnerMatrixRuns
export PYTHONUNBUFFERED=1
SESSION="timelearner-matrix-$(date -u +%Y%m%dT%H%M%SZ)"
tmux new-session -d -s "$SESSION" \
  "cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain && export PYTHONUNBUFFERED=1 && python3 -u scripts/run_timelearner_matrix_queue.py --jobs 8 > _repro/TimeLearnerMatrixRuns/queue.log 2>&1; rc=\$?; printf '%s\n' \"\$rc\" > _repro/TimeLearnerMatrixRuns/queue.exit"
printf 'Session: %s\n' "$SESSION"
```

После каждой волны скрипт формирует компактную сводку в `TimeLearnerMatrix/Wxx/results.json`, обновляет `EXPERIMENTS.md` и `SUCCESSFUL_EXPERIMENTS.md`, затем делает отдельные коммиты в Bin и корневом репозитории. Автоматического push нет. Обычный FAIL строки считается результатом эксперимента; очередь останавливается при инфраструктурной ошибке или отсутствии сохранённого результата.

## Наблюдение и возврат после потери соединения

```bash
tmux ls
tail -F /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/queue.log
cat /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/queue_status.json
```

Чтобы открыть сессию, используйте имя из `tmux ls`:

```bash
tmux attach -t "$(tmux ls -F '#S' | grep '^timelearner-matrix-' | tail -n 1)"
```

Отсоединиться и оставить работу выполняться: нажмите `Ctrl-B`, затем `D`. При повторном подключении достаточно снова выполнить `tmux ls` и посмотреть лог. Код завершения всей очереди записывается в `_repro/TimeLearnerMatrixRuns/queue.exit`; значение `0` означает, что все волны из текущего `matrix.json` завершены и результаты сохранены.

## Запуск одного случая и просмотр конфигов

Список ID и факторов находится в `TimeLearnerMatrix/matrix.json`. Чтобы выполнить один подготовленный случай через тот же C++-путь проверки, укажите его волну и ID:

```bash
python3 scripts/timelearner_matrix.py --case W01 W01_CL25_N0_PSIoff
```

Результат отдельного случая будет записан в `_repro/TimeLearnerMatrixRuns/W01/<case>/matrix_result.json`. Код возврата `1` может означать обычный FAIL качества/обучения; смотрите JSON. Отдельный worker сам не создаёт отчёт волны и коммиты — для последовательного запуска с обновлением документов используйте очередь выше.

Входы можно открыть вручную, например:

- `TimeLearnerMatrix/W01/inputs/W01_CL25_N0_PSIoff/Train/Project.ini`
- `TimeLearnerMatrix/W01/inputs/W01_CL25_N0_PSIoff/Test/Project.ini`

Рабочие копии и выходные данные лежат отдельно в `_repro/runs/`. Не запускайте Console прямо на `inputs/Train` или `inputs/Test`, чтобы не менять сохранённый эталон.

## Остановка

Если нужно прервать очередь, отправьте Ctrl-C только её tmux-сессии и проверьте, что процессов Console не осталось:

```bash
tmux send-keys -t "$(tmux ls -F '#S' | grep '^timelearner-matrix-' | tail -n 1)" C-c
pgrep -af '[N]euroModelerConsole' || true
```

Удаляйте только незавершённые рабочие каталоги конкретного остановленного запуска в `_repro/runs/` и его временную `_repro/TimeLearnerMatrixRuns/`. Не удаляйте `TimeLearnerMatrix/Wxx/inputs` и другие исторические каталоги `_repro/runs/`.
