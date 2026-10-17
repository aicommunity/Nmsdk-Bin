#!/usr/bin/env python3
"""Audit configured channel time scales without running a trainer.

This tool only reads experiment XML and reports the dimensionless quantity
Q = C * R * f used to assess the fixed-step NPulseChannel update. It does not
implement or alter any learning behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


DEFAULT_FREQUENCY_HZ = 2000.0
CHANNEL_RESISTANCE_FIELDS = ("Resistance", "RestingResistance", "FBResistance")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_float(element: ET.Element, name: str) -> float | None:
    child = element.find(name)
    if child is None or child.text is None:
        return None
    try:
        value = float(child.text.strip())
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def classify_q(q: float) -> str:
    # For the coded channel update K=(1+G*R)^2/Q and G>=0, so K>=1/Q.
    # Strict linear stability requires K<2; monotone no-crossing requires K<=1.
    if q <= 0.5:
        return "no_strict_linear_stability_for_any_finite_Rs"
    if q <= 1.0:
        return "no_finite_monotone_no_crossing_Rs_floor"
    return "finite_monotone_no_crossing_Rs_floor_possible"


def load_manifest(case_dir: Path) -> dict[str, Any]:
    manifest_path = case_dir / "matrix_input_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def project_frequency(project_path: Path, override_hz: float | None) -> tuple[float, dict[str, Any]]:
    settings: dict[str, Any] = {}
    if project_path.exists():
        project_text = project_path.read_text(encoding="utf-8", errors="replace")
        for name in ("DefaultTimeStep", "GlobalTimeStep", "UseIndTimeStepFlag"):
            # Project.ini is XML-like but channel tags such as <00> are not
            # legal XML names, so use a narrow field parser instead of ET.
            values = re.findall(rf"<{name}>\s*([^<\s]+)\s*</{name}>", project_text)
            if values:
                settings[name] = values

    use_individual = any(
        int(value) != 0 for value in settings.get("UseIndTimeStepFlag", ["0"])
    )
    if override_hz is not None:
        return override_hz, {
            "source": "explicit --frequency-hz override",
            "project_settings": settings,
        }
    if use_individual:
        raise ValueError(
            f"{project_path}: UseIndTimeStepFlag is enabled; per-channel time-step overrides "
            "must be resolved before this static audit can classify the case"
        )

    global_values = [float(value) for value in settings.get("GlobalTimeStep", [])]
    default_values = [float(value) for value in settings.get("DefaultTimeStep", [])]
    nonzero_global = [value for value in global_values if value > 0.0]
    candidates = nonzero_global or default_values or [DEFAULT_FREQUENCY_HZ]
    distinct = sorted(set(candidates))
    if len(distinct) != 1:
        raise ValueError(
            f"{project_path}: multiple channel time-step values {distinct}; "
            "resolve them per channel before this static audit"
        )
    frequency = distinct[0]
    if not math.isfinite(frequency) or frequency <= 0.0:
        raise ValueError(f"{project_path}: no positive GlobalTimeStep/DefaultTimeStep found")
    source = "Train/Project.ini GlobalTimeStep" if nonzero_global else "Train/Project.ini DefaultTimeStep"
    return frequency, {"source": source, "project_settings": settings}


def inspect_parameters(path: Path, frequency_hz: float) -> tuple[list[dict[str, Any]], int]:
    tree = ET.parse(path)
    root = tree.getroot()
    parents = {child: parent for parent in root.iter() for child in parent}

    time_step_tags = [node.text.strip() for node in root.iter("TimeStep") if node.text]
    if time_step_tags:
        raise ValueError(
            f"{path}: explicit TimeStep values need per-channel inheritance handling: "
            f"{time_step_tags[:5]}"
        )

    channels: list[dict[str, Any]] = []
    channel_count = 0
    for parameters in root.iter("Parameters"):
        capacity = text_float(parameters, "Capacity")
        if capacity is None:
            continue

        component = parents.get(parameters)
        channel_count += 1
        resistances: list[dict[str, Any]] = []
        if component is not None:
            for field in CHANNEL_RESISTANCE_FIELDS:
                resistance = text_float(parameters, field)
                if resistance is None or resistance <= 0.0:
                    continue
                q = capacity * resistance * frequency_hz
                resistances.append({
                    "field": field,
                    "resistance_ohm": resistance,
                    "q": q,
                    "minimum_step_gain_at_G_zero": 1.0 / q,
                    "classification": classify_q(q),
                })

        if resistances:
            channels.append({
                "component_name": component.tag if component is not None else "",
                "component_class": component.attrib.get("Class", "") if component is not None else "",
                "capacity_farad": capacity,
                "resistance_modes": resistances,
            })
    return channels, channel_count


def audit_matrix(matrix_dir: Path, frequency_override: float | None) -> dict[str, Any]:
    parameter_files = sorted(matrix_dir.glob("W*/inputs/*/Train/Parameters_00.xml"))
    cases: list[dict[str, Any]] = []
    summary = Counter()
    frequency_counts: Counter[float] = Counter()
    q_mode_counts = Counter()
    minimum_q_observed: dict[str, Any] | None = None
    total_channels = 0

    for parameters_path in parameter_files:
        case_dir = parameters_path.parents[1]
        manifest = load_manifest(case_dir)
        frequency_hz, frequency_source = project_frequency(
            case_dir / "Train" / "Project.ini", frequency_override)
        channels, channel_count = inspect_parameters(parameters_path, frequency_hz)
        total_channels += channel_count
        frequency_counts[frequency_hz] += 1

        all_modes = [
            (channel, mode)
            for channel in channels
            for mode in channel["resistance_modes"]
        ]
        case_minimum = min(
            ((mode["q"], channel, mode) for channel, mode in all_modes),
            key=lambda item: item[0],
            default=None,
        )
        for _, mode in all_modes:
            if mode["q"] <= 0.5:
                q_mode_counts["q_le_0_5"] += 1
            if mode["q"] <= 1.0:
                q_mode_counts["q_le_1"] += 1
            if mode["q"] <= 2.0 * (1.0 + 1.0e-12):
                q_mode_counts["q_le_2_with_1e-12_relative_tolerance"] += 1
        if case_minimum is not None:
            q_value, q_channel, q_mode = case_minimum
            if minimum_q_observed is None or q_value < minimum_q_observed["q"]:
                minimum_q_observed = {
                    "q": q_value,
                    "case_id": manifest.get("case", case_dir.name),
                    "wave": manifest.get("wave", case_dir.parent.name),
                    "frequency_hz": frequency_hz,
                    "component_name": q_channel["component_name"],
                    "component_class": q_channel["component_class"],
                    "capacity_farad": q_channel["capacity_farad"],
                    "resistance_field": q_mode["field"],
                    "resistance_ohm": q_mode["resistance_ohm"],
                }

        risks = [
            (channel, mode)
            for channel in channels
            for mode in channel["resistance_modes"]
            if mode["q"] <= 1.0
        ]
        risk_groups: Counter[tuple[str, str, float, str, float, float, str]] = Counter()
        for channel, mode in risks:
            risk_groups[(
                channel["component_name"], channel["component_class"],
                channel["capacity_farad"], mode["field"],
                mode["resistance_ohm"], mode["q"], mode["classification"],
            )] += 1

        minimum_q = case_minimum[0] if case_minimum is not None else None
        risk_class = classify_q(minimum_q) if minimum_q is not None else "no_channel_parameters"
        summary[risk_class if risks else "all_configured_modes_q_above_1"] += 1
        cases.append({
            "id": manifest.get("case", case_dir.name),
            "wave": manifest.get("wave", case_dir.parent.name),
            "frequency_hz": frequency_hz,
            "time_step_seconds": 1.0 / frequency_hz,
            "frequency_source": frequency_source["source"],
            "project_ini": (case_dir / "Train" / "Project.ini").relative_to(matrix_dir).as_posix(),
            "project_ini_sha256": (
                sha256_file(case_dir / "Train" / "Project.ini")
                if (case_dir / "Train" / "Project.ini").is_file() else None
            ),
            "train_parameters": parameters_path.relative_to(matrix_dir).as_posix(),
            "train_parameters_sha256": sha256_file(parameters_path),
            "channel_count": channel_count,
            "minimum_q": minimum_q,
            "minimum_step_gain_at_G_zero": 1.0 / minimum_q if minimum_q else None,
            "classification": risk_class if risks else "all_configured_modes_q_above_1",
            "risk_channel_modes": [
                {
                    "component_name": row[0],
                    "component_class": row[1],
                    "capacity_farad": row[2],
                    "resistance_field": row[3],
                    "resistance_ohm": row[4],
                    "q": row[5],
                    "minimum_step_gain_at_G_zero": 1.0 / row[5],
                    "classification": row[6],
                    "channel_count": count,
                }
                for row, count in sorted(risk_groups.items())
            ],
        })

    return {
        "schema_version": 2,
        "purpose": "static fixed-step stability precondition audit; no training code is run. Q alone does not establish runtime stability because G and active resistance vary during simulation.",
        "matrix_dir": matrix_dir.as_posix(),
        "frequency_hz_override": frequency_override,
        "frequency_provenance": "Train/Project.ini GlobalTimeStep or DefaultTimeStep when UseIndTimeStepFlag=0; explicit override is available",
        "formula": {
            "channel_update": "V_next = V + (u - (1 + G*R)*V)/(Ti*f)",
            "ti": "C/(G + 1/R)",
            "step_gain": "K = (1 + G*R)^2/(C*R*f)",
            "lower_bound_for_G_nonnegative": "K >= 1/Q, Q=C*R*f",
            "strict_linear_stability": "0 < K < 2",
            "monotone_no_crossing": "0 < K <= 1",
        },
        "files_examined": len(parameter_files),
        "channel_parameter_nodes_examined": total_channels,
        "cases_with_q_at_or_below_1": sum(
            1 for case in cases if case["classification"] != "all_configured_modes_q_above_1"
        ),
        "frequency_counts_hz": {
            str(key): value for key, value in sorted(frequency_counts.items())
        },
        "configured_channel_modes_below_thresholds": dict(sorted(q_mode_counts.items())),
        "minimum_q_observed": minimum_q_observed,
        "summary": dict(sorted(summary.items())),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parents[1]
    parser.add_argument("--matrix-dir", type=Path, default=default_dir)
    parser.add_argument("--frequency-hz", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.frequency_hz is not None and (
        not math.isfinite(args.frequency_hz) or args.frequency_hz <= 0.0
    ):
        parser.error("--frequency-hz must be finite and positive")

    result = audit_matrix(args.matrix_dir.resolve(), args.frequency_hz)
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
