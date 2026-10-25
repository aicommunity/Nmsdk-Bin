# SelectivityInhGrid — PSI × NextSeg × SegEI

Кампания Classic/Branch inhibition (2026-10-23). Источник постановки: `Docs/Audit/.../evidence/CLASSIC_BRANCH_INH_PLAN_2026-10-23.ru.md`.

- Манифест: `INH_EXP_MANIFEST.json` (72 EXP)
- Клон: `python3 clone_inh_grid.py`
- Neuron: `NSPNeuronGenSymInhC1e9`
- SoftCold cases: `inh_{c|b}{span}_{mod}_{n0|n1}_pton` via `posttune_verify.py`

Classic: 8 Mod × {25,50,100} × {N0,N1} = 48.  
Branch: 8 Mod × {25,50,100} × N1 = 24.
