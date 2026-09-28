#!/usr/bin/env python3
"""Validate and compare paired historical/new LTZone-threshold replay pools."""

from __future__ import annotations

import argparse
import csv
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from analyze_burst_replays import analyze


HERE = Path(__file__).resolve().parent
REPRO = HERE.parent


def verify_ltz_links(project: Path, expected_threshold: float) -> None:
    root = ET.parse(project / "Model_00.xml").getroot()
    model = root.find("./Model")
    if model is None:
        raise ValueError(f"{project}: serialized model missing")
    recorder = model.find("./Components/ClassifierDynamicsRecorder")
    if recorder is None:
        raise ValueError(f"{project}: ClassifierDynamicsRecorder missing")
    aliases = recorder.findtext("./Parameters/SignalNamesCsv", "").split(",")
    source_links = []
    for link in model.findall("./Links/elem"):
        if any(
            item.get("Name") == "Signals" and (item.text or "").strip() == recorder.tag
            for item in link.findall("./Connector")
        ):
            source = link.find("./Item")
            if source is None:
                raise ValueError(f"{project}: recorder link without source")
            source_links.append((source.text or "").strip())
    expected = [
        f"SpikeClassifier.NeuronTrainer{index}.Neuron.LTZone"
        for index in range(1, 4)
    ]
    actual = [source for alias, source in zip(aliases, source_links)
              if alias.lower().endswith("_ltz")]
    if actual != expected or len(source_links) != len(aliases):
        raise ValueError(f"{project}: unexpected recorder outputs {actual}; expected {expected}")
    with (project / "signals.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream))
    recorded = {column.partition(" [")[0]: column for column in header[1:]}
    for index, alias in enumerate(aliases):
        if not alias.lower().endswith("_ltz"):
            continue
        expected_column = f"[Model.{expected[index]}.Output]"
        if expected_column not in recorded.get(alias, ""):
            raise ValueError(
                f"{project}: CSV column for {alias} does not resolve to {expected_column}: "
                f"{recorded.get(alias)}"
            )

    zones = [component for component in model.iter()
             if component.get("Class") == "NPulseLTZoneThreshold"]
    zone_thresholds = [float(component.findtext("./Parameters/Threshold", "nan"))
                       for component in zones]
    if not zone_thresholds or any(
        not math.isclose(value, expected_threshold, rel_tol=0.0, abs_tol=1e-12)
        for value in zone_thresholds
    ):
        raise ValueError(f"{project}: LTZone thresholds {zone_thresholds}, expected {expected_threshold}")


def project_key(name: str, threshold_label: str) -> str:
    suffix = f"_Threshold{threshold_label}_20260928"
    if not name.endswith(suffix):
        raise ValueError(f"Unexpected threshold-pool project name: {name}")
    return name[:-len(suffix)]


def add_expected_classes(project: Path, result: dict[str, object]) -> None:
    expected_path = project / "expected_classes.csv"
    if not expected_path.is_file():
        raise ValueError(f"{project}: expected_classes.csv is missing")
    with expected_path.open("r", encoding="utf-8-sig", newline="") as stream:
        expected_rows = list(csv.DictReader(stream))
    outputs = str(result["output_bits"]).split(";") if result["output_bits"] else []
    if len(expected_rows) != len(outputs):
        raise ValueError(f"{project}: expected labels and output rows differ in length")
    width = len(outputs[0]) if outputs else 0
    expected_bits = []
    correct = 0
    for label_row, output in zip(expected_rows, outputs):
        class_id = int(label_row["expected_class"])
        if class_id == 0:
            target = "0" * width
        elif 1 <= class_id <= width:
            target = "".join("1" if index == class_id else "0" for index in range(1, width + 1))
        else:
            raise ValueError(f"{project}: expected class {class_id} exceeds output width {width}")
        expected_bits.append(target)
        correct += output == target
    result["expected_bits"] = ";".join(expected_bits)
    result["strict_correct_rows"] = correct
    result["strict_accuracy"] = f"{correct}/{len(outputs)}"


def collect_pool(root: Path, label: str, threshold: float) -> dict[str, dict[str, object]]:
    pool: dict[str, dict[str, object]] = {}
    for project in sorted(root.iterdir()):
        if not project.is_dir() or not project.name.startswith((
            "NSpikeSynapseCount_", "NSpikeClassifier_AllProbes_", "NSpikeDendriteLength_",
            "NSpikeClassifier_Iris10_", "NSpikeClassifier_Iris3Prototypes_",
            "NSpikeClassifier_SyntheticOutputs_",
        )):
            continue
        if not (project / "output_data.txt").is_file() or not (project / "signals.csv").is_file():
            raise ValueError(f"{project}: incomplete replay output")
        verify_ltz_links(project, threshold)
        result = analyze(project)
        add_expected_classes(project, result)
        expected_rows = result["output_rows"]
        if expected_rows == 0 or result["output_rows_compared"] != expected_rows:
            raise ValueError(f"{project}: incomplete classifier output windows, got {result}")
        if result["output_bits_match_trace"] != expected_rows:
            raise ValueError(f"{project}: classifier outputs do not match LTZone edges: {result}")
        key = project_key(project.name, label)
        result["threshold_pool"] = label
        pool[key] = result

    if not pool:
        raise ValueError(f"No projects found in {root}")
    with (root / "burst_replay_summary.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = list(next(iter(pool.values())).keys())
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(pool[key] for key in sorted(pool))
    return pool


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, default=REPRO / "BurstReplayHistorical_20260928")
    parser.add_argument("--new-root", type=Path, default=REPRO / "BurstReplayVerified_20260928")
    parser.add_argument("--output", type=Path, default=REPRO / "classifier_threshold_comparison.csv")
    args = parser.parse_args()

    historical = collect_pool(args.historical_root, "00047", 0.0047)
    new = collect_pool(args.new_root, "00085", 0.0085)
    if set(historical) != set(new):
        raise ValueError(
            f"Paired pools differ: only historical={sorted(set(historical)-set(new))}; "
            f"only new={sorted(set(new)-set(historical))}"
        )

    fields = [
        "experiment", "historical_threshold", "historical_outputs", "historical_primary_edges_by_row",
        "historical_expected", "historical_strict_accuracy", "historical_max_edges_any_signal",
        "historical_burst_signals", "new_threshold", "new_outputs", "new_expected", "new_strict_accuracy",
        "new_primary_edges_by_row", "new_max_edges_any_signal", "new_burst_signals",
        "historical_bits_match_trace", "new_bits_match_trace",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for key in sorted(historical):
            old, current = historical[key], new[key]
            writer.writerow({
                "experiment": key,
                "historical_threshold": "0.0047",
                "historical_outputs": old["output_bits"],
                "historical_primary_edges_by_row": old["primary_edge_counts_by_row"],
                "historical_expected": old["expected_bits"],
                "historical_strict_accuracy": old["strict_accuracy"],
                "historical_max_edges_any_signal": old["max_edges_any_signal_window"],
                "historical_burst_signals": old["burst_signals"] or "none",
                "new_threshold": "0.0085",
                "new_outputs": current["output_bits"],
                "new_expected": current["expected_bits"],
                "new_strict_accuracy": current["strict_accuracy"],
                "new_primary_edges_by_row": current["primary_edge_counts_by_row"],
                "new_max_edges_any_signal": current["max_edges_any_signal_window"],
                "new_burst_signals": current["burst_signals"] or "none",
                "historical_bits_match_trace": old["output_bits_match_trace"],
                "new_bits_match_trace": current["output_bits_match_trace"],
            })

    print(f"Validated {len(historical)} paired experiments; wrote {args.output}")
    for key in sorted(historical):
        old, current = historical[key], new[key]
        print(
            f"{key}: 0.0047 max_edges={old['max_edges_any_signal_window']} "
            f"bursts={'yes' if old['burst_signals'] else 'no'} "
            f"correct={old['strict_accuracy']} outputs={old['output_bits']} | "
            f"0.0085 max_edges={current['max_edges_any_signal_window']} "
            f"bursts={'yes' if current['burst_signals'] else 'no'} "
            f"correct={current['strict_accuracy']} outputs={current['output_bits']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
