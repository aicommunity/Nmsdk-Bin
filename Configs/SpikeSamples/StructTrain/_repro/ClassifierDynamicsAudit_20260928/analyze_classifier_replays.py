#!/usr/bin/env python3
"""Validate output_data bits against LTZone edges in the synthetic replay CSVs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WINDOWS = ((0.0, 2.0), (2.0, 4.0), (4.0, 6.0), (6.0, 8.01))
THRESHOLDS = (("00060", 0.006), ("00085", 0.0085))


def read_output(path: Path) -> list[list[int]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append([int(float(value)) for value in line.split()])
    if any(len(row) != 3 for row in rows):
        raise ValueError(f"Expected three output bits in each row: {path}")
    return rows


def read_trace(path: Path) -> tuple[list[dict[str, float]], dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        aliases: dict[str, str] = {}
        for index, title in enumerate(header):
            if title == "model_time":
                aliases[title] = ""
                continue
            alias, separator, source = title.partition(" [")
            if not separator or not source.endswith("]"):
                raise ValueError(f"Missing component path in CSV column {title!r}")
            aliases[alias] = source[:-1]
        rows = [{name: float(value) for name, value in zip(aliases, raw)} for raw in reader]
    return rows, aliases


def edges(rows: list[dict[str, float]], signal: str) -> list[float]:
    return [
        rows[index]["model_time"]
        for index in range(1, len(rows))
        if rows[index - 1][signal] < 0.5 <= rows[index][signal]
    ]


def in_window(times: list[float], start: float, end: float) -> list[float]:
    return [time for time in times if start <= time < end]


def signal_path(aliases: dict[str, str], alias: str, suffix: str) -> None:
    actual = aliases.get(alias, "")
    if not actual.endswith(suffix):
        raise ValueError(f"{alias} points to {actual!r}, expected a path ending in {suffix!r}")


def summarize_window_rows(threshold: str, mode: str, output: list[list[int]],
                          trace: list[dict[str, float]]) -> list[dict[str, object]]:
    events = {class_id: edges(trace, f"NeuronTrainer{class_id}_ltz") for class_id in (1, 2, 3)}
    result = []
    for window_index, (start, end) in enumerate(WINDOWS):
        counts = {class_id: len(in_window(times, start, end)) for class_id, times in events.items()}
        actual_bits = [int(counts[class_id] > 0) for class_id in (1, 2, 3)]
        if output[window_index] != actual_bits:
            raise ValueError(
                f"output_data disagrees with LTZone edges for threshold={threshold}, mode={mode}, "
                f"window={window_index + 1}: file={output[window_index]}, edges={actual_bits}"
            )
        result.append({
            "threshold": float(threshold),
            "inhibition": mode,
            "input_window": window_index + 1,
            "start_s": start,
            "end_s": end,
            "output_bits": "".join(map(str, output[window_index])),
            "class1_spikes": counts[1],
            "class2_spikes": counts[2],
            "class3_spikes": counts[3],
        })
    return result


def competition_case(trace: list[dict[str, float]], aliases: dict[str, str],
                     source_class: int, start: float, end: float, label: str) -> dict[str, object]:
    source = f"NeuronTrainer{source_class}_ltz"
    synapse_index = 1 if source_class == 1 else 2
    syn_input = f"class2_inh_syn{synapse_index}input1"
    syn_output = f"class2_inh_syn{synapse_index}1"
    channel = "class2_inh_channel1"
    target_potential = "class2_ltz_potential"
    target_output = "NeuronTrainer2_ltz"
    signal_path(aliases, source, f"NeuronTrainer{source_class}.Neuron.LTZone.Output")
    signal_path(aliases, syn_input, f"NeuronTrainer2.Neuron.Soma1.InhSynapse{synapse_index}.OutInCopy")
    signal_path(aliases, syn_output, f"NeuronTrainer2.Neuron.Soma1.InhSynapse{synapse_index}.Output")

    source_edges = in_window(edges(trace, source), start, end)
    inhibition_edges = in_window(edges(trace, syn_input), start, end)
    target_edges = in_window(edges(trace, target_output), start, end)
    region = [row for row in trace if start <= row["model_time"] < end]
    post_source = [row for row in region if row["model_time"] >= (max(source_edges) + 0.05 if source_edges else end)]
    return {
        "case": label,
        "source_class": source_class,
        "window_s": [start, end],
        "source_spikes_s": source_edges,
        "inhibitory_input_edges_s": inhibition_edges,
        "target_class2_spikes_s": target_edges,
        "synapse_peak_conductance": max((row[syn_output] for row in region), default=0.0),
        "class2_ltz_potential_peak": max((row[target_potential] for row in region), default=0.0),
        "class2_ltz_potential_peak_after_source_plus_50ms": max(
            (row[target_potential] for row in post_source), default=0.0
        ),
        "class2_inhibitory_channel_min": min((row[channel] for row in region), default=0.0),
        "bit_is_latched_from_target_spikes": bool(target_edges),
    }


def main() -> None:
    window_rows: list[dict[str, object]] = []
    for token, threshold in THRESHOLDS:
        for mode in ("On", "Off"):
            name = f"NSpikeClassifier_Synthetic_Outputs{mode}_Threshold{token}_20260928"
            output = read_output(ROOT / name / "output_data.txt")
            trace_path = next((ROOT / name / "ClassifierDynamics").glob("*.csv"))
            trace, aliases = read_trace(trace_path)
            if len(output) != 4:
                raise ValueError(f"Expected four output windows in {name}; found {len(output)}")
            window_rows.extend(summarize_window_rows(f"{threshold:g}", mode, output, trace))

    output_csv = ROOT / "classifier_window_summary.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(window_rows[0]))
        writer.writeheader()
        writer.writerows(window_rows)

    competition = {}
    for mode in ("On", "Off"):
        name = f"NSpikeClassifier_AllProbesCompetition_Dynamics{mode}_Threshold0006_20260928"
        trace_path = next((ROOT / name / "ClassifierDynamicsCompetition").glob("*.csv"))
        trace, aliases = read_trace(trace_path)
        for class_id in (1, 2, 3):
            signal_path(aliases, f"NeuronTrainer{class_id}_ltz",
                        f"NeuronTrainer{class_id}.Neuron.LTZone.Output")
        competition[mode] = {
            "third_clean_pattern_class3_to_class2": competition_case(
                trace, aliases, 3, 4.0, 6.0, "third_clean_pattern_class3_to_class2"
            ),
            "midpoint_class1_to_class2": competition_case(
                trace, aliases, 1, 6.0, 8.01, "midpoint_class1_to_class2"
            ),
        }
    (ROOT / "competition_timing_summary.json").write_text(
        json.dumps(competition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output_csv)
    print(ROOT / "competition_timing_summary.json")


if __name__ == "__main__":
    main()
