## RU

### Чистый клон NNeuronLearner с интервальным сохранением

Свежая исходная структура из `TestTrain` содержит только `NNeuronLearner`; `NNeuronTrainer` и его связи удалены. `UseAutoPreset=0`, параметры нейрона и исходная структура сохранены.

В `project.ini` включено `ProjectAutoSaveModelTimeInterval=2`. Функция работает в Release-сборке `NeuroModelerConsole.exe` и сохраняет текущие `Model_00.xml` и `Parameters_00.xml` по мере расчёта. Для теста можно выполнить:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 12 -x -S
```

Каталог оставлен как чистая копия для повторного запуска; экспериментальные снимки лежат отдельно в `TestTrain_LearnerOnly_AutoSaveProbe`.
