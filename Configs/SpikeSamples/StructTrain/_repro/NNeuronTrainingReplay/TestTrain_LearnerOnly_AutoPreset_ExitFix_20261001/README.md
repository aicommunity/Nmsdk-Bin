# Release-smoke AutoPreset after the updated API

Date: 2026-10-01.

This clean clone is based on `../TestTrain_LearnerOnly_PostInitFix_AutoPreset_Seed_20260927`. The seed starts with `UseAutoPreset=1`, `IsNeedToTrain=1`, `DendriteLength=[1,1,1,1]`, and `NumSynapse=[1,1,1,1]`. Only project log verbosity (`DebugModeFlag`) was enabled in this clone to retain the AutoPreset trace; neuron parameters and calculation settings are unchanged.

Run from this directory:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' `
  -c '.\project.ini' -s -t 12 -x -S
```

The updated `Auto_Preset::setFirstState(PushParam)` / `GetRecParam` integration ran in the Release console. The `EventsLog` contains:

```text
Auto_Preset initial DendriteLength=[4,3,2,1] (NumSynapse unchanged).
```

The run exited with code `0`. Both saved files contain `UseAutoPreset=1`, `DendriteLength=[4,3,2,1]`, `NumSynapse=[9,7,4,1]`, nonzero `InitialSomaPotential≈[0.0157814,0.0157814,0.0157814,0.0157814]`, and `IsNeedToTrain=0`. The calibration dendrite stayed at length `1`. `--check-config .\project.ini` also returned code `0` with `VALID`.

The previous `TestTrain_LearnerOnly_AutoPreset_InterfaceCheck_20261001` run saved model data but crashed during process teardown. Investigation traced the access violation to the Release output directory containing the Debug vcpkg `glog.dll`; see the replay index for the DLL deployment fix and the separate engine-thread self-wait fix.
