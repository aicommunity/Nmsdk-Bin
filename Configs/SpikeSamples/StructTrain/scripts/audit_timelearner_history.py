#!/usr/bin/env python3
"""Inventory saved Aug-Oct TimeLearner configs and map them to current matrix rows.

This is a read-only audit of tracked historical inputs and saved evaluator CSVs.
It never launches NeuroModelerConsole or changes training state.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
BIN_ROOT = BASE.parents[2]
ROOT = BIN_ROOT.parent
MATRIX = BASE / "TimeLearnerMatrix"
MANIFEST = MATRIX / "matrix.json"
FULL49_COVERAGE = MATRIX / "historical_coverage.json"
OUTPUT = MATRIX / "legacy_history_inventory.json"
REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md"
FAMILY_REPORT = BASE / "CAMPAIGN_REPORT_2026-08_09.md"
SKIP_PARTS = {"TimeLearnerMatrix", "_repro", ".git"}
EFFECTIVE_CONDITION_ALIASES = {
    "SelectivityFastResponse/EXPD005C25e11": {
        "matrix_case_id": "W46_HIST_FAST_D005_C5E10",
        "reason": "The historical UploadClass for D005C25e11 actually sets MembraneCapacity=5e-10 F, identical to EXPD005C5e10; the intended 2.5e-10 F was never applied. Keep its saved result as a separate historical observation of the same effective condition.",
    }
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def xml_values(path: Path, tag: str) -> list[str]:
    if not path.is_file():
        return []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []
    return [(node.text or "").strip() for node in root.iter(tag)]


def config_signature(config: Path) -> str:
    h = hashlib.sha256()
    for side in ("Train", "Test"):
        folder = config / side
        for name in ("Model_00.xml", "Parameters_00.xml"):
            path = folder / name
            if path.is_file():
                h.update(f"{side}/{name}".encode())
                h.update(path.read_bytes())
        for pattern in ("Matrix*.xml", "Pack*.xml", "*.pack"):
            for path in sorted(folder.glob(pattern)):
                h.update(f"{side}/{path.name}".encode())
                h.update(path.read_bytes())
    return h.hexdigest()


def git_config_revision(relative: str) -> dict[str, Any]:
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(BIN_ROOT), "log", "-1", "--format=%H", "--", relative],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if not commit:
            return {"config_last_changed_commit": None, "config_commit_date": None}
        date = subprocess.check_output(
            ["git", "-C", str(BIN_ROOT), "show", "-s", "--format=%cI", commit],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return {"config_last_changed_commit": commit, "config_commit_date": date}
    except (OSError, subprocess.CalledProcessError):
        return {"config_last_changed_commit": None, "config_commit_date": None}


def duration_from_path(relative: str) -> int | None:
    lower = relative.lower()
    for pattern in (r"span[_-]?(\d+)", r"br[_-]?(\d+)", r"exp[_-](\d+)", r"(\d+)ms"):
        match = re.search(pattern, lower)
        if match:
            value = int(match.group(1))
            if value in (10, 25, 50, 100, 200, 300, 400, 480):
                return value
    if "phase6" in lower or "phasea" in lower or relative.split("/")[0] == "TimeNeuronTimeLearner":
        return 480
    return None


def pattern_family(relative: str) -> str:
    lower = relative.lower()
    if "fastresponse" in lower:
        return "FastResponse/RC"
    if "fastspan" in lower:
        return "FastSpan"
    if "ltzcalibrate" in lower or "ltzcal" in lower:
        return "LTZ-calibrated"
    if "phasea" in lower or "phase6" in lower:
        return "PhaseA/Phase6"
    pack = re.search(r"pack[_-]?([abc])", lower)
    if pack:
        return f"Pack {pack.group(1).upper()}"
    if "branch" in lower:
        return "Branch pack A"
    if "asymrm" in lower or "presynapticinhib" in lower:
        return "AsymRm / PSI"
    return "legacy baseline"


def old_factors(config: Path, relative: str) -> dict[str, Any]:
    lower = relative.lower()
    trainer = "NNeuronTimeLearnerBranch" if "branch" in lower or "timeneurontimelearnerbranch" in lower else "NNeuronTimeLearner"
    model = config / "Train" / "Model_00.xml"
    params = config / "Train" / "Parameters_00.xml"
    classes = xml_values(model, "SynapseClassName") + xml_values(params, "SynapseClassName")
    flags = xml_values(model, "UsePresynapticInhibition") + xml_values(params, "UsePresynapticInhibition")
    preinh_classes = [value for value in classes if "Preinh" in value]
    psi = any(value.strip() == "1" for value in flags) or bool(preinh_classes) or "preinh" in lower
    coeff = None
    coeff_match = re.search(r"preinh(\d+)_(\d+)", " ".join(preinh_classes), re.I)
    if coeff_match:
        coeff = float(f"{coeff_match.group(1)}.{coeff_match.group(2)}")
    if coeff is None:
        coeff_match = re.search(r"preinh[_-]?(\d{3,4})", lower)
        if coeff_match:
            coeff = int(coeff_match.group(1)) / 100
    nextseg_values = xml_values(model, "EnableNextSegmentInhibition") + xml_values(params, "EnableNextSegmentInhibition")
    nextseg = any(value == "1" for value in nextseg_values) or "nextseg" in lower
    norm_values = xml_values(params, "NormalizationMode")
    pack = re.search(r"pack[_-]?([abc])", lower)
    return {
        "trainer": trainer,
        "duration_ms": duration_from_path(relative),
        "pattern_family": pattern_family(relative),
        "pack": pack.group(1).upper() if pack else ("A" if pattern_family(relative) in ("AsymRm / PSI", "Branch pack A", "FastSpan", "LTZ-calibrated") else None),
        "normalization_mode": int(norm_values[0]) if norm_values and norm_values[0].isdigit() else None,
        "presynaptic_inhibition": psi,
        "presynaptic_coefficient": coeff,
        "branch_nextseg": nextseg,
    }


def saved_test_metrics(config: Path) -> dict[str, Any]:
    path = config / "Test" / "SelectivityLog" / "results.csv"
    if not path.is_file():
        return {"results_csv": None, "metrics_status": "not found"}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, csv.Error) as exc:
        return {"results_csv": path.as_posix(), "metrics_status": f"unreadable: {exc}", "results_csv_sha256": sha256(path)}
    matches = [row for row in rows if row.get("match") == "1"]
    target = next((row for row in rows if row.get("trial") == "0"), None)
    false_accepts = [row for row in rows if row.get("trial") != "0" and row.get("neuron_fired") == "1"]
    late_false_positives = [row for row in rows if row.get("trial") != "0" and row.get("late_fired") == "1"]
    return {
        "results_csv": path.as_posix(),
        "results_csv_sha256": sha256(path),
        "metrics_status": "stored evaluator CSV; does not prove C++ convergence or identify the run commit",
        "n_trials": len(rows),
        "legacy_match_count": len(matches),
        "legacy_accuracy": f"{len(matches)}/{len(rows)}" if rows else None,
        "target_detected": target.get("neuron_fired") == "1" if target else None,
        "false_accept_trial_count": len(false_accepts),
        "late_false_positive_count": len(late_false_positives),
        "fire_all": bool(rows) and all(row.get("neuron_fired") == "1" for row in rows),
    }


def case_source(case: dict[str, Any], templates: dict[str, Any]) -> str:
    return str(case.get("source_config") or templates[case["template"]].get("paired_source", templates[case["template"]].get("preinh_source", "")))


def row_match_score(old: dict[str, Any], case: dict[str, Any], source: str) -> tuple[int, list[str]]:
    if old["trainer"] != case.get("trainer"):
        return -100, ["trainer differs"]
    score = 2
    differences: list[str] = []
    if old.get("duration_ms") is not None:
        if old["duration_ms"] == case.get("duration_ms"):
            score += 2
        else:
            differences.append("pattern duration differs")
    if old.get("pack"):
        family_text = f"{case.get('pattern_family', '')} {source}".lower()
        if f"pack {old['pack'].lower()}" in family_text or f"pack{old['pack'].lower()}" in family_text:
            score += 3
        elif old["pack"] == "A" and "pack a" in family_text:
            score += 3
        else:
            differences.append("pattern family differs")
    if old.get("presynaptic_inhibition") == bool(case.get("presynaptic_inhibition")):
        score += 2
    else:
        differences.append("presynaptic inhibition state differs")
    if old.get("branch_nextseg") == bool(case.get("branch_nextseg")):
        score += 2
    else:
        differences.append("Branch NextSeg state differs")
    if old.get("normalization_mode") is not None:
        if old["normalization_mode"] == case.get("normalization_mode"):
            score += 1
        else:
            differences.append("NormalizationMode differs")
    if old.get("presynaptic_coefficient") is not None and old.get("presynaptic_inhibition"):
        if case.get("presynaptic_coefficient") == old["presynaptic_coefficient"]:
            score += 1
        else:
            differences.append("PSI coefficient differs")
    if old["pattern_family"] == "FastResponse/RC" and "rm/c" not in source.lower():
        differences.append("FastResponse RC parameter set has no matching dedicated matrix family")
        score -= 3
    if old["pattern_family"] == "FastSpan" and "fastspan" not in source.lower() and "fastspan" not in str(case.get("pattern_family", "")).lower():
        differences.append("FastSpan time-constant family differs")
        score -= 3
    return score, differences


def build_inventory() -> tuple[dict[str, Any], str]:
    matrix = json.loads(MANIFEST.read_text(encoding="utf-8"))
    coverage = json.loads(FULL49_COVERAGE.read_text(encoding="utf-8"))
    exact_source_map: dict[str, list[str]] = defaultdict(list)
    cases_by_id = {case["id"]: case for case in matrix["cases"]}
    for case in matrix["cases"]:
        if case.get("source_mode") == "historical_exact":
            exact_source_map[case_source(case, matrix["templates"])].append(case["id"])

    configs: set[Path] = set()
    for project_ini in BASE.rglob("Train/Project.ini"):
        if any(part in SKIP_PARTS for part in project_ini.parts):
            continue
        config = project_ini.parent.parent
        if (config / "Test" / "Project.ini").is_file():
            configs.add(config)

    signatures: dict[str, list[str]] = defaultdict(list)
    for config in configs:
        signatures[config_signature(config)].append(config.relative_to(BASE).as_posix())

    records: list[dict[str, Any]] = []
    for config in sorted(configs):
        relative = config.relative_to(BASE).as_posix()
        factors = old_factors(config, relative)
        exact_ids = exact_source_map.get(relative, [])
        candidates: list[tuple[int, dict[str, Any], str, list[str]]] = []
        for case in matrix["cases"]:
            source = case_source(case, matrix["templates"])
            score, differences = row_match_score(factors, case, source)
            if score >= 0:
                candidates.append((score, case, source, differences))
        candidates.sort(key=lambda entry: (-entry[0], entry[1]["id"]))
        if exact_ids:
            mapping_quality = "exact source replay"
            mapped_rows = exact_ids
            mapping_differences: list[str] = []
            source_commits = sorted({cases_by_id[case_id].get("source_commit") for case_id in exact_ids if cases_by_id[case_id].get("source_commit")})
            source_commit = source_commits[0] if len(source_commits) == 1 else source_commits
            historical_rows = [
                coverage["cases"].get(cases_by_id[case_id].get("worker_case"))
                for case_id in exact_ids
                if cases_by_id[case_id].get("worker_case") in coverage["cases"]
            ]
        elif relative in EFFECTIVE_CONDITION_ALIASES:
            alias = EFFECTIVE_CONDITION_ALIASES[relative]
            mapping_quality = "exact effective condition (documented historical alias)"
            mapped_rows = [alias["matrix_case_id"]]
            mapping_differences = [alias["reason"]]
            source_commit = cases_by_id[alias["matrix_case_id"]].get("source_commit")
            historical_rows = []
        elif candidates and candidates[0][0] >= 7:
            mapping_quality = "close analogue"
            mapped_rows = [candidate[1]["id"] for candidate in candidates[:3] if candidates[0][0] - candidate[0] <= 1]
            mapping_differences = candidates[0][3]
            source_commit = None
            historical_rows = []
        else:
            mapping_quality = "no coverage"
            mapped_rows = []
            mapping_differences = candidates[0][3] if candidates else ["no same-trainer matrix row"]
            source_commit = None
            historical_rows = []
        git_path = "Configs/SpikeSamples/StructTrain/" + relative
        revision = git_config_revision(git_path)
        metrics = saved_test_metrics(config)
        record = {
            "source_config": relative,
            "source_config_git_path": git_path,
            **revision,
            "source_run_commit": "not identified in the saved artifacts; config revision is not asserted to be the run revision",
            "historical_factors_inferred_from_config": factors,
            "mapping_quality": mapping_quality,
            "current_matrix_rows": mapped_rows,
            "mapping_differences_or_limits": mapping_differences,
            "stored_test_metrics": metrics,
            "unique_train_test_factor_signature": config_signature(config),
            "duplicate_config_paths_with_same_train_test_signature": sorted(signatures[config_signature(config)]),
            "historical_full49_cross_reference": historical_rows,
            "historical_report": "Configs/SpikeSamples/StructTrain/CAMPAIGN_REPORT_2026-08_09.md",
        }
        if exact_ids:
            record["historical_source_bin_commit"] = source_commit
            record["historical_full49_campaign_summaries"] = [entry for entry in historical_rows if entry]
        if relative in EFFECTIVE_CONDITION_ALIASES:
            record["documented_historical_alias"] = EFFECTIVE_CONDITION_ALIASES[relative]
        records.append(record)

    summary = {
        "schema": 1,
        "generated_utc": matrix.get("generated_utc"),
        "source_matrix_version": matrix.get("matrix_version"),
        "legacy_train_test_config_pair_count": len(records),
        "unique_model_parameter_pattern_signatures": len(signatures),
        "tracked_campaign_summary": "Configs/SpikeSamples/StructTrain/CAMPAIGN_REPORT_2026-08_09.md covers 13-Aug through 8-Sep and summarizes later September validation campaigns.",
        "campaign_run_commits_for_august_september": "not fully recorded per run in the saved config folders; per-config last-changed Bin commit is listed and must not be misrepresented as the run commit",
        "records": records,
    }
    count_quality = Counter(row["mapping_quality"] for row in records)
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in records:
        by_family[row["historical_factors_inferred_from_config"]["pattern_family"]][row["mapping_quality"]] += 1
    lines = [
        "# Историческое покрытие экспериментов TimeLearner (август — октябрь 2026)",
        "",
        "Сводка инвентаризирует текущие Train/Test-пары, относящиеся к кампаниям августа и сентября, и связывает их с подготовленной текущей матрицей. Она не объявляет сохранённый Test CSV доказательством сходимости C++-обучения.",
        "",
        f"В Bin найдены **{len(records)}** исторических пар Train/Test. После группировки по Model/Parameters и паттерн-файлам остаётся **{len(signatures)}** различных сигнатур условий. В текущей матрице: {count_quality.get('exact source replay',0)} точных повторов входных конфигов, {count_quality.get('exact effective condition (documented historical alias)',0)} документированный дубль фактически той же настройки, {count_quality.get('close analogue',0)} близких аналогов и {count_quality.get('no coverage',0)} записей без строки.",
        "",
        "Источники: [сводный отчёт кампаний августа—сентября](../../../Bin/Configs/SpikeSamples/StructTrain/CAMPAIGN_REPORT_2026-08_09.md), [полная строковая инвентаризация JSON](../../../Bin/Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/legacy_history_inventory.json), [full49-покрытие и run-метрики](../../../Bin/Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/historical_coverage.json). Для каждой папки указан последний Git-коммит изменения конфигурации. Он не считается коммитом запуска: старые каталоги обычно не сохраняют точную пару root/PulseLib/Bin/Console для конкретного результата.",
        "",
        "## Покрытие по семействам",
        "",
        "| Историческое семейство | Train/Test-папок | Точный входной конфиг | Документированный дубль | Близкий аналог | Нет строки |",
        "|---|---:|---:|---:|---:|",
    ]
    for family, counts in sorted(by_family.items()):
        lines.append(f"| {family} | {sum(counts.values())} | {counts.get('exact source replay',0)} | {counts.get('exact effective condition (documented historical alias)',0)} | {counts.get('close analogue',0)} | {counts.get('no coverage',0)} |")
    lines.extend([
        "",
        "## Что добавлено в матрицу и какие остаются пробелы",
        "",
        "- Все 49 уникальных условий октябрьского full49 связаны с точными Train/Test-входами из Bin-коммита 6a7ef63a и отдельными матричными строками. Повторные кампании 3, 6 и 9 октября прикреплены к тем же строкам как наблюдения, а не считаются новыми условиями.",
        "- Исторические Classic/Branch baseline, FastSpan, LTZ-calibration, PSI sweep, PhaseA/Phase6 и Branch NextSeg/PSI имеют прямые или близкие сопоставления; качество сопоставления и отличающиеся факторы записаны по каждой папке в JSON.",
        "- Pack B/C покрыты отдельными текущими структурными/структурно-параметрическими клетками для Classic и Branch на 25 и 100 мс; исторические 50-мс и PSI/NextSeg-взаимодействия не выдаются за точное покрытие этой сеткой.",
        "- Для исторического FastResponse добавлены W46 (восемь фактически различных настроек DissociationTC×MembraneCapacity) и W47 (два случая PHASE10.3 с ручным TipR@Rmin). Это отдельная серия, а не аналог имеющихся изменений Rm/Cm. Папка `EXPD005C25e11` задавала фактическую ёмкость 5e-10 Ф из-за ошибки UploadClass; её старый результат сопоставлен той же физической настройке, что и `EXPD005C5e10`.",
        "- Исторические переключения LTZone/порога и audit-only прогоны по 8 проб — это этап проверки качества распознавания после обучения, а не отдельные опыты с алгоритмом TimeLearner. Их сохранённые метрики остаются в историческом отчёте и не добавляются как новые C++-обучения.",
        "- Конфигурации NextSeg×PSI подготовлены отдельными строками W07/W08 для 25/50/100/480 мс и двух режимов NormalizationMode. Их SynapseClassName сопоставлены только с существующим коэффициентным классом 2.5 при сохранении NextSeg-топологии. В сумме с W46/W47 матрица теперь содержит 312 опытов: исходные 294 + 8 NextSeg×PSI + 10 FastResponse.",
        "",
        "## Детали строк",
        "",
        "JSON содержит одну запись на каждую из найденных исторических Train/Test-пар: путь исходного конфига, inferred-факторы, последний commit конфигов, доступные метрики CSV, выбранные строки матрицы, различия и повторяющиеся сигнатуры. Отдельно указаны ссылки на полные 49 октябрьских повторов и на августовские FastResponse исходники.",
        "",
        "| Источник конфигурации | Полный коммит изменения конфига | Факторы | Матч матрицы | Строки | Отличия / предел аналога | Сохранённая метрика |",
        "|---|---|---|---|---|---|---|",
    ])
    for row in records:
        factors = row["historical_factors_inferred_from_config"]
        metric = row["stored_test_metrics"]
        metric_text = metric.get("legacy_accuracy") or metric.get("metrics_status", "—")
        if metric.get("n_trials"):
            metric_text += f"; target={metric.get('target_detected')}; FP={metric.get('false_accept_trial_count')}"
        commit = row.get("config_last_changed_commit") or "unknown"
        differences = "; ".join(row.get("mapping_differences_or_limits") or []) or "точный входной источник"
        lines.append(
            f"| `{row['source_config']}` | `{commit}` | {factors['trainer']}, {factors['duration_ms'] or 'n/a'} ms, {factors['pattern_family']}, PSI={factors['presynaptic_inhibition']}, NextSeg={factors['branch_nextseg']}, N={factors['normalization_mode']} | {row['mapping_quality']} | {', '.join(row['current_matrix_rows']) or '—'} | {differences.replace('|', '\\|')} | {metric_text.replace('|', '\\|')} |"
        )
    lines.extend([
        "",
        "Показатели `legacy_accuracy`, `target_detected` и FP рассчитаны только по сохранённому evaluator CSV; они ничего не говорят о завершении C++-обучения, если это не подтверждено отдельным run bundle.",
        "",
    ])
    return summary, "\n".join(lines)


def main() -> int:
    inventory, report = build_inventory()
    OUTPUT.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(report, encoding="utf-8")
    counts = Counter(row["mapping_quality"] for row in inventory["records"])
    print(json.dumps({
        "legacy_config_pairs": inventory["legacy_train_test_config_pair_count"],
        "unique_factor_signatures": inventory["unique_model_parameter_pattern_signatures"],
        "mapping_quality": counts,
        "inventory": str(OUTPUT.relative_to(BASE)),
        "report": str(REPORT.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
