# PHASE12 — предложения по quality-бэклогу (после Wave6)

**Дата:** 2026-09-19 · PulseLib pin **`780ffc7`** (без изменений) · SoT: [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md)  
**EN:** [`QUALITY_BACKLOG_PROPOSALS.md`](QUALITY_BACKLOG_PROPOSALS.md)

Wave6 исчерпал soft/strip/overlay-инвесты по хвостам `ARTIFACT_KEEP` / `FAIL_ROOTCAUSE` после §8 Wave5. Ниже — **конкретные предложения** (конфиг / скрипты / **C++**) и **анализ рисков** относительно уже VALIDATED gold (Branch W1–W2, AsymRm25, LtzCal25).

**Нельзя:** marathon br480/nextseg; overwrite VALIDATED gold; менять глобальный `kAmpNormEps` / TipR path без регресса.

---

## Чеклист покрытия (31 ID)

| Вердикт | Кол-во | Примечание |
|---------|--------|------------|
| `CLOSED_VALIDATED` | 0 в W6 | Новых VALIDATED* в этой волне нет |
| `EXHAUSTED_KEEP` | 31 | Весь quality-бэклог ниже |

---

## A. FastSpan — Need застрял (FS25 + siblings×4)

### ID
- `SelectivityFastSpan/EXP_span25ms_fast_C1e9` — **FAIL_ROOTCAUSE**
- `EXP_span25ms_fast_preinh_C1e9`, `EXP_span50ms_fast_preinh_C1e9`, `EXP_span100ms_fast_C1e9`, `EXP_span100ms_fast_preinh_C1e9` — **ARTIFACT_KEEP** (parent)

### Факты Wave6
- Разбор кода: `_repro/_invest/fs25_unblock/NEED_TRACE_W6.ru.md`
- W3a: soft-cold L≡gold `6 5 4 1`, Need=1 @180×3
- **Pin PulseLib не меняли** (blast-radius; полный регресс Branch25+AsymRm25 не гоняли)

### Гипотеза
`EndOfLearning` блокируется `AllSynapsesNormalized()` (amp stall, `kAmpNormEps=1e-5`) и/или L-policy dend0 `peak_synced`, при уже совпавшем L с gold.

### Предложения
1. **Конфиг:** soft-cold с `EnableDebug=1` на FS25 Train; дампы ampDt/synced в `_repro/_invest/fs25_unblock/`.
2. **Скрипты:** `run-fs` после pin bump; авто-регресс Branch25+AsymRm25.
3. **C++** (`NNeuronTimeLearner.cpp`):
   - **A1 (P0):** в `EndOfLearning` (~3471) при EnableDebug — лог synced/normalized, |Initial−MaxAmp|, ResistanceStatus.
   - **A2 (P0):** plateau Need-clear при synced + L неизменен M эпох + max|ampDt|<2e-5 — **только** с FS/EstDelay/class guard (не глобально).
   - **A3 (P1):** не поднимать глобальный `kAmpNormEps` без регресса thr AsymRm25.
   - **A4 (P2):** hold-L dend0 в `ChangeDendriteStatus` (~3121) только если логи покажут 7↔6.

### Риски vs VALIDATED*

| Изменение | Задевает | Детект | Митигация |
|-----------|----------|--------|-----------|
| Глобальный Need clear / eps | AsymRm25, Phase6 TL | soft-cold AsymRm25 acc/thr | FS-only guard |
| L-policy dend0 | AsymRm25 L | сравнение L с gold | `num==0 && EstDelay` |
| Branch.cpp | Branch W1–W2 EXACT | stamp Branch25 | **не патчить Branch** ради FS |

**Приоритет:** P0 · Оценка: PulseLib+регресс (~½–1 день)

---

## B. AsymRm span50/100 midflat + clones + LtzCal50/100

### ID
- AsymRm packA 50/100 ×4 — **ARTIFACT_KEEP**
- AsymRm B/C ×8 — **ARTIFACT_KEEP** (parent)
- LtzCal 50/100 ×4 — **ARTIFACT_KEEP** (parent)

### Факты Wave6
- Soft Need=0 L≡gold; ltz≈0.0379 flat
- **W6.3 overlay** tiprmin на soft-веса (без retrain): снова flat — `_repro/_invest/asym_midflat/ROOTCAUSE.ru.md`
- `soma_amp_sum`=0 на gold и soft

### Гипотеза
Soft-cold даёт неверную amp/weight-иерархию при span≥50; одного TipR недостаточно. Span25 TipR86e6 — VALIDATED (span-зависимо).

### Предложения
1. **Конфиг:** diff gold vs soft InitSoma / tip Exc / Pattern / MatrixData; warm TipR schedule **во время** train.
2. **Скрипты:** опциональный InitSoma overlay с gold перед phase9 (QUALITY path).
3. **C++:**
   - **B1 (P1):** TipR path (~686+) — не сглаживать LTZ peaks на длинных span; лог ampDt.
   - **B2 (P1):** после Done — опциональный re-init tip Exc с gold под флагом.
   - **B3 (P2):** не переключать gate на `soma_amp_sum` (здесь всегда 0).

### Риски vs VALIDATED*

| Изменение | Задевает | Детект | Митигация |
|-----------|----------|--------|-----------|
| TipR ampDt | AsymRm25 TipR86e6 mid | phase9 acc=8 | только span≥50 / флаг |
| InitSoma overlay | AsymRm25 EXACT thr | thr drift | только QUALITY allowlist |

**Приоритет:** P1 · Оценка: протокол 1 день; C+++регресс 1–2 дня

---

## C. Phase6 @480 — L не растёт (soft+strip)

### ID
`SelectivityPhaseA/Phase6/EXP_480_*` ×4 — **ARTIFACT_KEEP**

### Факты Wave6
- AutoCal=0, Reset=1
- Soft+strip `-t`120, wall≤320s: L=`1 1 1 1` Need=1 — `_repro/_invest/phase6_w6/COMPARE.md`
- Совпадает с W5.1

### Гипотеза
Classic TL не входит в рост L на 480 мс паттерне при soft/strip cold (dataset/Reset/GTS), не TipR.

### Предложения
1. **Конфиг:** сравнить Pattern/GTS/CalculateMode с gold; diagnostic warm-start (не promote).
2. **Скрипты:** дамп `DetectNewImpulse` в debug.
3. **C++:** те же EnableDebug-логи (A1); лог при нуле импульсов и Need=1 (скорее конфиг).

**Приоритет:** P1 · Сначала forensics конфига

---

## D. Branch nextseg100 packA+B/C

### ID
- `EXP_br_span100_packA_nextseginh_C1e9` — **ARTIFACT_KEEP**
- packB/C — **ARTIFACT_KEEP** (parent)

### Факты Wave6
- Soft+strip `-t`200: L=`1 1 1 1` — `_repro/_invest/nextseg100/COMPARE.md`
- `EnableNextSegmentInhibition=1`

### Гипотеза
NextSegInh @span100 блокирует рост L при cold (nextseg25/50 VALIDATED). Возможно Branch-specific.

### Предложения
1. **Конфиг:** один controlled soft `-t`640 + extend; сравнить Matrix с nextseg50; diagnostic NextSeg=0 (не promote).
2. **Скрипты:** assert EnableNextSegmentInhibition в prepare.
3. **C++** (`NNeuronTimeLearnerBranch.cpp`) — только после исчерпания конфига:
   - **D1 (P1):** лог NextSeg ↔ ChangeDendriteStatus
   - **D2 (P2):** scoped exception span≥100 — высокий риск для Branch VALIDATED

**Приоритет:** P1 конфиг / P2 C++

---

## E. Branch br480 ×3

### ID
`EXP_br480_{tiprmin,nextseginh_tiprmin,preinh250_tiprmin}` — **ARTIFACT_KEEP**

### Факты Wave6
- Soft+strip tiprmin `-t`180: L stuck — `_repro/_invest/br480_w6/COMPARE.md`
- W2: Need≠0 @4×600; gold 7/8 сохранён

### Гипотеза
Как Phase6/nextseg: cold L не уходит с `1 1 1 1` на Branch@480 (короткий Branch VALIDATED).

### Предложения
1. **Конфиг:** done_tipr + phase8 mid stamp с gold (документационный QUALITY path, не ложный VALIDATED cold).
2. **Скрипты:** запрет 4×600 в CLI.
3. **C++ Branch:** те же D1-логи; масштабирование Epoch/GTS — только с регрессом Branch25.

**Приоритет:** P2

---

## Сквозные рекомендации (Wave7)

| P | Что | Зачем |
|---|-----|-------|
| P0 | FS25 EnableDebug + FS-only Need plateau clear | Разблокирует FS; AsymRm25/LtzCal25 уже VAL |
| P1 | AsymRm50 midflat InitSoma/TipR train-schedule | Overlay доказал: post-hoc TipR недостаточен |
| P1 | Phase6 / nextseg / br480 — forensics импульсов/NextSeg | L не растёт — до amp-политики |
| P2 | Branch.cpp NextSeg@100 / br480 | Высокий blast-radius на W1–W2 EXACT |

### Обязательный регресс перед любым bump pin PulseLib
1. `EXP_br_span25_packA_gen_C1e9` — EXACT/QUALITY  
2. `SelectivityAsymRm/EXP_span25ms_packA_gen` — phase9 acc≥7  
3. Целевой EXP — Need=0 + gate acc≥7  

---

## Указатели на историю
- W1–W6: [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md)  
- FS: `_repro/_invest/fs25_unblock/`  
- AsymRm: `_repro/_invest/asym_midflat/`  
- Phase6 / nextseg / br480: `_repro/_invest/phase6_w6/`, `nextseg100/`, `br480_w6/`
