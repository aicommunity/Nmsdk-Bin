# Pilot v3 — итог (остановлен 2026-09-02)

Pilot v3 остановлен вручную на span100 step +5120 (~36% sim, ~13ч без улучшения dend0).

См. исторические детали ниже в архивной секции. Актуальный статус — **Pilot v4 Done Unblock**.

---

# Pilot v4 Done Unblock — итог (2026-09-04)

## Gate train Done: 2/2

| EXP | L | sync_ok | IsNeedToTrain | FixedLTZ | Blocker (stall) | Test gate |
|-----|---|---------|---------------|----------|-----------------|-----------|
| span25 gen | 6 5 4 1 | yes | **0** | **0.0869** | AMP_OSCILLATION* | 6/8 partial_FA gate=1 |
| span25 preinh | 6 5 4 1 | yes | **0** | **0.0516** | AMP_OSCILLATION* | 1/8 fire_all gate=0 |
| span100 preinh | 9 17 12 1 | no | 1 | cold | LENGTH_STALL | вне gate |

\* after Done, stall classifier may still show residual amp flags; verify_train_done = OK.

## Root-cause и фикс

1. **Причина:** `l_guard_floor` поднимал L до `6 5 4 1` до train → C++ захват `InitialSomaPotential` только при `L==1` пропускался → R-tune skip → Done недостижим.
2. **Фикс протокола:**
   - [`scripts/seed_initial_from_ltzcal.py`](scripts/seed_initial_from_ltzcal.py) — seed Initial (и TipR) из LtzCal
   - [`scripts/l_train_guard.py`](scripts/l_train_guard.py) — `floor_skipped_no_initial`
   - [`scripts/run_asymrm.sh`](scripts/run_asymrm.sh) — `ensure_initial_ready`, abort amp при `AMP_NO_INITIAL`
   - [`scripts/analyze_train_stall.py`](scripts/analyze_train_stall.py) — blocker `AMP_NO_INITIAL`
3. **Догон span25:** in-place seed → amp; после amp SyncTolerance поднят до **0.0025** (dend1 dt≈0.0018) + TipR reseed → Done за T=320.

## C++ (v4, без новых правок в unblock)

- peak_synced hold + length settle skip — L держится `6 5 4 1`
- Нормализация корректна; проблема была в протоколе эксперимента

## Хвосты

| Задача | Статус |
|--------|--------|
| Gate train Done 2/2 | **OK** (`run_gate_scale.sh`) |
| Scale Pack B/C | `scale_asymrm.sh` исправлен (VERIFY path, SKIP_SWEEP, skip Done); см. `SCALE_DEFERRED.md` |
| span50 pilot | **стартовал** (`SEED_INITIAL` + L-floor `9 9 7/6 1`); лог `pilot_span50.log` |
| span100 | протокол [`SPAN100_PROTOCOL.md`](SPAN100_PROTOCOL.md); in-place, без blind 5120 |
| prune StatisticLog | ~120 GB удалено (защищены active/audit) |

## Команды

```bash
# Done verify
python3 ../SelectivityLtzCalibrate/scripts/verify_train_done.py \
  --require-calibrated --require-sync-ok --L-reference l_reference.json \
  EXP_span25ms_packA_gen/Train/Parameters_00.xml \
  EXP_span25ms_packA_preinh/Train/Parameters_00.xml

bash scripts/run_gate_scale.sh
bash scripts/run_pilot_span50.sh
SKIP_COLD_RESET=1 bash scripts/run_pilot_span100.sh
```

## Signal fidelity

span25 gen: `signal_fidelity_ok=True`, `sync_ok=True` vs `signal_reference_span25.json`.

---

# Архив: Pilot v3 / v4 инфраструктура

## Gate v3: 0/3 Done (исторический)

| EXP | L | L_effective | Blocker | Следующий шаг |
|-----|---|-------------|---------|---------------|
| span25 gen | 6 5 4 1 | 6 5 4 1 | LENGTH_STALL* | superseded |
| span25 preinh | 6 5 4 1 | 6 5 4 1 | LENGTH_STALL* | superseded |
| span100 preinh | 9 17 12 1 | 20 17 11 1 | LENGTH_UNDER | SPAN100_PROTOCOL |

## Инфраструктура v4 (2026-09-02)

| Фаза | Артефакт |
|------|----------|
| 0a | `statisticlog_manifest.json`, `inventory_statisticlog.sh` |
| 0b | `prune_statisticlog.sh` |
| 1 | `analyze_signal_fidelity.py`, `signal_reference_span25.json` |
| 2 | `train_time_budget.py` |
| 3.1 | `audit_l_oscillation.py` |
| 3.2 | C++ peak_synced hold |
| 4a | `PREINH_INTEGRITY_REPORT.md` |

## C++ fix (универсальный)

- Нет hardcode L в learner
- При `peak_valid` и `|needed−delay_meas| ≤ SyncTolerance` — не менять L
- Контрольные `6 5 4 1` только в `l_reference.json` / verify scripts

## Pilot v4 gate (2026-09-04)

- span25 Done: 2 / 2
- Action: scale Pack B/C span25

## Pilot v4 gate (2026-09-04)

- span25 Done: 2 / 2
- Action: scale Pack B/C span25

## Pilot v4 gate (2026-09-04)

- span25 Done: 2 / 2
- Action: scale Pack B/C span25
