# Smoke-проверка обновлённого API Auto_Preset

Дата: 01.10.2026.

Свежая копия основана на `TestTrain_LearnerOnly_PostInitFix_AutoPreset_Seed_20260927`: включён `NNeuronLearner`, `UseAutoPreset=1`, исходные `TimeStep=2000` и `CalculationMode=3`. Перед запуском сохранённые начальные длины и количества синапсов были `[1,1,1,1]`; исходные seed-файлы лежат в соседнем каталоге.

Сабмодуль обновлён для нового интерфейса `Auto_Preset::setFirstState(PushParam)` / `GetRecParam`; Release-цели `Nmsdk-PulseLib.core` и `NeuroModelerConsole` пересобраны. Запуск из каталога проекта:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' `
  -c '.\project.ini' -s -t 12 -x -S *> '.\interface-check-run.log'
```

## Результат

К 12 модельным секундам `Model_00.xml` и `Parameters_00.xml` были сохранены со значениями Learner:

- `DendriteLength=[4,3,2,1]`;
- `NumSynapse=[9,7,4,1]`;
- `InitialSomaPotential≈[0.0157814,0.0157814,0.0157814,0.0157814]`;
- `IsNeedToTrain=0`.

Это подтверждает, что свежая конфигурация с `UseAutoPreset=1` проходит обучение после замены интерфейса оценщика; последний калибровочный дендрит сохранил длину 1, и новые имена типов/поля интеграции корректно компилируются и запускаются.

Новый API отдельно проверен короткой C++-программой на тех же параметрах seed-конфига: `pattern=[0.01,0.02,0.03,0.04]`, `vectorT=[0.01,0.01,0.01,0.01]` (каждый `ExcChannel` имеет `R=1e7`, `C=1e-9`) и `tau=0.001`. `GetRecParam::recomDendriteLength` вернул `[4,3,2,1]`. Этот результат совпадает с конечной структурой Learner.

Консоль завершилась с кодом 1 после сохранения. `interface-check-run.log` содержит `Could not create logging file: Invalid argument`; файлы модели и параметров при этом записаны. Точную причину ненулевого кода завершения не установили, и прямую трассу вызова оценщика получить не удалось. Новый контракт и его численный результат подтверждены отдельным C++ smoke-вызовом; конечный результат обучения — сохранёнными файлами проекта.
