#!/usr/bin/env python3
"""Turn per-case C++ trainer results into versioned, readable matrix reports."""
from __future__ import annotations
import argparse
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from matrix_run_safety import atomic_write_json, exclusive_file_lock, sha256_file
from timelearner_matrix import case_attempt_result

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2].parent
MATRIX = BASE / "TimeLearnerMatrix"
EXPERIMENTS = BASE / "EXPERIMENTS.md"
SUCCESSFUL = BASE / "SUCCESSFUL_EXPERIMENTS.md"
ROOT_REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "evidence" / "metrics" / "TIMELEARNER_MATRIX_WAVES_20261010.md"
WAVE_PLAN = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "plans" / "TimeLearner-full-matrix-waves-20261010.ru.md"
FULL_MATRIX_REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "TIMELEARNER_FULL_MATRIX_AND_HISTORY_2026-10-10.ru.md"
RUNS_BASE = BASE / "_repro" / "TimeLearnerMatrixRuns"
RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
BEGIN = "<!-- GENERATED_WAVE_RESULTS_BEGIN -->"
END = "<!-- GENERATED_WAVE_RESULTS_END -->"


def run_root() -> Path:
    run_id = os.environ.get("TIMELEARNER_MATRIX_RUN_ID", "").strip()
    if not RUN_ID_RE.fullmatch(run_id):
        raise RuntimeError("TIMELEARNER_MATRIX_RUN_ID must name the run whose wave is being reported")
    return RUNS_BASE / run_id


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def append_wave_snapshot(wave_dir: Path, snapshot: dict[str, Any]) -> Path:
    """Persist one immutable run snapshot and atomically advance the compatibility index."""
    snapshots_dir = wave_dir / "run_results"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(snapshot["run_id"])
    snapshot_name = (
        f"{run_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid.uuid4().hex[:8]}.json"
    )
    target = snapshots_dir / snapshot_name
    index_path = wave_dir / "results.json"
    with exclusive_file_lock(
        wave_dir / ".results-index.lock",
        purpose=f"update {wave_dir.name} results index",
        wait_timeout_s=60.0,
    ):
        previous = load_json(index_path) or {}
        history = list(previous.get("runs", []))
        existing = []
        for candidate in sorted(snapshots_dir.glob("*.json")):
            data = load_json(candidate)
            if isinstance(data, dict) and str(data.get("run_id")) == run_id:
                existing.append((candidate, data))
        if existing:
            immutable_view = {key: value for key, value in snapshot.items() if key != "updated_utc"}
            for candidate, old in existing:
                old_view = {key: value for key, value in old.items() if key != "updated_utc"}
                if old_view == immutable_view:
                    target = candidate
                    break
            else:
                raise RuntimeError(
                    f"RUN_ID {run_id} already has an immutable result snapshot with different contents"
                )
        else:
            atomic_write_json(target, snapshot, replace=False)
        entry = {
            "run_id": run_id,
            "run_fingerprint": snapshot.get("run_fingerprint"),
            "snapshot": str(target.relative_to(wave_dir)).replace(os.sep, "/"),
            "run_complete": bool(snapshot.get("run_complete")),
            "updated_utc": snapshot.get("updated_utc"),
        }
        if not any(
            item.get("run_id") == run_id and item.get("snapshot") == entry["snapshot"]
            for item in history
        ):
            history.append(entry)
        atomic_write_json(index_path, {**snapshot, "runs": history})
    return target


def md(value: Any) -> str:
    if value is None or str(value) == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def result_rows() -> list[dict[str, Any]]:
    rows = []
    for wave_file in sorted(MATRIX.glob("W*/results.json")):
        wave = wave_file.parent.name
        seen: set[tuple[str, str]] = set()
        snapshots = sorted((wave_file.parent / "run_results").glob("*.json"))
        for snapshot_file in snapshots:
            data = load_json(snapshot_file)
            if not isinstance(data, dict):
                continue
            run_id = str(data.get("run_id") or snapshot_file.stem)
            seen.add((wave, run_id))
            for case in data.get("cases", []):
                rows.append({"wave": data.get("wave", wave), "run_id": run_id, **case})
        # Keep legacy committed results visible, unless that exact RUN_ID has an
        # immutable snapshot already. The canonical file remains a latest-view
        # compatibility layer for older scripts and users.
        data = load_json(wave_file)
        if isinstance(data, dict):
            run_id = str(data.get("run_id") or "legacy")
            if (wave, run_id) not in seen:
                for case in data.get("cases", []):
                    rows.append({"wave": data.get("wave", wave), "run_id": run_id, **case})
    return rows


def collect_wave(wave: str) -> tuple[dict[str, Any], Path]:
    registry = json.loads((MATRIX / "matrix.json").read_text(encoding="utf-8"))
    specs = [c for c in registry["cases"] if c["wave"] == wave]
    if not specs:
        raise ValueError(f"wave not in matrix registry: {wave}")
    runs = run_root()
    run_manifest_path = runs / "run_manifest.json"
    run_manifest = load_json(run_manifest_path)
    if not isinstance(run_manifest, dict):
        raise RuntimeError(f"run manifest missing/invalid: {run_manifest_path}")
    if run_manifest.get("wave") != wave:
        raise RuntimeError(f"run manifest wave mismatch: expected {wave}")
    status = load_json(runs / wave / "wave_status.json") or {}
    cases = []
    selected_cases = set(run_manifest.get("selected_cases", run_manifest.get("case_ids", [])))
    wave_case_ids = {spec["id"] for spec in specs}
    for spec in specs:
        case_id = spec["id"]
        row = None
        attempt_dir = None
        if case_id in selected_cases:
            input_manifest = MATRIX / wave / "inputs" / case_id / "matrix_input_manifest.json"
            if not input_manifest.is_file():
                raise FileNotFoundError(f"input manifest missing: {input_manifest}")
            saved = case_attempt_result(
                runs / wave / case_id,
                case_id=case_id,
                run_manifest=run_manifest,
                input_manifest_sha256=sha256_file(input_manifest),
            )
            if saved:
                attempt_dir, row = saved
        cases.append({
            "case": case_id,
            "factors": spec,
            "result": row,
            "attempt_id": attempt_dir.name if attempt_dir else None,
            "infrastructure_status": (
                status.get("cases", {}).get(case_id, {}).get("status", "missing")
                if case_id in selected_cases else "not_selected"
            ),
        })
    snapshot = {
        "wave": wave,
        "run_id": os.environ.get("TIMELEARNER_MATRIX_RUN_ID"),
        "run_fingerprint": run_manifest.get("run_fingerprint"),
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "jobs": status.get("jobs", 8),
        "started_utc": status.get("started_utc"),
        "finished_utc": status.get("finished_utc"),
        "run_complete": bool(status.get("run_complete")) and selected_cases == wave_case_ids,
        "cases": cases,
    }
    target = append_wave_snapshot(MATRIX / wave, snapshot)
    return snapshot, target


def separation_quality(row: dict[str, Any]) -> str:
    quality = row.get("separation_quality")
    if quality is None:
        metrics = str(row.get("metrics") or "")
        if row.get("quality_gate_ok") is True or "ok_audit=1" in metrics or "ok_strict=1" in metrics:
            quality = "pass"
        elif row.get("quality_gate_ok") is False or "ok_audit=0" in metrics or "ok_strict=0" in metrics:
            quality = "fail"
        elif (legacy_ok := re.search(r"(?:^|\s)ok=(\d+)", metrics)):
            quality = "legacy_gate_pass_strict_unavailable" if legacy_ok.group(1) == "1" else "legacy_gate_fail"
        elif row.get("expect_fires") and row.get("fires"):
            quality = "legacy_pattern_mismatch" if row["fires"] != row["expect_fires"] else "legacy_pattern_match_strict_unavailable"
        else:
            quality = "not_reached_or_unknown"
    return str(quality)


def target_detection(row: dict[str, Any]) -> str:
    detection = row.get("detection_quality")
    if detection in ("detected", "target_detected"):
        return "detected"
    if detection in ("target_not_detected", "not_detected"):
        return "target_not_detected"
    if detection in ("pass", "fail", "ok", "unknown", None):
        metrics = str(row.get("metrics") or "")
        hit = re.search(r"(?:target_hit_strict|target_hit)=(\d+)", metrics)
        if row.get("target_detected") is True:
            detection = "detected"
        elif row.get("target_detected") is False:
            detection = "target_not_detected"
        elif hit:
            detection = "detected" if hit.group(1) == "1" else "target_not_detected"
        elif row.get("fires") and row.get("fires") != "—":
            detection = "detected" if str(row["fires"]).startswith("1") else "target_not_detected"
        else:
            detection = "not_evaluated_training_incomplete"
    return str(detection)


def accuracy_summary(row: dict[str, Any]) -> str:
    metrics = str(row.get("metrics") or "")
    structured = row.get("quality_metrics") if isinstance(row.get("quality_metrics"), dict) else {}
    accuracy = structured.get("acc_strict")
    denominator = structured.get("n")
    label = "strict"
    if accuracy is None:
        acc_match = re.search(r"(?:^|\s)acc=(\d+)(?:/(\d+))?", metrics)
        n_match = re.search(r"(?:^|\s)n=(\d+)", metrics)
        if acc_match:
            accuracy = acc_match.group(1)
            denominator = acc_match.group(2) or (n_match.group(1) if n_match else None)
            label = "legacy"
    if accuracy is None:
        return "—"
    result = f"{accuracy}/{denominator}" if denominator else str(accuracy)
    fp = structured.get("late_fp_strict")
    if fp is None:
        fp_match = re.search(r"(?:^|\s)fa=(\d+)", metrics)
        fp = fp_match.group(1) if fp_match else None
    suffix = f"; FP={fp}" if fp is not None else ""
    audit = "" if label == "strict" else "; strict audit not saved"
    return f"{result} {label}{suffix}{audit}"


def provenance_summary(row: dict[str, Any]) -> str:
    provenance = row.get("run_provenance")
    if not isinstance(provenance, dict):
        return "runtime provenance missing"
    gitlinks = provenance.get("gitlinks") or {}
    return "; ".join([
        f"root={str(provenance.get('root_git') or '—')[:12]}",
        f"Bin={str(gitlinks.get('Bin') or '—')[:12]}",
        f"PulseLib={str(gitlinks.get('Libraries/Nmsdk-PulseLib') or '—')[:12]}",
        f"Console={str(provenance.get('binary_sha256') or '—')[:12]}",
    ])


def human_pattern_label(spec: dict[str, Any]) -> str:
    family = str(spec.get("pattern_family") or "")
    labels = {
        "AsymRm pack A": "базовый набор Pack A с асимметричными сопротивлениями мембран",
        "AsymRm Pack A": "набор Pack A с асимметричными сопротивлениями мембран",
        "Branch pack A": "набор Pack A на разных сегментах одного дендрита",
        "FastSpan": "сжатая по времени последовательность импульсов",
        "LTZ-calibrated Pack A": "набор Pack A с калибровкой порога локальной временной зоны",
        "PhaseA/Phase6": "полный паттерн 480 мс с исторической настройкой порога локальной временной интеграции",
        "Phase6 canonical": "полный паттерн 480 мс из базовой конфигурации Phase6",
        "PSI historical sweep": "исторические паттерны разной длительности для перебора силы пресинаптического торможения",
        "D long-pattern diagnostic": "длинный паттерн 480 мс для проверки мембранной RC-постоянной, задержки на сегмент и предела длины",
        "FastResponse D×C": "полный паттерн 480 мс и историческая комбинация постоянной диссоциации с ёмкостью мембраны",
        "FastResponse D×C + manual TipR@Rmin": "полный паттерн 480 мс, историческая комбинация D×C и ручное снижение сопротивления концевых синапсов до Rmin",
    }
    if family in labels:
        return labels[family]
    if family == "Pack B":
        return "исторический набор импульсов Pack B"
    if family == "Pack C":
        return "исторический набор импульсов Pack C"
    if family.startswith("AsymRm Pack "):
        pack = family.removeprefix("AsymRm Pack ")
        return f"набор Pack {pack} с асимметричными сопротивлениями мембран"
    if family.startswith("Branch"):
        return "импульсы последовательности на разных сегментах одного дендрита"
    return family or "исторический набор импульсов; см. сохранённые XML"


def human_case_description(spec: dict[str, Any]) -> str:
    existing = str(spec.get("description_ru") or "")
    if existing and not existing.startswith("Точная повторная проверка исторического случая"):
        return existing
    if not existing:
        detail = human_pattern_label(spec)
        return f"Базовая проверка: {detail}; сопоставленные PSI off/on варианты отличаются только явно указанным режимом и торможением."
    duration = spec.get("duration_ms")
    mode = "структурный" if spec.get("normalization_mode") == 0 else "структурно-параметрический"
    psi = "включено" if spec.get("presynaptic_inhibition") else "выключено"
    coeff = spec.get("presynaptic_coefficient")
    if spec.get("presynaptic_inhibition") and coeff is not None:
        psi += f" (коэффициент {coeff:g})"
    nextseg = "включено" if spec.get("branch_nextseg") else "выключено"
    post = "включена" if spec.get("posttrain_tuning") else "выключена"
    tip_modes = {0: "off", 1: "CanonRmin", 2: "FlatLastR", 3: "KeepDone", 4: "SearchSynthetic"}
    tip = tip_modes.get(spec.get("tipr_mode"), "как в исходном XML")
    return (
        f"Повтор сохранённой Train/Test-конфигурации: {human_pattern_label(spec)}, {duration} мс; "
        f"режим обучения — {mode}; пресинаптическое торможение {psi}; Branch NextSeg {nextseg}; "
        f"PostTrain {post}, режим TipR {tip}."
    )


def category(row: dict[str, Any]) -> str:
    if not row:
        return "результат не сохранён"
    conv = str(row.get("training_convergence") or "не определена")
    quality = separation_quality(row)
    detection = target_detection(row)
    if conv.startswith("converged") or conv == "training_converged":
        return f"обучение сошлось; качество={quality}; цель={detection}"
    if conv in ("not_started", "not_run"):
        return "обучение не запускалось"
    if conv in ("not_converged_at_stop", "cpp_training_refusal"):
        return "обучение не сошлось"
    if "incomplete" in conv or "fail" in conv:
        return "обучение не сошлось"
    return f"{conv}; quality={quality}; detection={detection}"


def replace_block(path: Path, content: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    block = BEGIN + "\n" + content.rstrip() + "\n" + END
    if pattern.search(text):
        text = pattern.sub(lambda _: block, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def update_documents() -> None:
    registry = load_json(MATRIX / "matrix.json") or {}
    readiness = load_json(MATRIX / "readiness.json") or {}
    history = load_json(MATRIX / "legacy_history_inventory.json") or {}
    rows = result_rows()
    results_by_case = {item.get("case"): item.get("result") or {} for item in rows}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in rows:
        grouped.setdefault(item["wave"], []).append(item)
    result_sections = []
    for wave in registry.get("queue_order", sorted(grouped)):
        if wave not in grouped:
            continue
        group = grouped[wave]
        table = [
            f"### {wave}",
            "",
            "| Случай | RUN_ID | Сходимость C++ | Качество разделения | Детекция цели | Acc / FP | Need | Fires | Категория | Provenance (SHA, начало) |",
            "|---|---|---|---|---|---:|---|---|---|---|",
        ]
        for item in group:
            result = item.get("result") or {}
            after = result.get("after") or {}
            table.append("| " + " | ".join([
                md(item["case"]),
                md(item.get("run_id")),
                md(result.get("training_convergence", item.get("infrastructure_status"))),
                md(separation_quality(result)),
                md(target_detection(result)),
                md(accuracy_summary(result)),
                md(after.get("IsNeedToTrain")),
                md(result.get("fires")),
                md(category(result)),
                md(provenance_summary(result)),
            ]) + " |")
        result_sections.extend(table + [""])

    cases = registry.get("cases", [])
    wave_cases: dict[str, list[dict[str, Any]]] = {}
    for spec in cases:
        wave_cases.setdefault(spec["wave"], []).append(spec)
    matrix_lines = []
    for wave in registry.get("queue_order", []):
        specs = wave_cases.get(wave, [])
        if not specs:
            continue
        title = (registry.get("wave_descriptions", {}).get(wave) or {}).get("title", "")
        matrix_lines.extend([
            f"### {wave}: {md(title)}",
            "",
            "| ID | Что именно проверяется | Тренер / длительность / режим | Пресинаптическое торможение / NextSeg | Train / Test |",
            "|---|---|---|---|---|",
        ])
        for spec in specs:
            trainer = spec.get("trainer")
            trainer_name = "Classic (`NNeuronTimeLearner`)" if trainer == "NNeuronTimeLearner" else "Branch (`NNeuronTimeLearnerBranch`)"
            mode = "структурный (NormalizationMode=0)" if spec.get("normalization_mode") == 0 else "структурно-параметрический (NormalizationMode=1)"
            duration = f"{spec.get('duration_ms')} мс"
            psi = "включено" if spec.get("presynaptic_inhibition") else "выключено"
            coefficient = spec.get("presynaptic_coefficient")
            if spec.get("presynaptic_inhibition") and coefficient is not None:
                psi += f", k={coefficient:g}"
            nextseg = "включено" if spec.get("branch_nextseg") else "выключено"
            input_root = f"TimeLearnerMatrix/{wave}/inputs/{spec['id']}"
            train = f"[{spec['id']} Train]({input_root}/Train/Project.ini)"
            test = f"[{spec['id']} Test]({input_root}/Test/Project.ini)"
            matrix_lines.append("| " + " | ".join([
                md(spec["id"]),
                md(human_case_description(spec)),
                f"{md(trainer_name)}; {md(duration)}; {md(mode)}",
                f"PSI {md(psi)}; Branch NextSeg {md(nextseg)}",
                f"{train} / {test}",
            ]) + " |")
        matrix_lines.append("")

    total_cases = len(cases)
    wave_count = len(registry.get("queue_order", []))
    max_wave = max((len(v) for v in wave_cases.values()), default=0)
    convergence_counts: dict[str, int] = {}
    for item in rows:
        result = item.get("result") or {}
        state = str(result.get("training_convergence") or "не определено")
        convergence_counts[state] = convergence_counts.get(state, 0) + 1
    successful_count = sum(
        1 for item in rows
        if (result := (item.get("result") or {}))
        and str(result.get("training_convergence", "")).startswith("converged")
        and separation_quality(result) == "pass"
        and target_detection(result) == "detected"
    )
    history_counts: dict[str, int] = {}
    for row in history.get("records", []):
        key = row.get("mapping_quality", "unknown")
        history_counts[key] = history_counts.get(key, 0) + 1
    full49 = load_json(MATRIX / "historical_coverage.json") or {}

    intro = [
        "# StructTrain: матрица экспериментов TimeLearner",
        "",
        "## Что проверяется",
        "",
        f"Реестр содержит **{total_cases} отдельных обучающих опытов** в **{wave_count} волнах**; самая большая волна — {max_wave} опытов. Каждая строка — одно обучение одной конфигурации. Восемь проб внутри Test — измерения качества одной модели, а не восемь отдельных обучающих опытов. Очередь запускается только на сервере `.17`, максимум восемь процессов NeuroModelerConsole. Полные 312 запусков в рамках подготовки матрицы не выполнялись.",
        "",
        "Проверяются два C++-тренера: Classic (`NNeuronTimeLearner`) распределяет импульсы входного паттерна по нескольким дендритам; Branch (`NNeuronTimeLearnerBranch`) размещает импульсы на разных сегментах одного дендрита. Оба обучают длину дендритов. `NormalizationMode=0` меняет структуру синапсов для нормализации амплитуды; `NormalizationMode=1` использует параметрическую настройку сопротивления синапса. Пресинаптическое торможение и Branch NextSeg — отдельные механизмы и факторы.",
        "",
        "В документах `PSI` означает пресинаптическое торможение, `NextSeg` — отдельное торможение следующего сегмента Branch, а `TipR` — сопротивление концевого синапса. Pack A/B/C обозначают сохранённые семейства входных последовательностей; их точные интервалы находятся в XML. Исторические подписи «FastSpan» и «Phase A/6» оставлены рядом с человеческим описанием: это сжатые по времени последовательности и длинный паттерн с настройкой порога зоны локальной временной интеграции.",
        "",
        "Для каждого опыта отдельно фиксируются: завершение/сходимость C++-обучения; качество разделения и доступная точность; детекция целевой последовательности. `Need=0` не заменяет проверку метрик, а успешный выход оценщика не подтверждает качество. Скрипты только собирают исходные конфиги, запускают C++-тренер, сохраняют результаты и анализируют их.",
        "",
        "Каждый случай имеет отдельные ручные папки Train и Test с XML/INI, хэш-манифестом и `Interface.xml` для графиков. Статическая проверка готовности нашла Train/Test и непустые настройки графиков у всех случаев; оригинальные варианты заголовков графиков сохранены в своих конфигурациях.",
        "",
        "## Покрытие исторических запусков",
        "",
        f"Проверено **{history.get('legacy_train_test_config_pair_count', 0)}** исторических Train/Test-папок и **{history.get('unique_model_parameter_pattern_signatures', 0)}** уникальных сигнатур условий. Сопоставления: {history_counts.get('exact source replay', 0)} точных источников, {history_counts.get('exact effective condition (documented historical alias)', 0)} документированный дубль фактической физической настройки, {history_counts.get('close analogue', 0)} близких аналогов, {history_counts.get('no coverage', 0)} без строки матрицы. Все 49 уникальных конфигураций октябрьского full49 имеют отдельные строки; повторные кампании привязаны к тем же условиям.",
        "",
        "Августовская серия FastResponse была отдельным перебором `DissociationTC × MembraneCapacity`: она вынесена в W46, а два случая с ручным TipR@Rmin — в W47. Папка `EXPD005C25e11` фактически задавала C=5e-10 Ф из-за ошибки UploadClass и отражена как дубль соответствующей настройки, а не как мнимая C=2.5e-10 Ф.",
        "",
        "Сохранённые оценки по старым конфигам относятся к своим историческим Train/Test и исходным версиям. Последний commit конфигурации не выдаётся за точный commit запуска; для значительной части старых опытов точный root/PulseLib/Bin/Console run pin не сохранился. Подробная построчная таблица: [историческое покрытие](../../../../Docs/Audit/TimeLearner-2026-09-26-review/HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md); хронология результатов: [CAMPAIGN_REPORT_2026-08_09.md](CAMPAIGN_REPORT_2026-08_09.md).",
        "",
        "## Ранее сохранённые результаты базовых 32 случаев",
        "",
        f"В имеющихся снимках W01–W04 записано {len(rows)} случаев: {convergence_counts.get('not_converged_at_stop', 0)} не сошлись к моменту остановки, {sum(v for k, v in convergence_counts.items() if k.startswith('converged'))} завершились с Need=0; строгих подтверждённых PASS по одновременным критериям сходимости, разделения и детекции — {successful_count}. Это ранее сохранённые результаты, не новые прогоны текущей подготовки. У них нет зафиксированного Console SHA, поэтому точную версию бинарника по этим таблицам восстановить нельзя.",
        "",
        "Среди двух сошедшихся случаев: `W03_BR25_N1_PSIoff` обнаружил цель, но получил только legacy `ok=1`, `Acc=7/8`, один false acceptance; strict-аудит в run bundle отсутствует. `W03_BR50_N1_PSIoff` не обнаружил цель (`Acc=7/8`, все `fires=00000000`; legacy gate `ok=0`). Старое поле `detection_quality=pass` переинтерпретируется по `target_hit`/`fires` и не считается качеством разделения.",
        "",
        "Сохранённые базовые результаты содержат много незавершённых обучений и требуют повторной проверки с известным бинарником. После каждой новой волны сначала анализируются C++-сходимость и причины остановки. Отказ тренера, несходимость или ошибка оценщика останавливают очередь для разбора; если C++-обучение завершилось, но разделение или детекция цели слабые, это записывается как результат качества, и следующие волны продолжаются.",
        "",
        "## Факторы и волны в порядке запуска",
        "",
        "Сначала проверяется сбалансированная базовая матрица; затем отдельные исторические конфигурации и взаимодействия. Любая волна — максимум восемь опытов и имеет обязательную точку анализа до следующей. Полные case ID, факторы и Train/Test ссылки ниже являются реестром исполнения.",
        "",
        "| Волна | Описание | Опытов |",
        "|---|---|---:|",
    ]
    for wave in registry.get("queue_order", []):
        title = (registry.get("wave_descriptions", {}).get(wave) or {}).get("title", "")
        intro.append(f"| {wave} | {md(title)} | {len(wave_cases.get(wave, []))} |")
    intro.extend(["", "## Реестр опытов и ручные конфиги", "", *matrix_lines])
    intro.extend(["## Результаты сохранённых запусков", "", *(result_sections or ["_Сохранённых результатов волн пока нет._"])])
    intro.extend([
        "## Протокол следующей волны",
        "",
        "Каждый запуск ограничен одной волной и имеет уникальный Run ID. После волны отчёты и её результаты обновляются и коммитятся, затем требуется анализ до запуска следующей волны. C++ refusal/non-convergence, ошибка оценщика, отсутствующий результат или инфраструктурная ошибка требуют паузы. Провал разделения или недетекция после завершённого обучения записываются отдельно и сами по себе не останавливают матрицу. Exit code процесса отдельно от метрик не считается PASS. Подробная процедура: [RUN_ON_SERVER.ru.md](TimeLearnerMatrix/RUN_ON_SERVER.ru.md); фактический порядок: `TimeLearnerMatrix/matrix.json`.",
        "",
        "Исторические Train/Test исходники остаются для воспроизводимости и связаны в Git; пользовательский текущий набор запусков находится в `TimeLearnerMatrix/Wxx/inputs/<case>/{Train,Test}`. Скрипт не переносит обучение и обновление состояния из C++ в Python.",
        "",
    ])
    EXPERIMENTS.write_text("\n".join(intro), encoding="utf-8")

    success = []
    for item in rows:
        result = item.get("result") or {}
        if (
            result
            and not result.get("row_fail")
            and str(result.get("training_convergence", "")).startswith("converged")
            and separation_quality(result) == "pass"
            and target_detection(result) == "detected"
        ):
            factor = item.get("matrix_factors") or item.get("factors") or {}
            train = f"TimeLearnerMatrix/{item['wave']}/inputs/{item['case']}/Train/Project.ini"
            test = f"TimeLearnerMatrix/{item['wave']}/inputs/{item['case']}/Test/Project.ini"
            success.append("| " + " | ".join([
                md(item["case"]),
                md(factor.get("trainer")),
                md(factor.get("duration_ms")),
                md(factor.get("normalization_mode")),
                md("включено" if factor.get("presynaptic_inhibition") else "выключено"),
                md(target_detection(result)),
                md(accuracy_summary(result)),
                f"[Train]({train}) / [Test]({test})",
            ]) + " |")
    success_lines = [
        "# Подтверждённые успешные эксперименты TimeLearner",
        "",
        "## Правило включения",
        "",
        "Сюда попадают только опыты, где C++-тренер сошёлся, строгие метрики качества разделения прошли аудит (`ok_audit=1`/эквивалентный зафиксированный strict gate) и цель обнаружена. `Need=0`, успешный код выхода оценщика и исторический permissive `ok=1` сами по себе недостаточны.",
        "",
        "Исторические PASS по старым конфигам и бинарникам остаются в [CAMPAIGN_REPORT_2026-08_09.md](CAMPAIGN_REPORT_2026-08_09.md), [исторической инвентаризации](../../../../Docs/Audit/TimeLearner-2026-09-26-review/HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md) и истории Git. Их нельзя выдавать за PASS текущего кода.",
        "",
        "## Подтверждённые случаи текущей матрицы",
        "",
        "| Случай | Тренер | Длительность, мс | Режим | Пресинаптическое торможение | Детекция цели | Acc / FP | Воспроизводимые конфиги |",
        "|---|---|---:|---|---|---|---|---|",
        *(success or ["| _Пока нет подтверждённых строгих PASS матричных прогонов._ | — | — | — | — | — | — | — |"]),
        "",
        "В сохранённых базовых W01–W04 есть два сходившихся обучения, но строгого PASS нет: один результат имеет legacy `ok=1`, Acc 7/8 и один false acceptance при отсутствующем strict-аудите; другой сошёлся, но не обнаружил цель. Эти результаты остаются в [EXPERIMENTS.md](EXPERIMENTS.md) в таблице сходимости, качества и детекции.",
        "",
        "Ручные Train/Test-конфиги каждой строки лежат в `TimeLearnerMatrix/<wave>/inputs/<case>/`. Полная матрица содержит отдельный Run case на обучение; внутренние восемь Test-проб не считаются восьмью отдельными обучениями.",
        "",
    ]
    SUCCESSFUL.write_text("\n".join(success_lines), encoding="utf-8")

    wave_rows = []
    for wave in registry.get("queue_order", []):
        specs = wave_cases.get(wave, [])
        if not specs:
            continue
        title = (registry.get("wave_descriptions", {}).get(wave) or {}).get("title", "")
        ids = ", ".join(spec["id"] for spec in specs)
        wave_rows.append(f"| {wave} | {md(title)} | {len(specs)} | `{ids}` |")
    historical_line = (
        f"Инвентаризировано {history.get('legacy_train_test_config_pair_count', 0)} старых Train/Test-пар и "
        f"{history.get('unique_model_parameter_pattern_signatures', 0)} уникальных сигнатур условий: "
        f"{history_counts.get('exact source replay', 0)} точных источников, "
        f"{history_counts.get('exact effective condition (documented historical alias)', 0)} документированный alias, "
        f"{history_counts.get('close analogue', 0)} близких аналогов, "
        f"{history_counts.get('no coverage', 0)} непокрытых записей."
    )
    plan_lines = [
        "# План волн матрицы TimeLearner",
        "",
        "## Объём и изменения после проверки истории",
        "",
        f"Подготовлена матрица из **{total_cases} опытов** и **{wave_count} волн**, максимум **{max_wave} опытов на волну**. Это подготовка будущего прогона; текущий документ не запускает обучение и не включает полный запуск 312 строк.",
        "",
        "Исходная конструкция из 294 опытов расширена на восемь взаимодействий Branch NextSeg×пресинаптическое торможение (W07/W08) и ещё на десять отсутствовавших исторических условий FastResponse: восемь фактических комбинаций постоянной диссоциации/ёмкости мембраны и два исторических ручных TipR@Rmin (W46/W47). Папка `EXPD005C25e11` в старом эксперименте реально устанавливала ту же ёмкость 5e-10 Ф, что `EXPD005C5e10`; это сохранённый повторный результат, не отдельное значение C.",
        "",
        "## Алгоритмы и смысл факторов",
        "",
        "Classic (`NNeuronTimeLearner`) распределяет импульсы по нескольким дендритам; Branch (`NNeuronTimeLearnerBranch`) учит размещение импульсов на разных сегментах одного дендрита. Оба меняют длины дендритов. В структурном режиме (`NormalizationMode=0`) амплитуда корректируется числом синапсов; в структурно-параметрическом (`NormalizationMode=1`) тренер настраивает сопротивление синапса. Пресинаптическое торможение и дополнительное торможение следующего сегмента Branch являются разными факторами.",
        "",
        "В действующем C++ коде максимум и минимум сопротивления синапса — наблюдаемые состояния, вычисляемые по мембранным сопротивлениям и параметру `MaxSynapseToMembraneResistanceRatio` (по умолчанию 1000). Стартовое сопротивление не пересчитывается как `Rm × InitialRatio`; оно берётся из исходной конфигурации/сохранённого состояния. W23–W26 специально исследуют влияние заданного стартового Rs. W3 (`EnableRmaxLengthEscape`) по умолчанию выключен; достижение предела Rs при нерешённой амплитуде должно завершаться отказом C++-обучения после проверки синхронизации. Состояния и проверки остаются в C++ тренеров.",
        "",
        "PSI — пресинаптическое торможение, NextSeg — торможение следующего сегмента, TipR — сопротивление концевого синапса. Pack A/B/C — точные семейства входных последовательностей, сохранённые в XML. Исторические подписи FastSpan и Phase A/6 относятся к сжатым по времени паттернам и настройке порога локальной временной интеграции; они не заменяют человеческое описание или XML.",
        "",
        "## Историческое покрытие",
        "",
        historical_line,
        "",
        "Все 49 уникальных конфигураций SoftCold full49 октябрьских запусков имеют отдельные строки точного повторения исходных Train/Test. Повторные кампании 3, 6 и 9 октября остаются несколькими историческими наблюдениями одной исходной конфигурации, а не новыми факторными клетками. Весь список 179 пар с историческим конфиг-коммитом, доступными CSV-метриками и различиями сопоставления: [HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md](../HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md).",
        "",
        "Старые August/September серии включают исходные baseline, пресинаптическое торможение, Branch/NextSeg, короткие паттерны, калибровку порога, асимметричные мембраны, FastResponse D×C и аудитные прогоны. Точные и близкие сопоставления указаны по каждой папке; Pack B/C 50-мс условия и некоторые сочетания торможения остаются близкими аналогами, явно с отличиями. Сохранённый Test CSV не доказывает C++ сходимость. Последний коммит изменения конфига не считается коммитом запуска, если run bundle не содержит версии бинарника.",
        "",
        "## Волны и порядок исполнения",
        "",
        "Порядок ниже совпадает с `TimeLearnerMatrix/matrix.json`. Запускайте одну волну за один вызов; после неё изучите результаты и обновите документы перед следующим запуском. Несходимость C++-обучения, отказ тренера, ошибка оценщика, инфраструктурная ошибка или неполный результат требуют паузы и классификации. Низкая метрика разделения или отсутствие детекции после завершённого обучения сохраняются как исходы эксперимента и не блокируют следующие волны автоматически.",
        "",
        "| Волна | Человеческое описание | Опытов | Case ID |",
        "|---|---|---:|---|",
        *wave_rows,
        "",
        "## Сервер, сохранение и границы",
        "",
        "Сборка и запуск выполняются только на удалённом `.17`; максимум восемь процессов `NeuroModelerConsole`; длительная очередь запускается внутри `tmux`, чтобы пережить потерю SSH и выключение рабочей станции. Перед каждой волной проверяется диск и уникальность рабочих каталогов. Входные пользовательские Train/Test снапшоты в `Bin/Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/Wxx/inputs/<case>/` не являются каталогами результатов; каждый содержит `Train/Project.ini`, `Test/Project.ini`, Interface для графиков и SHA-манифест.",
        "",
        "Скрипты только готовят входные конфиги, вызывают готовый C++ тренер, собирают логи/метрики и обновляют документы. Вся логика обучения и изменения состояния остаются в C++. Данные каждого запуска и компактный JSON-результат сохраняются отдельно. Обычный отказ — причина остановить очередь и провести анализ, а не условие пропустить к следующей волне.",
        "",
        "В этой подготовительной работе полный прогон не запускался. Имеющиеся W01–W04 — сохранённый серверный снимок из 32 базовых условий: 30 не сошлись к остановке, два завершились с `Need=0`; в одном legacy quality gate пропустил 7/8 с одним false acceptance, в другом целевая последовательность не детектировалась. Строгого PASS нет, а Console SHA для этих снимков не сохранён. До дальнейшего исполнения сначала требуется контрольный запуск с полным provenance.",
        "",
        "См. [EXPERIMENTS.md](../../../Bin/Configs/SpikeSamples/StructTrain/EXPERIMENTS.md) для каждой строки и ручных Train/Test ссылок, [SUCCESSFUL_EXPERIMENTS.md](../../../Bin/Configs/SpikeSamples/StructTrain/SUCCESSFUL_EXPERIMENTS.md) для строгого реестра успехов и [RUN_ON_SERVER.ru.md](../../../Bin/Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/RUN_ON_SERVER.ru.md) для команд серверного запуска.",
        "",
    ]
    WAVE_PLAN.parent.mkdir(parents=True, exist_ok=True)
    WAVE_PLAN.write_text("\n".join(plan_lines), encoding="utf-8")

    full_report_lines = [
        "# Полная матрица TimeLearner и исторические результаты",
        "",
        "**Срез:** 2026-10-10. **Статус:** подготовка завершена; полный запуск матрицы не выполнялся.",
        "",
        f"Текущий реестр содержит **{total_cases} обучающих опытов в {wave_count} волнах** (не более {max_wave} случаев на волну). Это исходные 294 предложенных условия плюс 8 отдельных NextSeg×PSI конфигураций и 10 FastResponse условий, которые не имели строки или близкой физической замены в исходном реестре. Подробные case ID, факторы, описания и пользовательские Train/Test конфиги приведены в [EXPERIMENTS.md](../../../Bin/Configs/SpikeSamples/StructTrain/EXPERIMENTS.md).",
        "",
        "## Что означают опыты",
        "",
        "Один случай — одно обучение одним C++-тренером с конкретным паттерном и параметрами. Восемь тестовых проб измеряют селективность одной полученной модели. Classic обучает согласование временных импульсов между несколькими дендритами; Branch — их положения на сегментах одного дендрита. Структурный режим корректирует число синапсов; структурно-параметрический изменяет сопротивление синапса. Пресинаптическое торможение, торможение следующего Branch-сегмента, PostTrain, TipR, физические параметры и порядок импульсов проверяются отдельными блоками.",
        "",
        "## Августовские и сентябрьские исторические конфигурации",
        "",
        historical_line,
        "",
        "История кампаний и их метрик, включая baseline, настройки пресинаптического торможения, Branch, короткие последовательности, калибровку локального порога, FastResponse и аудит 154 тестовых проб с 64 `ok_audit=1`, сведена в [CAMPAIGN_REPORT_2026-08_09.md](../../../Bin/Configs/SpikeSamples/StructTrain/CAMPAIGN_REPORT_2026-08_09.md). По каждой найденной Train/Test-паре приведены путь, последний коммит изменения конфига, сохранённые метрики и exact/analogue match в [HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md](HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md). В большинстве старых папок run commit и Console SHA отсутствуют: конфиг-коммит не выдаётся за версию запуска.",
        "",
        "Один пропуск исходного 294-плана устранён отдельными W46/W47: исторический FastResponse менял DTC и ёмкость канала в фиксированном паттерне 480 мс; он не заменяется изменением мембранного R или C в W41/W42. В W46 включены восемь фактически разных D×C клеток, в W47 — два отдельных испытания ручной настройки трёх TipR до 20 МОм при одном оставленном 86 МОм. Старая `EXPD005C25e11` была подписана как 2.5e-10 Ф, но UploadClass задавал 5e-10 Ф; её Test CSV относится к дублю `EXPD005C5e10`, а не к реальному измерению 2.5e-10 Ф.",
        "",
        "Построчный реестр и результаты mapping доступны в `Bin/Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/legacy_history_inventory.json`. 49 конфигураций SoftCold full49 03/06/09 октября повторяются отдельными актуальными строками; прежние 8/41 и 13/36 PASS/FAIL — разные запуски и разные gate-срезы, а full49 от 9 октября записал 0 PASS, 48 FAIL и один неполный `br100_search` (`rc=137`). Эти числа не доказывают, что 49 задач математически неразрешимы.",
        "",
        "## Сохранённые результаты базовых 32",
        "",
        f"Имеются результаты W01–W04 для {len(rows)} случаев: {convergence_counts.get('not_converged_at_stop', 0)} не сошлись к моменту остановки, {sum(v for k, v in convergence_counts.items() if k.startswith('converged'))} завершились с `Need=0`. Один из двух сошедшихся получил legacy `ok=1`, Acc=7/8 и один false acceptance, но без strict-аудита; другой имел Acc=7/8, `fires=00000000` и не детектировал цель. Строгого подтверждённого PASS нет. Снимкам не сопоставлен Console SHA, поэтому они остаются предварительной базовой точкой, а не provenance-полным подтверждением текущего кода.",
        "",
        "## Операционные условия",
        "",
        "Полный прогон 312 строк не входит в эту работу. Если позже понадобится контрольный запуск, его выполняют только на `.17`, с tmux и максимум восемью Console-процессами. После каждой волны — остановка, разбор C++ сходимости отдельно от качества/детекции и фиксация отчёта. Скрипты не исполняют алгоритм обучения: изменения состояния остаются внутри соответствующего C++ тренера.",
        "",
        f"Статическая готовность Train/Test/GUI: {readiness.get('case_count', 0)} конфигураций; `all_cases_have_train_test_and_gui={readiness.get('all_cases_have_train_test_and_gui')}`. Матрица: `full_matrix_execution_performed={registry.get('full_matrix_execution_performed', False)}`.",
        "",
    ]
    FULL_MATRIX_REPORT.write_text("\n".join(full_report_lines), encoding="utf-8")

    if ROOT_REPORT.exists():
        lines = [
            "# Текущий статус матричных волн TimeLearner", "",
            f"Обновлено: {datetime.now(timezone.utc).isoformat()} UTC.", "",
            f"Реестр подготовлен: {total_cases} опыта, {wave_count} волн, максимум {max_wave} в волне. Полный прогон не выполнялся в рамках подготовки. Существуют только сохранённые результаты: {len(rows)} базовых опытов W01–W04; exact Console SHA в этих записях отсутствует.", "",
        ]
        lines.extend(result_sections or ["Экспериментальных волн ещё нет."])
        ROOT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wave", nargs="?")
    parser.add_argument("--refresh-docs", action="store_true", help="regenerate reports from already saved wave snapshots without reading run bundles")
    args = parser.parse_args()
    if args.refresh_docs:
        update_documents()
        print(json.dumps({"documents_refreshed": True, "saved_wave_snapshots": len(result_rows())}, ensure_ascii=False))
        return 0
    if not args.wave:
        parser.error("provide WAVE or --refresh-docs")
    snapshot, target = collect_wave(args.wave)
    update_documents()
    print(json.dumps({
        "wave": args.wave,
        "cases": len(snapshot["cases"]),
        "all_results_saved": all(x["result"] is not None for x in snapshot["cases"]),
        "run_complete": snapshot["run_complete"],
        "result_snapshot": str(target.relative_to(BASE)),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
