#!/usr/bin/env python3
"""Summarize classifier replay traces and verify output bits against LTZone edges."""

from __future__ import annotations

import argparse
import csv
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def response_period(project: Path) -> float:
    root = ET.parse(project / "Parameters_00.xml").getroot()
    classifier = next(
        node for node in root.iter()
        if node.get("Class") in {"NSpikeClassifier", "NClassifier"}
    )
    params = classifier.find("./Parameters")
    frequency = float(params.findtext("SpikesFrequency", "0"))
    time_step = float(params.findtext("TimeStep", "0"))
    if time_step <= 0:
        ini = (project / "Project.ini").read_text(encoding="utf-8-sig")
        match = re.search(r"<GlobalTimeStep>([^<]+)</GlobalTimeStep>", ini)
        time_step = float(match.group(1)) if match else 0.0
    if frequency <= 0 or time_step <= 0:
        raise ValueError(f"Invalid response period in {project}")
    return 1.0 / frequency - 1.0 / time_step


def read_outputs(path: Path) -> list[list[int]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        values = [float(part) for part in line.split()]
        if any(value not in (0.0, 1.0) for value in values):
            raise ValueError(f"{path}:{line_number}: output values must be 0 or 1")
        rows.append([int(value) for value in values])
    return rows


def read_edges(path: Path, period: float) -> tuple[dict[str, dict[int, int]], int, float]:
    edges: dict[str, dict[int, int]] = {}
    previous: dict[str, float] = {}
    last_time = 0.0
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        aliases = [item.partition(" [")[0] for item in header]
        indices = [i for i, alias in enumerate(aliases) if alias.lower().endswith("_ltz")]
        if not indices:
            indices = [i for i, alias in enumerate(aliases) if alias.lower().endswith("ltz")]
        edges = {aliases[i]: {} for i in indices}
        for row in reader:
            if len(row) != len(aliases):
                continue
            now = float(row[0])
            last_time = now
            for i in indices:
                alias = aliases[i]
                value = float(row[i])
                if previous.get(alias, 0.0) < 0.5 <= value:
                    window = max(0, math.ceil((now - 1e-10) / period) - 1)
                    edges[alias][window] = edges[alias].get(window, 0) + 1
                previous[alias] = value
    window_count = max(0, math.floor((last_time + 1e-9) / period))
    return edges, window_count, last_time


def primary_outputs(project: Path, aliases: list[str], width: int) -> list[str]:
    # NClassifier writes the aggregated OR-layer LTZones; the example trainers
    # are still monitored for bursts but are not the classifier's output bits.
    or_aliases = [alias for alias in aliases if re.fullmatch(r"or_class\d+_ltz", alias, re.I)]
    if or_aliases:
        return sorted(or_aliases, key=lambda value: int(re.search(r"\d+", value).group()))
    numbered = [alias for alias in aliases if re.fullmatch(r"(?:class|NeuronTrainer)\d+_ltz", alias, re.I)]
    if numbered:
        return sorted(numbered, key=lambda value: int(re.search(r"\d+", value).group()))
    if width == 1:
        candidates = [alias for alias in aliases if alias.lower().endswith("_ltz")]
        if len(candidates) == 1:
            return candidates
    return []


def analyze(project: Path) -> dict[str, object]:
    output_rows = read_outputs(project / "output_data.txt")
    period = response_period(project)
    edges, trace_windows, last_time = read_edges(project / "signals.csv", period)
    aliases = list(edges)
    selected = primary_outputs(project, aliases, len(output_rows[0]) if output_rows else 0)
    expected_bits = len(output_rows[0]) if output_rows else 0
    width_matches = len(selected) == expected_bits
    compared = min(len(output_rows), trace_windows)
    matched = 0
    no_response = 0
    multi_bit = 0
    one_hot = 0
    max_primary_edges = 0
    output_edge_rows: list[str] = []
    for window, row in enumerate(output_rows[:compared]):
        counts = [edges[alias].get(window, 0) for alias in selected]
        actual = [count > 0 for count in counts]
        output_edge_rows.append("/".join(map(str, counts)))
        if width_matches and [int(value) for value in actual] == row:
            matched += 1
        active = sum(row)
        no_response += active == 0
        multi_bit += active > 1
        one_hot += active == 1
        max_primary_edges = max(
            max_primary_edges,
            max((edges[alias].get(window, 0) for alias in selected), default=0),
        )

    bursts: list[str] = []
    burst_windows: set[int] = set()
    max_any = 0
    for alias, per_window in edges.items():
        for window, count in per_window.items():
            max_any = max(max_any, count)
            if count > 1:
                bursts.append(f"{alias}@{window + 1}={count}")
                burst_windows.add(window + 1)

    project_id = project.name
    result: dict[str, object] = {
        "project": project_id,
        "period_seconds": f"{period:.6f}",
        "output_rows": len(output_rows),
        "trace_windows": trace_windows,
        "last_model_time": f"{last_time:.6f}",
        "signals_monitored": len(edges),
        "primary_outputs": ";".join(selected),
        "output_rows_compared": compared,
        "output_bits_match_trace": matched if width_matches else "width mismatch",
        "output_bits": ";".join("".join(map(str, row)) for row in output_rows[:compared]),
        "primary_edge_counts_by_row": ";".join(output_edge_rows),
        "burst_windows": ";".join(map(str, sorted(burst_windows))),
        "burst_signals": ";".join(bursts),
        "max_edges_any_signal_window": max_any,
        "max_edges_primary_output_window": max_primary_edges,
        "one_hot_rows": one_hot,
        "multi_bit_rows": multi_bit,
        "no_response_rows": no_response,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("projects", nargs="+", help="clone names under project-root")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    results = [analyze(args.project_root / name) for name in args.projects]
    output = args.output or args.project_root / "burst_replay_summary.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {output}")
    for result in results:
        bursts = result["burst_signals"] or "none"
        print(
            f"{result['project']}: rows={result['output_rows_compared']}/"
            f"{result['output_rows']}, bursts={bursts}, "
            f"bit/trace matches={result['output_bits_match_trace']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
