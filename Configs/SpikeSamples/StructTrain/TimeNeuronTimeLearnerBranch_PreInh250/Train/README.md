# TimeNeuronTimeLearnerBranch_PreInh250

Cold train `NNeuronTimeLearnerBranch` with **presynaptic inhibition k=2.5**:

- `NeuronClassName = NSPNeuronGenPreinh2_5`
- `SynapseClassName = NPSynapseBioPreinh2_5` (`UsePresynapticInhibition=1`, `InhibitionCoeff=2.5`)
- Baseline Branch layout (без `EnableNextSegmentInhibition`)

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranch_PreInh250/Project.ini \
  -s -t 160 -x -S
```

## После Done (2026-08-20)

| Параметр | Значение |
|----------|----------|
| `DendriteLength` | `[97, 50, 25, 1]` |
| `TipSynapseResistance` | ≈`[4.00e6, 9.83e7, 8.20e7, 2.09e9]` |
| `FixedLTZThreshold` | **0.1136** |
| tip Exc class | `NPSynapseBioPreinh2_5` (Use=1, k=2.5) |
| gen_links | 4 |

Test: [`TimeNeuronTimeLearnerBranchTest_PreInh250`](../TimeNeuronTimeLearnerBranchTest_PreInh250/) → **7/8** (fn=0, fp=1, late_fp=3) после полного sync.  
Порог: [`../TimeNeuronTimeLearnerBranch/REPORT_preinh250_threshold.md`](../TimeNeuronTimeLearnerBranch/REPORT_preinh250_threshold.md).

Watch (верхний tab_1): `InputPattern`, `Generator1`, `DendriticSumPotential`, `SomaSumPotential`, `LTZone.Potential (вход)`.


> Layout 2026-09-10: Train/Test under one root. See ../../LAYOUT.md and ../../AUDIT_REPORT.md (Branch legacy 7/8 demoted: late_fp + per_stim).
