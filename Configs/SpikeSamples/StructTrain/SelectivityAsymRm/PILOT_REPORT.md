# Pilot retrain v2 — Pack A (3 EXP)

Протокол: GTS=20000, 3-phase adaptive (`LENGTH_STEPS=80 160 320 640 1280`, cumulative T=2480), amp-continue не запускался (нет `all_sync_ok`).

## Результаты train

| EXP | L (после) | L_formula | NeedTrain | FixedLTZ | blocker | sync_all |
|-----|-----------|-----------|-----------|----------|---------|----------|
| span25 gen | **6 5 3 1** | 6 5 3 1 | 1 | 0.0115 | LENGTH_STALL | no |
| span25 preinh | 6 5 4 1 | 6 5 3 1 | 1 | 0.0115 | LENGTH_STALL | no |
| span100 preinh | 9 17 12 1 | 20 17 11 1 | 1 | 0.0115 | LENGTH_STALL | no |

**Прогресс vs v1:** span25 gen — dend2 **4→3** (совпал с L_formula); узкое место сместилось на dend2.

**Итог:** **0/3 Done** (gate fail-hard). Sync/test не запускались. Amp-phase пропущена: `skip amp-continue` (нет `all_non_ref_sync_ok`).

## Порог синхронизации (`tol`)

`tol` = **`SyncTolerance`** в `Parameters_00.xml` (learner: `DendLastAbsDt ≤ SyncTolerance` → `sync_ok`).

| span | SyncTolerance (`tol`) | DelayAgreeMarginMin | PeakMeasureMargin | формула |
|------|----------------------|---------------------|-------------------|---------|
| 25 ms | **0.00104167 s** (≈1.04 ms) | 0.002 s | 0.002 s | `max(0.5ms, 0.02·α)`, α=span/480 |
| 50 ms | 0.002083 s (≈2.08 ms) | — | — | то же |
| 100 ms | **0.004167 s** (≈4.17 ms) | — | — | то же |

Эталон LtzCal Done (span25 gen) использует **тот же** `SyncTolerance=0.00104167` и достигает `sync_ok` на всех non-ref при L=`6 5 4 1`. Значит порог **не завышен абсолютно** — при тех же tol Done достижим. Отказ пилота v2 — **рассогласование пика/кабеля** (`last_abs_dt`), не обязательно «слишком жёсткий tol».

## Per-dendrite last_abs_dt (span25 gen, pilot v2)

`tol = 0.00104167 s`. `sync_ok ⇔ last_abs_dt ≤ tol`.

| dend | L | last_abs_dt | dt / tol | sync_ok |
|:----:|:-:|:-----------:|:--------:|:-------:|
| 0 | 6 | 0.00020 s | 0.19× | yes |
| 1 | 5 | 0.00103 s | **0.99×** | yes (на грани) |
| 2 | 3 | **0.00270 s** | **2.59×** | **no** ← блокирует `all_sync_ok` |

После уменьшения L dend2 (4→3) `last_abs_dt` на dend2 **вырос** (было ~0.00025 при L=4 в v1). Гипотеза: L=3 по формуле не согласован с измеренным пиком; LtzCal Done держал L=4 при том же tol.

## span100 preinh (кратко)

`tol = 0.004167 s`. Блокер: dend0 `last_abs_dt=0.0612 s` (**15× tol**), не «пограничный» случай.

## Вывод

Масштабирование Pack A / 18 EXP **не запускалось** (нужно ≥2/3 pilot Done). Следующий шаг: `sweep_asymrm_amp.sh` (PeakMargin / Gain) или B.7 margin на dend1 PEAK_MISALIGNED.

См. также: [`AMP_REPORT.md`](AMP_REPORT.md), [`PEAK_SYNC_REPORT.md`](PEAK_SYNC_REPORT.md), [`CPP_FALLBACK.md`](CPP_FALLBACK.md).
