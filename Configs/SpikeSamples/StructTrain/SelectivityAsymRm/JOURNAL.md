# SelectivityAsymRm — JOURNAL

## Phase 0 — C++ overrides

- `NPulseNeuron`: Exc/InhMembraneResistance, Exc/InhSynapseResistance, SynapseSecretionTC → `ApplyElementDefaults`.
- `NPulseSynapse::SetSecretionTC` больше не сбрасывает Ready (как Dissoc).
- UploadClass Pack A/B/C × gen/preinh; после set props — явный `ApplyElementDefaults()` (второй `Build()` no-op при Ready).
- ClDesc: NSPNeuronGen.xml + NPNeuron.xml.
- verify: cold train L=1 → Cap/Rm/InhR/Secr OK.

## Phase 1 — AsymRmSettle

См. [`../../NeuralElements/AsymRmSettle/REPORT.md`](../../NeuralElements/AsymRmSettle/REPORT.md).  
GTS=20000 для element settle; Pack C = Rm=5e6 (не C=5e-12 — osc при GTS≤20000).

## Phase 1b

AsymRm Pack A на шаблоне EXPD001C25e11: element params verified.  
Dip SomaSumPotential — только Watch (кампанийный Statistic не пишет потенциал).

## Phase 2 — grid (2026-08-27)

- GTS кампании **10000** (GTS=20000 слишком медленный + огромные StatisticLog; Activity Statistic отключён в Model).
- TRAIN_T=80, TEST_T=15, MAX_JOBS=4.
- **18/18 fire_all** @ FixedLTZ=0.0115 — как FastSpan; AsymRm не чинит селективность без калибровки LTZ.
- Next: LtzCalibrate / AutoCalibrate на лучшем pack (A), не новый Rm sweep.
