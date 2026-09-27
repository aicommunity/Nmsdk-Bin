#!/usr/bin/env python3
"""Summarize recorded classifier spikes, synaptic inhibition, and dendritic recovery."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


LTZ_THRESHOLD = 1e-5


def load_trace(path: Path) -> tuple[list[str], list[dict[str, float]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = [{key: float(value) if value else 0.0 for key, value in row.items() if key}
                for row in reader]
    return fields, rows


def column_alias(name: str) -> str:
    """Return the configured alias, without the recorder's verified source path."""
    return name.split(" [", 1)[0]


def column_source(name: str) -> str | None:
    if " [" not in name or not name.endswith("]"):
        return None
    return name.rsplit(" [", 1)[1][:-1]


def trace_path_for(path: Path) -> Path:
    readme = path / "README.md"
    if readme.is_file():
        match = re.search(r"CSV:\s*`([^`]+)`", readme.read_text(encoding="utf-8-sig"))
        if match:
            candidate = path / match.group(1).replace("/", "/")
            if candidate.is_file():
                return candidate
    return path / "ClassifierDynamics" / "signals.csv"


def edges(rows: list[dict[str, float]], column: str, threshold: float) -> list[float]:
    result: list[float] = []
    prev = 0.0
    for row in rows:
        value = row.get(column, 0.0)
        if prev <= threshold < value:
            result.append(row["model_time"])
        prev = value
    return result


def summarize(path: Path) -> dict:
    trace_path = trace_path_for(path)
    if not trace_path.is_file():
        return {"path": str(path), "error": "no recorder output"}
    fields, rows = load_trace(trace_path)
    signal_fields = fields[1:]
    mapped_fields = [name for name in signal_fields if column_source(name)]
    if len(signal_fields) > 1 and len(mapped_fields) != len(signal_fields):
        return {"path": path.name,
                "error": "multi-signal trace lacks verified source paths in its CSV header; rerun with the updated recorder"}
    is_nclassifier = "NClassifier_Synthetic_" in path.name
    response_prefixes = ("OrNeuron" if is_nclassifier else "NeuronTrainer")
    response_columns = [name for name in fields
                        if column_alias(name).startswith(response_prefixes)
                        and column_alias(name).endswith("_ltz")]
    response_edges_by_column = {name: edges(rows, name, LTZ_THRESHOLD) for name in response_columns}
    response_edges = {column_alias(name): times for name, times in response_edges_by_column.items()}

    inhibition_columns = [name for name in fields
                          if "_InhSynapse" in column_alias(name)
                          and column_alias(name).endswith("_output")]
    inhibitory_events = []
    for column in inhibition_columns:
        onset_times = edges(rows, column, 0.0)
        values = [row.get(column, 0.0) for row in rows]
        for onset in onset_times:
            index = next((i for i, row in enumerate(rows) if row["model_time"] >= onset), 0)
            peak = max(values[index:index + 50] or [0.0])
            decay_time = rows[-1]["model_time"] if rows else onset
            if peak > 0:
                for i in range(index + 1, len(rows)):
                    if rows[i].get(column, 0.0) <= peak * 0.01:
                        decay_time = rows[i]["model_time"]
                        break
            alias = column_alias(column)
            target = alias.split("_InhSynapse", 1)[0]
            target_idx = int("".join(c for c in target if c.isdigit()) or "0")
            for competitor_column, spike_times in response_edges_by_column.items():
                competitor_alias = column_alias(competitor_column)
                competitor_idx = int("".join(c for c in competitor_alias.split("_", 1)[0] if c.isdigit()) or "0")
                if competitor_idx != target_idx:
                    continue
                inhibitory_events.append({
                    "inhibitory_signal": alias,
                    "inhibitory_signal_source": column_source(column),
                    "arrival_time": onset,
                    "peak": peak,
                    "decay_time_1pct": decay_time,
                    "competitor_ltz": competitor_alias,
                    "competitor_ltz_source": column_source(competitor_column),
                    "spikes_after_arrival_before_decay": sum(onset <= t <= decay_time for t in spike_times),
                    "spikes_after_decay": sum(t > decay_time for t in spike_times),
                })

    potentials = [name for name in fields
                  if "_dendrite" in column_alias(name) and column_alias(name).endswith("_terminal")]
    potential_summary = {}
    for column in potentials:
        values = [row.get(column, 0.0) for row in rows]
        potential_summary[column_alias(column)] = {
            "source": column_source(column),
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
            "last": values[-1] if values else 0.0,
        }

    return {
        "path": path.name,
        "samples": len(rows),
        "model_time_start": rows[0]["model_time"] if rows else None,
        "model_time_end": rows[-1]["model_time"] if rows else None,
        "signal_columns": {column_alias(name): column_source(name) for name in fields[1:]},
        "response_spike_times": response_edges,
        "response_spike_counts": {name: len(times) for name, times in response_edges.items()},
        "response_isis": {
            name: [round(b - a, 9) for a, b in zip(times, times[1:])]
            for name, times in response_edges.items()
        },
        "inhibitory_events": inhibitory_events,
        "dendritic_terminal_potentials": potential_summary,
        "output_data_rows": [line.strip() for line in (path / "output_data.txt").read_text(encoding="utf-8-sig").splitlines()
                             if line.strip()] if (path / "output_data.txt").exists() else [],
    }


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: analyze_classifier_dynamics.py <experiment-dir> [...]")
    results = [summarize(Path(value)) for value in sys.argv[1:]]
    out_path = Path(sys.argv[1]).parent / "dynamics_summary.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
