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

## Проверка узкой Classic-правки — завершена

16 октября 2026 на `.17` завершён повтор с интеграцией принятого нижнего квантованного числа контактов: `RUN_ID=w01-cl50-n0-step86m-quantlower-stepdown-fix-20261016-01`, случай `W01_CL50_N0_PSIoff`, `NormalizationMode=0`, `SynapseResistanceStep=86 МОм`, `AcceptQuantizedAmpUnderTarget=1`. Прогон занял 1:02:31 (UTC `18:42:25`—`19:44:56`), на отдельном Release-бинарнике и изолированных копиях Train/Test. Каталог и исходные тяжёлые логи остаются на Data-диске `.17`: `/media/user/Data/NmsdkRuntime/TimeLearnerAudit-20261016/quantized-lower-stepdown-fix-20261016/runs/w01-cl50-n0-step86m-quantlower-stepdown-fix-20261016-01/`.

**Обучение сошлось:** на audit-итерации 138 интеграция применила ранее принятый нижний count: третья компонента перешла с `N=99` на `N=98` (`synapse_status=-1`, `amp_quantized_under_target=1`). На итерации 139 `eol_sync=1` и `eol_amp=1`; после финализации сохранённый Train state имеет `IsNeedToTrain=0`. Runner подтвердил `converged_need0`; `training_stop_cases=0`, `execution_error_cases=0`, `evaluation_error_cases=0`.

**Качество классификации не прошло:** midpoint-проверка дала `NonSeparable` (`gap=-0.000835909485`, `landscape_ok=0`), затем полный Test завершился штатно в тихом режиме. Целевой паттерн не обнаружен, `fires=00000000`, `matches=01111111`, `Acc=7/8`, false positives `0/7`; `quality_gate_ok=false`, `separation_quality=fail`. Это подтверждает, что Classic step-down исправляет потерю принятого структурного шага и приводит этот пример к `Need=0`, но не восстанавливает распознавание цели. Качество здесь зафиксировано как отдельный исход; его оптимизация не проводилась.

Runner завершил волну как `completed_awaiting_local_commit` / `queue_completed_no_commit`; Test gate вернул `rc=0`. `child_rc=-15` относится к остановке уже завершившего обучение Console после grace period, а не к отказу тренера или оценщика. Во время запуска исходники и бинарник не менялись (`source_changed_during_run=false`, `binary_changed_during_run=false`). Provenance помечает рабочие Train-конфиги как изменённые; это ожидаемые результаты обучения в изолированном run-каталоге. Восемь исходных файлов Train/Test побайтно совпадают с парным повтором до запуска.

Исходный снимок: root `16d87dd90b49699fdf432e99348a8b9f5115f32a`, PulseLib `56a59623d896e4ef7f2c3c1c2a545985a02855af` с патчем step-down (SHA-256 `557BA3BB07FB20F42215CA8B916C533D4A31CD66EE511A71FBB8D4A6709195D9`), Bin `cfc5bcf0151dd8f5582198432fa52b007ea6e147`, Rdk `b3b2472dc347899af266cd46e64bca2a6ea16fea`. Патч теста: `4C951574B2DEA6AA4D67E00ED1D3AC1FAF7DD733F5811ABC3BCB755D37F4D16B`. Release Console SHA-256 `59734e11e001231ae695dcb49bfe02ee08e4869f06d5c0162ffce8c1350c778c`; соответствующий PulseLib fix закоммичен как `7c8f6f2`. Сборка и `PulseLib_StorageComponents` прошли до запуска.

Компактная запись результата и контрольные SHA удалённых артефактов сохранены в [`result_summary.json`](result_summary.json). Полный C++ audit (`292768` байт, 141 строка) оставлен на Data-диске `.17`, SHA-256 `321cbca6ae5df83b5e0e53c16011a839ac153f91ad5bf2a9332d84dcc31f61f3`; хеши матричного результата, provenance, входного manifest и queue status указаны в JSON. Сохранённая до этого 401-строчная исходная трасса остаётся отдельным контрольным прогоном и не перезаписана.
