# TimeNeuronTimeLearnerBranch_NextSegInh

Cold train `NNeuronTimeLearnerBranch` with **`EnableNextSegmentInhibition=1`**:

- Exc @ `Dendrite1_{L[k]}` + Inh @ `Dendrite1_{L[k]+1}` (`Type=1`, `R=SynapseResistanceBase`)
- Cable length = `max(L)+1`; mute links=2; Done/Calibrate links=2N

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranch_NextSegInh/Project.ini \
  -s -t 160 -x -S
```

Test: [`TimeNeuronTimeLearnerBranchTest_NextSegInh`](../TimeNeuronTimeLearnerBranchTest_NextSegInh/).

После Done (пример): `L≈[89,46,25,1]`, Inh@`{90,47,26,2}`, `gen_links=8`, `FixedLTZ≈0.065`, tip[N−1] после amp-eq ≫ Base×N. Test → **7/8** (fn=0, fp=1).

Watch (верхний tab_1): `InputPattern`, `Generator1`, `DendriticSumPotential`, `SomaSumPotential`, `LTZone.Potential (вход)`.
