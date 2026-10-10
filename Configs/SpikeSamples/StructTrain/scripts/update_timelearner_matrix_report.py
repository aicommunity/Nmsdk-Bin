#!/usr/bin/env python3
"""Turn per-case C++ trainer results into versioned, readable matrix reports."""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2].parent
MATRIX = BASE / "TimeLearnerMatrix"
EXPERIMENTS = BASE / "EXPERIMENTS.md"
SUCCESSFUL = BASE / "SUCCESSFUL_EXPERIMENTS.md"
ROOT_REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "evidence" / "metrics" / "TIMELEARNER_MATRIX_WAVES_20261010.md"
RUNS = BASE / "_repro" / "TimeLearnerMatrixRuns"
BEGIN = "<!-- GENERATED_WAVE_RESULTS_BEGIN -->"
END = "<!-- GENERATED_WAVE_RESULTS_END -->"


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def md(value: Any) -> str:
    if value is None or str(value) == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def result_rows() -> list[dict[str, Any]]:
    rows = []
    for wave_file in sorted(MATRIX.glob("W*/results.json")):
        data = load_json(wave_file)
        if not isinstance(data, dict):
            continue
        for case in data.get("cases", []):
            rows.append({"wave": data.get("wave", wave_file.parent.name), **case})
    return rows


def collect_wave(wave: str) -> tuple[dict[str, Any], Path]:
    registry = json.loads((MATRIX / "matrix.json").read_text(encoding="utf-8"))
    specs = [c for c in registry["cases"] if c["wave"] == wave]
    if not specs:
        raise ValueError(f"wave not in matrix registry: {wave}")
    status = load_json(RUNS / wave / "wave_status.json") or {}
    cases = []
    for spec in specs:
        path = RUNS / wave / spec["id"] / "matrix_result.json"
        row = load_json(path)
        cases.append({
            "case": spec["id"],
            "factors": spec,
            "result": row,
            "infrastructure_status": status.get("cases", {}).get(spec["id"], {}).get("status", "missing"),
        })
    snapshot = {
        "wave": wave,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "jobs": status.get("jobs", 8),
        "started_utc": status.get("started_utc"),
        "finished_utc": status.get("finished_utc"),
        "run_complete": bool(status.get("run_complete")),
        "cases": cases,
    }
    target = MATRIX / wave / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return snapshot, target


def category(row: dict[str, Any]) -> str:
    if not row:
        return "результат не сохранён"
    conv = str(row.get("training_convergence") or "не определена")
    quality = str(row.get("posttune_quality") or "не оценено")
    detection = str(row.get("detection_quality") or "не оценено")
    if conv.startswith("converged") or conv == "training_converged":
        if row.get("row_fail"):
            return "обучение сошлось; quality/detection FAIL"
        return "обучение сошлось; quality/detection PASS"
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
    rows = result_rows()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in rows:
        grouped.setdefault(item["wave"], []).append(item)
    sections = []
    for wave in sorted(grouped):
        group = grouped[wave]
        table = [
            f"### {wave}",
            "",
            "| Случай | Сходимость обучения | Качество PostTune | Детекция цели | Need | Fires | Категория |",
            "|---|---|---|---|---:|---|---|",
        ]
        for item in group:
            result = item.get("result") or {}
            after = result.get("after") or {}
            table.append("| " + " | ".join([
                md(item["case"]),
                md(result.get("training_convergence", item.get("infrastructure_status"))),
                md(result.get("posttune_quality")),
                md(result.get("detection_quality")),
                md(after.get("IsNeedToTrain")),
                md(result.get("fires")),
                md(category(result)),
            ]) + " |")
        sections.extend(table + [""])
    replace_block(EXPERIMENTS, "\n".join(sections) if sections else "_Выполненных волн пока нет._")

    success = []
    for item in rows:
        result = item.get("result") or {}
        if (
            result
            and not result.get("row_fail")
            and str(result.get("training_convergence", "")).startswith("converged")
            and result.get("detection_quality") == "pass"
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
                md(result.get("detection_quality")),
                f"[Train]({train}) / [Test]({test})",
            ]) + " |")
    successful_body = "\n".join([
        "| Случай | Тренер | Длительность, мс | Режим | Пресинаптическое торможение | Детекция | Воспроизводимые конфиги |",
        "|---|---|---:|---|---|---|---|",
        *(success or ["| _Пока нет подтверждённых PASS новых матричных прогонов._ | — | — | — | — | — | — |"]),
    ])
    replace_block(SUCCESSFUL, successful_body)

    if ROOT_REPORT.exists():
        lines = ["# Текущий статус матричных волн TimeLearner", "", f"Обновлено: {datetime.now(timezone.utc).isoformat()} UTC.", ""]
        lines.extend(sections or ["Экспериментальных волн ещё нет."])
        ROOT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wave")
    args = parser.parse_args()
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
