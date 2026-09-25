# Реестр успешных экспериментов StructTrain

**Срез HEAD 2026-09-25:** Console SHA-256 `5e7829bf9beb1901336ed15b7595786d5708c40d0dd9c9f2f1329bff3c3a1b63` · PulseLib `8d429e7` · Bin `0600e38`.

Только строки со статусом HEAD **PASS** (алгоритм + параметры + протокол на текущем runtime).  
Полный реестр (PASS + FAIL + NOT_RETESTED) → [`EXPERIMENTS.md`](EXPERIMENTS.md).  
Контракт cold: [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md). Narrative: [`EXPERIMENTS_AFTER_FIXES.ru.md`](../../../Docs/Audit/TimeLearner-2026-09-24-review/EXPERIMENTS_AFTER_FIXES.ru.md).  
Уровни T1–T5 (PHASE12-era) → [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md); **здесь вердикт только HEAD PASS**.

## Антипутаница

1. Одна строка = алгоритм + отличимые параметры + **протокол**. Acc gold и soft-cold — разные строки ([`EXPERIMENTS.md`](EXPERIMENTS.md) §A).
2. PHASE12 `VALIDATED` / RELIABILITY T1 **≠** запись в этом файле.
3. `ok_audit=1` (Acc≥4) сам по себе не даёт места в SUCCESSFUL.
4. Короткое **Имя**; полный путь — в **Конфиги**. Twin LtzCal — префикс `LtzCal/…`.
5. Pack B/C MatrixClone не смешивать с cold родителя.
6. Нет хроники remediation; только текущий вердикт.

## Легенда статусов HEAD

| Статус | В этом файле |
|--------|----------------|
| **PASS** | да |
| FAIL / NOT_RETESTED | нет → [`EXPERIMENTS.md`](EXPERIMENTS.md) |

## Колонки

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|

- **Acc** — успешные пробы / 8.
- **Цель** — срабатывание на правильном примере (`да` / `нет` / `—`). При Acc&lt;8/8 колонка обязательна для чтения результата.

## Как обновлять

1. Новый прогон с PASS → добавить строку сюда и в [`EXPERIMENTS.md`](EXPERIMENTS.md).
2. Строка перестала проходить → удалить отсюда; в EXPERIMENTS поставить FAIL.
3. Cold: [`scripts/posttune_verify.py`](scripts/posttune_verify.py), clean workdir, bundle в `_repro/runs/`.

---

## A. PostTune / строгий cold (текущий HEAD)

На срезе подтверждён один PASS: контроль на frozen gold-весах Branch 25 мс (обучение не запускалось).  
Строгая cold-матрица 6 клонов: **0 PASS** — FAIL в [`EXPERIMENTS.md`](EXPERIMENTS.md) §A.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| br25_posttune | NNeuronTimeLearnerBranch | span25 TipR canon mid≈0.0718 | SkipTrainGold | 8/8 | да | selective | **PASS** | — | fires `10000000`; mid 0.0718001 cpp | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`bundle`](_repro/runs/br25_on_20260924T165949Z) |

Связанный gold-корень (те же веса): [`EXP_br_span25_packA_gen_C1e9`](SelectivityBranch/EXP_br_span25_packA_gen_C1e9) — в полном реестре как GoldTest NOT_RETESTED; SoftCold на HEAD — **FAIL** ([`EXPERIMENTS.md`](EXPERIMENTS.md) §A).

Секции B–H в SUCCESSFUL пусты: других HEAD PASS нет.

---

## Риск при NOT_RETESTED (соседние строки в полном реестре)

| Риск | Когда | Примеры |
|------|-------|---------|
| **high** | SoftCold Train+PostTune; Search/Keep | cold FAIL в EXPERIMENTS §A; br480; nextseg100 |
| **med** | GoldTest на старых весах | Asym50/100; Phase6 7/8; Branch short packA |
| **low** | MatrixClone B/C; ARTIFACT partial_FA | VALIDATED_CLONE; Phase A / PSI |

---

## Указатели

| Документ | Роль |
|----------|------|
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | полный HEAD-срез |
| [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md) | исторические cold-бейджи |
| [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) | T1–T5 |
| [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md) | контракт PostTune |
| [`LAYOUT.md`](LAYOUT.md) | раскладка каталогов |
| [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) | gate CSV |
