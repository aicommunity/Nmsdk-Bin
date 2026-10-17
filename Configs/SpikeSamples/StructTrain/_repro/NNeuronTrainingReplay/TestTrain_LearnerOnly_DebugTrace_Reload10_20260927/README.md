## RU

### Чистый клон NNeuronLearner с интервальным сохранением

Свежая исходная структура из `TestTrain` содержит только `NNeuronLearner`; `NNeuronTrainer` и его связи удалены. `UseAutoPreset=0`, параметры нейрона и исходная структура сохранены.

В `project.ini` включено `ProjectAutoSaveModelTimeInterval=2`. Функция работает в Release-сборке `NeuroModelerConsole.exe` и сохраняет текущие `Model_00.xml` и `Parameters_00.xml` по мере расчёта. Для теста можно выполнить:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 12 -x -S
```

Каталог оставлен как чистая копия для повторного запуска; экспериментальные снимки лежат отдельно в `TestTrain_LearnerOnly_AutoSaveProbe`.

## Runtime graph reload diagnostic
This clone starts from the clean fresh run saved at model time 80 (NumSynapse=119/119/119/1, DendriteLength=4/3/2/1). It tests whether stored synapse input links and response become active after reload. Run horizon: 10 model seconds. No neuron physical parameters changed.
