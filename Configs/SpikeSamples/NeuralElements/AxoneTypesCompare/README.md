# AxoneTypesCompare

Сравнение типов аксона при одном `NPGenerator` (10 Hz, импульс 1 мс).

| Компонент | Класс | Параметры |
|-----------|-------|-----------|
| AxoneDelay | NAxoneDelay | DelayTime=0.005 |
| AxoneChain | NAxoneChain | NumSegments=3, Soma=NPMembraneBio, LTZone=NPulseLTZoneThreshold |
| AxoneChainAndDelay | NAxoneChainAndDelay | NumNodes=2, InternodeDelayTime=0.002 |

Сегмент: Inertial(Bias=-1)→ExcChannel; PosGenerator(+1)→InhChannel; feedback LTZone↔Soma.

## Watch

Один график: `PGenerator.Output` + выходы трёх аксонов (schemaVersion=2).
