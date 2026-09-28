#!/usr/bin/env python3
"""Analyze the shared-threshold replay across fixed dendrite lengths."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "NSpikeDendriteThresholdAudit_20260928"
VARIANTS = {"short": 3, "medium": 8, "long": 17}
WINDOWS = [(i, float(i * 2), float((i + 1) * 2)) for i in range(4)]


def field_for_path(rows: list[dict[str, str]], path: str) -> str:
    matches = [name for name in rows[0] if f"[{path}]" in name]
    if len(matches) != 1:
        raise ValueError(f"Expected one field for {path}, got {matches}")
    return matches[0]


def edges(rows: list[dict[str, str]], name: str, start: float, end: float) -> list[float]:
    previous = 0.0
    result: list[float] = []
    for row in rows:
        time = float(row["model_time"])
        value = float(row[name])
        if start <= time < end and previous <= 0.0 < value:
            result.append(round(time, 6))
        # Carry the previous sample across window boundaries. Resetting it at
        # each window would mistake a pulse that remained high from the prior
        # window for a fresh rising edge.
        previous = value
    return result


def summarize(root: Path, mode: str, label: str, length: int) -> dict[str, object]:
    name = f"NSpikeClassifier_Class2_{label}_D{length}_{mode}_Threshold00085_20260928"
    project = root / name
    trace = project / "trace.csv"
    if not trace.is_file():
        raise FileNotFoundError(trace)
    with trace.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 16200 or float(rows[-1]["model_time"]) < 8.0:
        raise ValueError(f"{name}: incomplete trace ({len(rows)} samples)")
    # The saved signal connection order can differ from the hand-written CSV
    # aliases. Select each real LTZone output by its persisted component path.
    ltz = [
        field_for_path(rows, f"Model.SpikeClassifier.NeuronTrainer{i}.Neuron.LTZone.Output")
        for i in range(1, 4)
    ]
    ltz_potentials = []
    for i in range(1, 4):
        path = f"Model.SpikeClassifier.NeuronTrainer{i}.Neuron.LTZone.OutputPotential"
        try:
            ltz_potentials.append(field_for_path(rows, path))
        except ValueError:
            # The existing recorder clone exposes potentials for classes 1–2;
            # class 3 is only sampled at its binary LTZone output.
            ltz_potentials.append(None)
    output_text = (project / "output_data.txt").read_text(encoding="utf-8").strip()
    output_rows = [[int(value) for value in line.split()] for line in output_text.splitlines() if line.strip()]
    if len(output_rows) != 4:
        raise ValueError(f"{name}: expected 4 result rows, got {len(output_rows)}")
    windows = []
    for index, start, end in WINDOWS:
        per_class = [edges(rows, column, start, end) for column in ltz]
        interval_rows = [row for row in rows if start <= float(row["model_time"]) < end]
        max_potential_by_class = [
            max(float(row[column]) for row in interval_rows) if column else None
            for column in ltz_potentials
        ]
        edge_bits = [int(bool(events)) for events in per_class]
        if edge_bits != output_rows[index]:
            raise ValueError(
                f"{name} window {index + 1}: trace LTZone bits {edge_bits} "
                f"do not match output_data.txt {output_rows[index]}"
            )
        windows.append({
            "window": index + 1,
            "expected_class": index + 1 if index < 3 else None,
            "output_bits": output_rows[index],
            "ltz_edges_seconds_by_class": per_class,
            "edge_counts_by_class": [len(value) for value in per_class],
            "max_ltz_potential_by_class": max_potential_by_class,
        })
    return {
        "project": name,
        "mode": mode,
        "length_variant": label,
        "dendrite_length": length,
        "threshold": 0.0085,
        "trace_samples": len(rows),
        "last_model_time": float(rows[-1]["model_time"]),
        "windows": windows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=ROOT)
    args = parser.parse_args()
    results = [
        summarize(args.input_root, mode, label, length)
        for mode in ("On", "Off")
        for label, length in VARIANTS.items()
    ]
    (args.input_root / "length_threshold_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (args.input_root / "length_threshold_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("mode", "length_variant", "dendrite_length", "window", "output_bits", "class1_edges", "class2_edges", "class3_edges", "class1_max_potential", "class2_max_potential", "class3_max_potential"))
        for run in results:
            for window in run["windows"]:
                counts = window["edge_counts_by_class"]
                writer.writerow((run["mode"], run["length_variant"], run["dendrite_length"], window["window"], "".join(map(str, window["output_bits"])), *counts, *window["max_ltz_potential_by_class"]))
    print(args.input_root / "length_threshold_summary.csv")
    print(args.input_root / "length_threshold_summary.json")


if __name__ == "__main__":
    main()
