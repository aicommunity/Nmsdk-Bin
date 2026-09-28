#!/usr/bin/env python3
"""Summarize fixed-length synapse-count replays and validate classifier bits."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "NSpikeSynapseCountAudit_20260928"
WINDOWS = ((0.0, 2.0), (2.0, 4.0), (4.0, 6.0), (6.0, 8.01))
NAME_RE = re.compile(r"NSpikeClassifier_Class2_D17_Syn(\d+)_(On|Off)_20260928$")


def read_output(path: Path) -> list[list[int]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append([int(float(value)) for value in line.split()])
    if any(len(row) != 3 for row in rows):
        raise ValueError(f"Expected three output bits per row in {path}")
    return rows


def read_trace(path: Path) -> tuple[list[dict[str, float]], dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        names = []
        aliases: dict[str, str] = {}
        for title in header:
            if title == "model_time":
                names.append(title)
                aliases[title] = ""
                continue
            alias, separator, source = title.partition(" [")
            if not separator or not source.endswith("]"):
                raise ValueError(f"Missing component path in CSV column {title!r}")
            names.append(alias)
            aliases[alias] = source[:-1]
        rows = [
            {name: float(value) for name, value in zip(names, raw)}
            for raw in reader
        ]
    return rows, aliases


def edge_times(rows: list[dict[str, float]], signal: str) -> list[float]:
    if not rows or signal not in rows[0]:
        raise ValueError(f"Signal {signal!r} is absent from trace")
    return [
        rows[index]["model_time"]
        for index in range(1, len(rows))
        if rows[index - 1][signal] < 0.5 <= rows[index][signal]
    ]


def in_window(times: list[float], window: tuple[float, float]) -> list[float]:
    start, end = window
    return [time for time in times if start <= time < end]


def summarize(path: Path) -> dict[str, object]:
    match = NAME_RE.fullmatch(path.name)
    if match is None:
        raise ValueError(f"Unexpected clone name {path.name}")
    synapse_count, inhibition = int(match.group(1)), match.group(2)
    output = read_output(path / "output_data.txt")
    if len(output) != len(WINDOWS):
        raise ValueError(f"Expected {len(WINDOWS)} output rows in {path}")
    traces = list((path / "ClassifierDynamicsCompetition").glob("*.csv"))
    if len(traces) != 1:
        raise ValueError(f"Expected one competition trace in {path}, found {len(traces)}")
    rows, aliases = read_trace(traces[0])
    class_edges = {
        class_id: edge_times(rows, f"NeuronTrainer{class_id}_ltz")
        for class_id in (1, 2, 3)
    }

    for index, window in enumerate(WINDOWS):
        actual = [int(bool(in_window(class_edges[class_id], window))) for class_id in (1, 2, 3)]
        if output[index] != actual:
            raise ValueError(
                f"Output bits differ from LTZone edges in {path.name}, window {index + 1}: "
                f"{output[index]} != {actual}"
            )

    target_window = WINDOWS[2]
    target_rows = [row for row in rows if target_window[0] <= row["model_time"] < target_window[1]]
    if not target_rows:
        raise ValueError(f"No trace samples for the third pattern in {path}")
    target_edges = in_window(class_edges[2], target_window)
    source_edges = in_window(class_edges[3], target_window)
    inh_input_alias = "class2_inh_syn2input1"
    inh_output_alias = "class2_inh_syn21"
    inhibition_edges = in_window(edge_times(rows, inh_input_alias), target_window)
    inhibition_peak = max(row[inh_output_alias] for row in target_rows)
    return {
        "active_branch_length": 17,
        "branch_synapses": synapse_count,
        "inhibition": inhibition,
        "third_pattern_class2_spikes": len(target_edges),
        "third_pattern_class2_spike_times_s": target_edges,
        "third_pattern_class3_spikes": len(source_edges),
        "third_pattern_class3_spike_times_s": source_edges,
        "third_pattern_class2_inhibitory_input_edges_s": inhibition_edges,
        "third_pattern_class2_inhibitory_synapse_peak": inhibition_peak,
        "third_pattern_class2_ltz_potential_peak": max(
            row["class2_ltz_potential"] for row in target_rows
        ),
        "third_pattern_output_bits": "".join(map(str, output[2])),
        "model_time_samples": len(rows),
        "trace_end_s": rows[-1]["model_time"],
    }


def main() -> None:
    results = [summarize(path) for path in sorted(ROOT.glob("NSpikeClassifier_Class2_D17_Syn*_20260928"))]
    if not results:
        raise FileNotFoundError(f"No synapse-count variants in {ROOT}")
    output_json = ROOT / "synapse_count_summary.json"
    output_csv = ROOT / "synapse_count_summary.csv"
    output_json.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(output_csv)
    print(output_json)


if __name__ == "__main__":
    main()
