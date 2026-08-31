# SelectivityAsymRm — REPORT

Кампания асимметричной мембраны (Inh Rm/Rsyn = 10× Exc) на short-span 100/50/25 мс.  
Каталог: `Bin/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/`.

## Протокол цели

Цель: trial0 (trained) → fire; trials 1–7 (distractors: reverse / permute / clusters / uniform) → silence. Gate: target_hit ∧ Acc≥4 ∧ ¬fire_all. Acc=1/8 + fp=7 = fire_all (порог слишком низкий или нет gap).

## Параметры packs (из AsymRmSettle)

| Pack | C | ExcRm | ExcRsyn | InhRm | InhRsyn | gen class | preinh class |
|------|---|-------|---------|-------|---------|-----------|--------------|
| A | 2.5e-11 | 1e7 | 8.6e7 | 1e8 | 8.6e8 | `NSPNeuronGenAsymRmD001C25e12` | `NSPNeuronGenPreinh2_5AsymRmD001C25e12` |
| B | 1e-11 | 1e7 | 5e7 | 1e8 | 5e8 | `NSPNeuronGenAsymRmD001C1e11` | `NSPNeuronGenPreinh2_5AsymRmD001C1e11` |
| C | 2.5e-11 | 5e6 | 8.6e7 | 5e7 | 8.6e8 | `NSPNeuronGenAsymRmD001C25e12Rm5e6` | `NSPNeuronGenPreinh2_5AsymRmD001C25e12Rm5e6` |

Общее: Dissoc=Secr=0.001, Preinh k=2.5, **GTS=10000**, FixedLTZ=0.0115 (из шаблона).  
Сетка: 3 pack × 3 span × {gen, preinh} = **18 EXP**.  
Прогон: `TRAIN_T=80`, `TEST_T=15`, `MAX_JOBS=4` (2026-08-27).

## Результаты (`grid_summary.csv`)

Все **18/18** → `mode=fire_all`, `acc=1/8`, `gate=0`, `target_hit=1`, `fires=8`.

| pack | span | kind | L (Train) | gate |
|------|------|------|-----------|------|
| A | 100/50/25 | gen+preinh | 9 1 1 1 / 6 5 1 1 | 0 |
| B | 100/50/25 | gen+preinh | до 20 17 10 1 (preinh100) | 0 |
| C | 100/50/25 | gen+preinh | 9 1 1 1 / 6 5 4 1 | 0 |

Element verify после train: Cap/ExcR/InhR(=10×)/Secr/Dissoc — OK на всех EXP.

## Сравнение с FastSpan

[`SelectivityFastSpan/REPORT.md`](../SelectivityFastSpan/REPORT.md): D002 C=2.5e-10, FixedLTZ=0.0115 → **fire_all** на valid 100/50/25.  
AsymRm (быстрее settle + Inh τ=10×) **не снял fire_all** при том же FixedLTZ — узкое место снова readout/порог, не мембранный τ.

## Вывод

1. Мембранный settle для ISI25 достигнут (AsymRmSettle Pack A/B/C).  
2. **fire_all на всех 18 EXP** при FixedLTZ=0.0115 — thr ниже и target (~0.02), и многих distractors; coincidence-gap не используется. Follow-up: AutoCalibrate LTZ (`SelectivityLtzCalibrate/AsymRmLtzCal`), не дальнейший sweep C/Rm.  
3. gen vs preinh: без разницы по gate (оба fire_all).

## Запуск

```bash
bash scripts/setup_asymrm.sh
MAX_JOBS=4 TRAIN_T=80 TEST_T=15 bash scripts/run_asymrm.sh
```

## Pilot v3 (2026-08-31, в процессе)

- **Протокол:** GTS=20000, adaptive LENGTH_STEPS=80…2560, span100 +5120, `L_REFERENCE=ltzcal`, `l_train_guard.py`
- **Диагностика:** [`SYNC_TOL_REPORT.md`](SYNC_TOL_REPORT.md), [`PILOT_REPORT.md`](PILOT_REPORT.md)
- **Лог:** `pilot_v3.log`
- **Масштабирование:** `bash scripts/scale_asymrm.sh` (gate ≥2/3 Done) — см. [`SCALE_DEFERRED.md`](SCALE_DEFERRED.md)
