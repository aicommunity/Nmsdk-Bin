# AxoneChainLengthSweep

Структурная длина `NAxoneChain` (`NumSegments` 1 / 3 / 5).

Каждый сегмент — регенеративный узел (Inertial Bias=-1 + Soma + PosGenerator + LTZone).

`NumSegments=1` обязан содержать `Segment1` в XML (`Model`/`Parameters`). Смена длины в GUI через property + Reset: структура достраивается в `BuildStructure`.
