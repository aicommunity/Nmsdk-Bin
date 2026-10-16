# Classic W01 structural trace — 2026-10-16

This directory contains the compact provenance/result package and the complete 401-record `TimeLearnerTrainingAudit.log` for `ampref-finishfix-w01-cl50-n0-step86m-quantlower-20261016-02`.

The attempt used Classic W01 50 ms, `NormalizationMode=0`, `SynapseResistanceStep=86 МОм`, `AcceptQuantizedAmpUnderTarget=1`, root `16d87dd90b49699fdf432e99348a8b9f5115f32a`, PulseLib `56a59623d896e4ef7f2c3c1c2a545985a02855af`, Bin `cfc5bcf0151dd8f5582198432fa52b007ea6e147`, and Release Console SHA-256 `df952fdd0b469838b730be3fd41b4c77b13bbb34ce9565e338328bf3679e1e4c`. The input manifest is `b8b85ca87ada4f99ae0056946da473ec0082cfeb23d277b3aa1c838ae7fefab4`.

## Evidence from the repeated N=99 state

Audit rows record `peak_amp` before a structural action but `num_synapse` after it. The measured count is therefore reconstructed as `num_synapse - synapse_status`. For valid, settled measurements of the third input at measured `N=99`, `L=15`, `Rs=86 МОм`, and pulse index 3, the audit contains two repeatable outcomes against target `0.0143095308`:

| State at start of measurement | Samples | Peak | Difference from target |
|---|---:|---:|---:|
| Previous iteration changed structure and called `Neuron->Reset()` | 122 | `0.0150701376469` | `+0.0007606068610` |
| Previous iteration made no structural change and did not reset | 55 | `0.0134861213558` | `−0.0008234094301` |

Example: iteration 398 measured N=99 after a prior synapse-count mutation and reset; its peak was `0.0150701376`. Iteration 399 measured the same static topology/resistance and pulse without an intervening reset; its peak was `0.0134861214`. In both rows the other measured inputs, lengths and resistances are recorded in the audit.

The trainer's `StructuralAmpQuantizationTracker` had already recorded accepted lower count 98 at iterations 393 and 398, while the current count remained 99, `synapse_status=0`, and `amp_quantized_under_target=0`. The ordinary near-target sign-reversal path held at the upper count instead of stepping down to the accepted lower count; the next warm-state observation crossed the same count's target side and invalidated the bracket. This is direct evidence of a Classic integration gap in the opt-in quantized-acceptance path. The reset/warm state difference is a separate dynamic-state inconsistency to validate in a controlled C++ experiment before changing reset policy.

`TimeLearnerTrainingAudit.log` SHA-256: `C0C26CB3C62A9960DC9424C49B3E3BD12D44114353DB393C3D28942BC8EF19A`.

Terminal result: `Need=1`, no C++ refusal, no Test evaluation. This is a training-incomplete case, not a quality result.

The current Bin and preserved local run logs contain no Branch audit with `accept_quantized_amp_under_target=1`. Branch has its own call into the tracker, but this evidence does not establish the same stall there; the pending step-down change stays Classic-only until a Branch trace demonstrates an equivalent failure.

## Проверка узкой Classic-правки — выполняется

16 октября 2026 на `.17` запущен отдельный повтор с интеграцией уже подтверждённого нижнего квантованного count: `RUN_ID=w01-cl50-n0-step86m-quantlower-stepdown-fix-20261016-01`, tmux-сессия `tl-w01-qstepdown-20261016`, случай `W01_CL50_N0_PSIoff`, `NormalizationMode=0`, `SynapseResistanceStep=86 МОм`, `AcceptQuantizedAmpUnderTarget=1`. Каталог попытки находится на Data-диске сервера в `NmsdkRuntime/TimeLearnerAudit-20261016/quantized-lower-stepdown-fix-20261016/runs/`.

Исходный снимок Console: root `16d87dd90b49699fdf432e99348a8b9f5115f32a`, PulseLib `56a59623d896e4ef7f2c3c1c2a545985a02855af`, Bin `cfc5bcf0151dd8f5582198432fa52b007ea6e147`; при сборке C++ diff был применён поверх этого снимка. SHA всех восьми Train/Test входов побайтно совпадают с предыдущим W01/50/N0 повтором, входной manifest сохранён в временной попытке. SHA-256 патча `NNeuronTimeLearner.cpp`/`NNeuronTimeLearnerStructuralAmp.h`: `557BA3BB07FB20F42215CA8B916C533D4A31CD66EE511A71FBB8D4A6709195D9`; патча теста: `4C951574B2DEA6AA4D67E00ED1D3AC1FAF7DD733F5811ABC3BCB755D37F4D16B`. После Release-сборки SHA-256 Console: `59734e11e001231ae695dcb49bfe02ee08e4869f06d5c0162ffce8c1350c778c`. После сборки тот же PulseLib diff закоммичен как `7c8f6f2`; его содержимое соответствует патчу по SHA. Release-сборка и `PulseLib_StorageComponents` прошли до запуска.

На контрольной точке 22:24 MSK Console и tmux-сессия ещё работали, C++-трасса дошла до `iter=127`, `phase=0`, `Need=1`, `failure_reason=0`; runner настроен на максимум 401 poll (это отдельный счётчик, не число C++-итераций). Это промежуточное состояние, не результат. В ERROR-логе повторилась известная инициализационная запись о невозможности вывести derived bounds до появления положительного сопротивления мембраны. Тренер продолжил работу; в последующих audit-строках `NormalizationMode=0`. Повторные `Core-SaveProject: skip Interface.xml write` совпадают с уже изученным служебным предупреждением: пропускается только запись GUI Interface после уничтожения контроллеров, само по себе оно не означает отказ тренера. Окончательный статус, Test-метрики и итоговая трасса будут добавлены после завершения попытки.
