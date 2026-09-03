# Pilot v3 — итог (остановлен 2026-09-02)

Pilot v3 остановлен вручную на span100 step +5120 (~36% sim, ~13ч без улучшения dend0).

## Gate: 0/3 Done

| EXP | L | L_effective | Blocker | Следующий шаг |
|-----|---|-------------|---------|---------------|
| span25 gen | 6 5 4 1 | 6 5 4 1 | LENGTH_STALL* | `finish_pilot_lref.sh` |
| span25 preinh | 6 5 4 1 | 6 5 4 1 | LENGTH_STALL* | `finish_pilot_lref.sh` |
| span100 preinh | 9 17 12 1 | 20 17 11 1 | LENGTH_UNDER | **вне pilot** — отдельный протокол |

\* traces устарели (gen: stat при L=3 dend2; preinh: dt=1.501 sentinel после disk full).

## Ключевые выводы

1. **L=`6 5 4 1` — правильная cable-цель** для span25 (LtzCal Done). Formula `6 5 3 1` off-by-one на dend2: измеренный d2 2.7 ms (L=3) vs 0.25 ms (L=4).
2. **L-guard работал** — rollback 6 5 3 1 → 6 5 4 1.
3. **span100 dend0** — L=9 при need L=20, gap **14× tol**, plateau; step +5120 бессмысленен (~50ч wall).
4. **Параллельный pilot** — span25 ждали span100; после length subprocess span25 не получили L-ref refresh (старый процесс).

## Изменения в скриптах (2026-09-02)

| Компонент | Изменение |
|-----------|-----------|
| `effective_l_target` | Цель = L_reference, не formula |
| `length_step_guard.py` | skip/abort: plateau, hopeless UNDER, max step |
| `run_asymrm.sh` | guard перед каждым length step; span100 default без 5120 |
| `LENGTH_MAX_STEP` | default **2560** (5120 только явно) |
| `finish_pilot_lref.sh` | span25 only: refresh 320 + amp |

### Правила guard

- `skip_step`: step > LENGTH_MAX_STEP, или hopeless UNDER + step ≥1280, или plateau + step ≥2560
- `abort_length`: at L_reference → refresh + amp; hopeless UNDER + plateau

## План дальше

### Фаза A — span25 (сейчас)

```bash
bash scripts/finish_pilot_amp.sh   # лог: finish_pilot_amp.log (AMP_ONLY)
bash scripts/pilot_status.sh
```

Запущено 2026-09-02: amp phase (320→640→1280) с `AMP_PARTIAL_AT_L_REF` + `AMP_FORCE_AT_L_REF`, L-floor перед каждым шагом.

### Фаза B — span100 (отложено)

- dend0 LENGTH_UNDER: нужен другой budget/протокол (warm-start L, extended steps с guard, не blind +5120)
- В pilot v3 **исключён** до отдельного sweep

### Фаза C — масштабирование

При gate ≥2/3: `bash scripts/scale_asymrm.sh`

При fail span25 после finish: `sweep_asymrm_amp.sh` (margin/gain)

## Мониторинг

```bash
tail -f finish_pilot_lref.log
bash scripts/pilot_status.sh
python3 scripts/length_step_guard.py EXP_.../Train --next-step 5120 --cumulative 5040 --json
```

См. [`SYNC_TOL_REPORT.md`](SYNC_TOL_REPORT.md), [`AMP_REPORT.md`](AMP_REPORT.md).

---

# Pilot v4 — инфраструктура и прогон (2026-09-02)

## Выполнено

| Фаза | Артефакт |
|------|----------|
| 0a | `statisticlog_manifest.json`, `inventory_statisticlog.sh` |
| 0b | `prune_statisticlog.sh` — ~38 GB удалено, protected preinh/span100 сохранены |
| 1 | `analyze_signal_fidelity.py`, `signal_reference_span25.json`, `SIGNAL_FIDELITY_REPORT.md` |
| 2 | `train_time_budget.py`, `check_timing_feasibility` + pattern_span |
| 3.1 | `audit_l_oscillation.py`, `L_OSCILLATION_AUDIT.md` |
| 3.2 | C++ fix: `peak_synced hold` + length settle skip в `NNeuronTimeLearner.cpp` |
| 4a | `PREINH_INTEGRITY_REPORT.md` — verdict **CORRUPT** → cold reset |

## Активные прогоны

```bash
tail -f pilot_v4_gen.log      # span25 gen
tail -f pilot_span100.log     # span100 (отдельный pilot)
```

После gen Done:
```bash
bash scripts/run_pilot_v4_preinh.sh
bash scripts/run_pilot_span50.sh
bash scripts/run_gate_scale.sh
```

## C++ fix (универсальный)

- Нет hardcode L в learner
- При `peak_valid` и `|needed−delay_meas| ≤ SyncTolerance` — не менять L
- Контрольные `6 5 4 1` только в `l_reference.json` / verify scripts

