#!/usr/bin/env python3
"""Inventory fixed-step stability prerequisites across a config tree.

This is a read-only config audit. It does not start a model or implement any
learning behavior. Q=C*R*f is only the zero-conductance feasibility bound;
runtime K also depends on the actual channel conductance G.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from audit_timelearner_step_stability import inspect_parameters, project_frequency, sha256_file


def git_head(path: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def audit_config_tree(config_root: Path) -> dict[str, Any]:
    repo_root = SCRIPT_DIR.parents[5]
    bin_root = repo_root / "Bin"
    relative_root = config_root.relative_to(bin_root).as_posix()
    tracked_paths = subprocess.run(
        ["git", "-C", str(bin_root), "ls-files", "--", relative_root],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    parameter_paths = [
        bin_root / relative_path
        for relative_path in tracked_paths
        if relative_path.endswith("/Train/Parameters_00.xml")
    ]
    cases: list[dict[str, Any]] = []
    frequencies: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    config_counts: Counter[str] = Counter()
    unresolved: list[dict[str, str]] = []

    for parameter_path in sorted(parameter_paths):
        project_path = parameter_path.parent / "Project.ini"
        if not project_path.is_file():
            unresolved.append({
                "train_parameters": parameter_path.relative_to(config_root).as_posix(),
                "reason": "missing sibling Train/Project.ini",
            })
            continue

        try:
            frequency_hz, frequency_info = project_frequency(project_path, None)
            channels, channel_count = inspect_parameters(parameter_path, frequency_hz)
        except (OSError, ValueError, ET.ParseError) as error:
            unresolved.append({
                "train_parameters": parameter_path.relative_to(config_root).as_posix(),
                "reason": str(error),
            })
            continue
        modes = [
            (channel, mode)
            for channel in channels
            for mode in channel["resistance_modes"]
        ]
        if not modes:
            continue

        minimum_channel, minimum_mode = min(modes, key=lambda pair: pair[1]["q"])
        minimum_q = float(minimum_mode["q"])
        for _, mode in modes:
            q = float(mode["q"])
            if q <= 0.5 * (1.0 + 1.0e-12):
                mode_counts["q_le_0_5"] += 1
            if q <= 1.0 * (1.0 + 1.0e-12):
                mode_counts["q_le_1"] += 1
            if q <= 2.0 * (1.0 + 1.0e-12):
                mode_counts["q_le_2"] += 1

        relative_parameter = parameter_path.relative_to(config_root).as_posix()
        relative_project = project_path.relative_to(config_root).as_posix()
        frequencies[f"{frequency_hz:.12g}"] += 1
        for threshold, label in ((0.5, "q_le_0_5"), (1.0, "q_le_1"), (2.0, "q_le_2")):
            if minimum_q <= threshold * (1.0 + 1.0e-12):
                config_counts[label] += 1

        cases.append({
            "train_parameters": relative_parameter,
            "train_parameters_sha256": sha256_file(parameter_path),
            "project_ini": relative_project,
            "project_ini_sha256": sha256_file(project_path),
            "frequency_hz": frequency_hz,
            "frequency_source": frequency_info["source"],
            "channel_parameter_nodes": channel_count,
            "minimum_q": minimum_q,
            "minimum_mode": {
                "component_name": minimum_channel["component_name"],
                "component_class": minimum_channel["component_class"],
                **minimum_mode,
            },
            "classification": minimum_mode["classification"],
            "modes_with_q_le_1": [
                {
                    "component_name": channel["component_name"],
                    "component_class": channel["component_class"],
                    **mode,
                }
                for channel, mode in modes
                if float(mode["q"]) <= 1.0 * (1.0 + 1.0e-12)
            ],
        })

    low_q_cases = [case for case in cases if case["minimum_q"] <= 1.0 * (1.0 + 1.0e-12)]
    return {
        "schema_version": 1,
        "purpose": "Read-only inventory of Train config fixed-step feasibility; Q excludes runtime synaptic conductance G.",
        "config_root": str(config_root.resolve()),
        "source_revisions": {
            "root": git_head(repo_root),
            "bin": git_head(repo_root / "Bin"),
            "pulse_lib": git_head(repo_root / "Libraries" / "Nmsdk-PulseLib"),
        },
        "train_config_count": len(cases),
        "tracked_train_parameter_files": len(parameter_paths),
        "unresolved_parameter_files": unresolved,
        "frequency_counts_hz": dict(sorted(frequencies.items(), key=lambda item: float(item[0]))),
        "channel_mode_counts": dict(sorted(mode_counts.items())),
        "config_counts_by_minimum_q": dict(sorted(config_counts.items())),
        "minimum_q_over_tree": min(cases, key=lambda case: case["minimum_q"]) if cases else None,
        "low_q_cases": low_q_cases,
        "cases": cases,
    }


def main() -> int:
    default_root = SCRIPT_DIR.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path, default=default_root)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_config_tree(args.config_root.resolve())
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
