#!/usr/bin/env python3
"""Analyze paired classifier recordings with explicit lateral-synapse inputs."""

from __future__ import annotations

import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


LTZ_THRESHOLD = 1e-5
SYNAPSE_SIGNAL_THRESHOLD = 1e-12


def csv_rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fields = list(reader.fieldnames or [])
        rows = [{key: float(value) if value else 0.0 for key, value in row.items() if key}
                for row in reader]
    return fields, rows


def column_alias(name: str) -> str:
    return name.split(" [", 1)[0]


def column_source(name: str) -> str | None:
    if " [" not in name or not name.endswith("]"):
        return None
    return name.rsplit(" [", 1)[1][:-1]


def trace_path_for(directory: Path) -> Path:
    readme = directory / "README.md"
    if readme.is_file():
        match = re.search(r"CSV:\s*`([^`]+)`", readme.read_text(encoding="utf-8-sig"))
        if match:
            candidate = directory / match.group(1)
            if candidate.is_file():
                return candidate
    return directory / "ClassifierDynamics" / "signals.csv"


def rising_edges(rows: list[dict[str, float]], column: str, threshold: float) -> list[float]:
    result: list[float] = []
    previous = 0.0
    for row in rows:
        value = row.get(column, 0.0)
        if previous <= threshold < value:
            result.append(row["model_time"])
        previous = value
    return result


def parameter_text(path: Path, component: str, property_name: str) -> str | None:
    root = ET.parse(path).getroot()
    node = root.find(f".//{component}/Parameters/{property_name}")
    return node.text.strip() if node is not None and node.text else None


def summarize(directory: Path) -> dict:
    trace = trace_path_for(directory)
    if not trace.is_file():
        return {"path": directory.name, "error": "no recorder CSV"}

    fields, rows = csv_rows(trace)
    signal_fields = fields[1:]
    mapped_fields = [name for name in signal_fields if column_source(name)]
    if len(signal_fields) > 1 and len(mapped_fields) != len(signal_fields):
        return {"path": directory.name,
                "error": "multi-signal trace lacks verified source paths in its CSV header; rerun with the updated recorder"}
    class_component = "SpikeClassifier" if directory.name.startswith("NSpikeClassifier") else "Classifier"
    freq_text = parameter_text(directory / "Parameters_00.xml", class_component, "SpikesFrequency")
    frequency = float(freq_text) if freq_text else None
    sample_interval = (1.0 / frequency - 0.002) if frequency else None
    input_lines = [line for line in (directory / "input_data.txt").read_text(encoding="utf-8-sig").splitlines()
                   if line.strip()]
    output_lines = [line.split() for line in (directory / "output_data.txt").read_text(encoding="utf-8-sig").splitlines()
                    if line.strip()] if (directory / "output_data.txt").exists() else []

    response_columns = [name for name in fields
                        if re.fullmatch(r"(?:NeuronTrainer\d+|OrNeuron\d+)_ltz", column_alias(name))]
    response_times = {column_alias(name): rising_edges(rows, name, LTZ_THRESHOLD) for name in response_columns}

    synapse_inputs = [name for name in fields
                      if column_alias(name).endswith("_input") and "InhSynapse" in column_alias(name)]
    synapse_outputs = [name for name in fields
                       if column_alias(name).endswith("_output") and "InhSynapse" in column_alias(name)]
    synapse_stats = {}
    for input_name in synapse_inputs:
        alias = column_alias(input_name)
        prefix = alias[:-len("_input")]
        output_name = prefix + "_output"
        output_column = next((name for name in synapse_outputs if column_alias(name) == output_name), None)
        input_values = [row.get(input_name, 0.0) for row in rows]
        output_values = [row.get(output_column, 0.0) for row in rows] if output_column else []
        input_edges = rising_edges(rows, input_name, SYNAPSE_SIGNAL_THRESHOLD)
        target_match = re.match(r"(?:NeuronTrainer|OrNeuron)(\d+)", alias)
        target_idx = int(target_match.group(1)) if target_match else None
        target_responses = [col for col in response_columns
                            if target_idx is not None and re.match(rf"(?:NeuronTrainer|OrNeuron){target_idx}_ltz$", col)]
        spike_times = [time for col in target_responses for time in response_times[col]]
        synapse_stats[alias] = {
            "input_source": column_source(input_name),
            "output_source": column_source(output_column) if output_column else None,
            "input_peak": max((abs(value) for value in input_values), default=0.0),
            "input_nonzero_samples": sum(abs(value) > SYNAPSE_SIGNAL_THRESHOLD for value in input_values),
            "input_rising_edges": input_edges,
            "output_peak": max((abs(value) for value in output_values), default=0.0),
            "output_nonzero_samples": sum(abs(value) > SYNAPSE_SIGNAL_THRESHOLD for value in output_values),
            "target_spikes_after_each_input_edge": [
                sum(edge <= spike < edge + 0.1 for spike in spike_times) for edge in input_edges
            ],
        }

    window_spikes = {}
    late_edges = {}
    if sample_interval:
        input_duration = sample_interval * len(input_lines)
        for name, times in response_times.items():
            window_spikes[name] = [sum(i * sample_interval <= t < (i + 1) * sample_interval for t in times)
                                   for i in range(len(input_lines))]
            late_edges[name] = [t for t in times if t >= input_duration]

    summary = {
        "path": directory.name,
        "model_time_end": rows[-1]["model_time"] if rows else None,
        "sample_frequency_hz": frequency,
        "sample_window_seconds": sample_interval,
        "input_pattern_rows": len(input_lines),
        "output_data_rows": output_lines,
        "signal_columns": {column_alias(name): column_source(name) for name in fields[1:]},
        "response_rising_edges": response_times,
        "response_edge_counts": {name: len(times) for name, times in response_times.items()},
        "response_edges_per_input_window": window_spikes,
        "response_edges_after_last_input_window": late_edges,
        "lateral_synapses": synapse_stats,
        "recorded_lateral_synapse_columns": len(synapse_inputs) + len(synapse_outputs),
    }
    return summary


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: analyze_detailed_dynamics.py <experiment-dir> [...]")
    results = [summarize(Path(item)) for item in sys.argv[1:]]
    output = Path(sys.argv[1]).parent / "detailed_dynamics_summary.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
