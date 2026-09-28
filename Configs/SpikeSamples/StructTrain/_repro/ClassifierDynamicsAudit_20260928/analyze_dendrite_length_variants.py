#!/usr/bin/env python3
"""Summarize matched class-2 dendrite length On/Off replay clones."""

from __future__ import annotations

import csv
import json
import argparse
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "NSpikeDendriteLengthAudit_20260928"
VARIANTS = {"short": 3, "medium": 8, "long": 17}
WINDOWS = [(i, float(i * 2), float((i + 1) * 2)) for i in range(4)]


def read_edges(rows: list[dict[str, str]], field: str, start: float, end: float) -> list[float]:
    events: list[float] = []
    previous = 0.0
    for row in rows:
        time = float(row["model_time"])
        value = float(row[field])
        if start <= time < end and previous <= 0.0 < value:
            events.append(round(time, 6))
        previous = value if start <= time < end else 0.0
    return events


def field_for(rows: list[dict[str, str]], alias: str) -> str:
    return next(key for key in rows[0] if key.startswith(alias + " ["))


def summarize(root: Path, mode: str, label: str, length: int) -> dict[str, object]:
    project = root / f"NSpikeClassifier_Class2_{label}_D{length}_{mode.title()}_20260928"
    trace_files = list((project / "ClassifierDynamicsCompetition").glob("*.csv"))
    if len(trace_files) != 1:
        raise RuntimeError(f"{project}: expected one trace CSV, found {len(trace_files)}")
    with trace_files[0].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or float(rows[-1]["model_time"]) < 8.0:
        raise RuntimeError(f"{project}: incomplete trace")

    ltz_fields = [field_for(rows, f"NeuronTrainer{i}_ltz") for i in range(1, 4)]
    class2_tip = field_for(rows, "class2_dendrite_input2")
    class2_inh_input = field_for(rows, "class2_inh_syn2input2")
    class2_inh_output = field_for(rows, "class2_inh_syn22")
    class2_soma = field_for(rows, "class2_soma2")
    class2_ltz_potential = field_for(rows, "class2_ltz_potential")
    source3 = field_for(rows, "input3")

    output_text = (project / "output_data.txt").read_text(encoding="utf-8").strip()
    output_rows = [[int(value) for value in line.split()] for line in output_text.splitlines() if line.strip()]
    if len(output_rows) != len(WINDOWS):
        raise RuntimeError(f"{project}: expected four classification rows, found {len(output_rows)}")

    window_results = []
    for index, start, end in WINDOWS:
        spikes = [read_edges(rows, field, start, end) for field in ltz_fields]
        inhibitory_arrivals = read_edges(rows, class2_inh_input, start, end)
        window_results.append({
            "window": index + 1,
            "range_seconds": [start, end],
            "output_bits": output_rows[index],
            "ltz_edges_seconds_by_class": spikes,
            "class2_inh_synapse_2_input_edges_seconds": inhibitory_arrivals,
            "source3_edges_seconds": read_edges(rows, source3, start, end),
        })

    class3_window = [row for row in rows if 4.0 <= float(row["model_time"]) < 6.0]
    tip_values = [(float(row["model_time"]), float(row[class2_tip])) for row in class3_window]
    tip_min = min(tip_values, key=lambda pair: pair[1])
    tip_max = max(tip_values, key=lambda pair: pair[1])
    inhibition_values = [(float(row["model_time"]), float(row[class2_inh_output])) for row in class3_window]
    competition_interval = [row for row in rows if 4.3 <= float(row["model_time"]) < 4.4]
    soma_values = [(float(row["model_time"]), float(row[class2_soma])) for row in competition_interval]
    ltz_potential_values = [(float(row["model_time"]), float(row[class2_ltz_potential])) for row in competition_interval]
    key_times = (4.3055, 4.3275, 4.347, 4.3565, 4.374, 4.384)
    samples_at_key_times = []
    for target_time in key_times:
        row = min(rows, key=lambda sample: abs(float(sample["model_time"]) - target_time))
        samples_at_key_times.append({
            "target_time": target_time,
            "sample_time": float(row["model_time"]),
            "tip_sum_potential": float(row[class2_tip]),
            "soma2_sum_potential": float(row[class2_soma]),
            "inhibitory_input_copy": float(row[class2_inh_input]),
            "inhibitory_synapse_output": float(row[class2_inh_output]),
        })
    return {
        "mode": mode,
        "variant": label,
        "class2_branch_2_length": length,
        "trace_samples": len(rows),
        "last_model_time": float(rows[-1]["model_time"]),
        "classification_outputs": output_rows,
        "windows": window_results,
        "class3_competition_window": {
            "class2_dendrite_tip_sum_potential_min": {"time": tip_min[0], "value": tip_min[1]},
            "class2_dendrite_tip_sum_potential_max": {"time": tip_max[0], "value": tip_max[1]},
            "class2_dendrite_tip_sum_potential_range_4_3_to_4_5": [
                min(float(row[class2_tip]) for row in competition_interval),
                max(float(row[class2_tip]) for row in competition_interval),
            ],
            "class2_soma2_sum_potential_peak_4_3_to_4_4": max(soma_values, key=lambda pair: pair[1]),
            "class2_ltz_output_potential_peak_4_3_to_4_4": max(ltz_potential_values, key=lambda pair: pair[1]),
            "key_time_samples": samples_at_key_times,
            "class2_inh_synapse_2_output_peak": max(inhibition_values, key=lambda pair: abs(pair[1])),
            "class2_ltz_edges": read_edges(rows, ltz_fields[1], 4.0, 6.0),
            "class3_ltz_edges": read_edges(rows, ltz_fields[2], 4.0, 6.0),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = [
        summarize(args.input_root, mode, label, length)
        for mode in ("on", "off")
        for label, length in VARIANTS.items()
    ]
    json_path = args.input_root / "dendrite_length_summary.json"
    csv_path = args.input_root / "dendrite_length_summary.csv"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("mode", "length_variant", "dendrite_length", "window", "output_bits", "class1_edges", "class2_edges", "class3_edges", "class2_brake_arrivals"))
        for run in result:
            for window in run["windows"]:
                edge_sets = window["ltz_edges_seconds_by_class"]
                writer.writerow((
                    run["mode"], run["variant"], run["class2_branch_2_length"], window["window"],
                    "".join(str(bit) for bit in window["output_bits"]),
                    len(edge_sets[0]), len(edge_sets[1]), len(edge_sets[2]),
                    len(window["class2_inh_synapse_2_input_edges_seconds"]),
                ))
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    main()
