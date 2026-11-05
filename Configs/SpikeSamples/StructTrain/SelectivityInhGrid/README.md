> Историческая постановка 23–25.10; не текущий launcher. Генератор `clone_inh_grid.py` удаляется из текущего дерева; исходник доступен в Bin commit `11ad066eac74d26c3e71e471c8a5998323e79176` по прежнему пути. Конфиги, INH_EXP_MANIFEST и измерения сохранены. Старое тело ниже не является актуальной спецификацией: оно называет SymInh, тогда как удалённый генератор задавал HIST AsymRm/Preinh2_5AsymRm. Фактическую физику конкретного результата нужно устанавливать по его сохранённой модели и commit, а не по этой подписи. Новые запуски — через корневой Scripts/StructTrain/TimeLearner с явными storage profiles, readback и versioned export/import. Никакой автоматический повтор кампании не выполняется.

# SelectivityInhGrid — PSI × NextSeg × SegEI

Кампания Classic/Branch inhibition (2026-10-23). Источник постановки: `Docs/Audit/.../evidence/CLASSIC_BRANCH_INH_PLAN_2026-10-23.ru.md`.

- Манифест: `INH_EXP_MANIFEST.json` (72 EXP)
- Клон: `python3 clone_inh_grid.py`
- Neuron: `NSPNeuronGenSymInhC1e9`
- SoftCold cases: `inh_{c|b}{span}_{mod}_{n0|n1}_pton` via `posttune_verify.py`

Classic: 8 Mod × {25,50,100} × {N0,N1} = 48.  
Branch: 8 Mod × {25,50,100} × N1 = 24.
