# StatisticLog archives

Создано 2026-09-01 при нехватке диска (100% → 70%).

## Pilot v3 (сохранены последние снимки)

| EXP | Оставленный StatisticLog |
|-----|--------------------------|
| span25 gen | `2026.08.31 20-24-39` |
| span25 preinh | `2026.08.31 21-30-39` |
| span100 preinh | `2026.09.01 01-34-18` (активный) |

Промежуточные шаги length (08-20 … 17-56) **удалены** без архива (критический 0 bytes free).

## Архивы (.tar.gz)

- `FastSpan_*` — SelectivityFastSpan StatisticLog
- `AsymRm_*` — не-pilot EXP (pack B/C, span50/100 gen, …)

Восстановление: `tar -xzf ARCHIVE.tar.gz -C path/to/Train/`

## PHASE10 S0 (актуально)

Полный pack 2026-09-14 (≥200M StatisticLog/EventsLog по всему StructTrain):  
[`../../archives/statisticlog_20260914T161650Z/`](../../archives/statisticlog_20260914T161650Z/) — MANIFEST + README. Avail `/`: 142G → 308G.
