#!/usr/bin/env python3
"""Evaluate NSpikeClassifier's three-bit Iris output without inventing a winner.

The C++ classifier implements competition through lateral inhibitory links, but
TreatDataFromFile writes a cumulative bit for every LTZone that was active at
any point in the sample window. A row with multiple bits is therefore
ambiguous; this script deliberately does not apply argmax or first-spike rules.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CLASS_ORDER = ("Iris-setosa", "Iris-versicolor", "Iris-virginica")


def read_numeric_rows(path: Path, expected_columns: int) -> list[list[float]]:
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_no, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) != expected_columns:
                raise ValueError(
                    f"{path}:{line_no}: expected {expected_columns} values, "
                    f"found {len(fields)}"
                )
            try:
                values = [float(field) for field in fields]
            except ValueError as exc:
                raise ValueError(f"{path}:{line_no}: invalid number") from exc
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"{path}:{line_no}: non-finite value")
            rows.append(values)
    return rows


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"row", "iris_id", "expected_class"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"{path}: required columns are {sorted(required)}")
        manifest = list(reader)

    for expected_row, item in enumerate(manifest, start=1):
        if int(item["row"]) != expected_row:
            raise ValueError(f"{path}: row numbers must be contiguous from 1")
        if item["expected_class"] not in CLASS_ORDER:
            raise ValueError(
                f"{path}: unsupported class {item['expected_class']!r} "
                f"at row {expected_row}"
            )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Iris output_data.txt using NSpikeClassifier's actual "
            "multi-neuron response semantics."
        )
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="directory containing input_data.txt and output_data.txt",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=SCRIPT_DIR / "iris_test_manifest.csv",
        help="CSV mapping input row order to Iris IDs and expected classes",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    manifest_path = args.manifest.resolve()
    input_path = project_dir / "input_data.txt"
    output_path = project_dir / "output_data.txt"

    try:
        inputs = read_numeric_rows(input_path, expected_columns=5)
        outputs = read_numeric_rows(output_path, expected_columns=3)
        manifest = read_manifest(manifest_path)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not (len(inputs) == len(outputs) == len(manifest)):
        print(
            "ERROR: row count mismatch: "
            f"inputs={len(inputs)}, outputs={len(outputs)}, manifest={len(manifest)}",
            file=sys.stderr,
        )
        return 1

    strict_correct = 0
    unique_wrong = 0
    no_response = 0
    ambiguous = 0
    expected_responded = 0

    print("row\tIris ID\texpected\tactive class neurons\tC++-compatible result")
    for index, (_, output_row, item) in enumerate(
        zip(inputs, outputs, manifest), start=1
    ):
        if any(value not in (0.0, 1.0) for value in output_row):
            print(
                f"ERROR: output row {index} must contain only 0/1 flags; "
                f"found {output_row}",
                file=sys.stderr,
            )
            return 1

        active = [
            class_name
            for class_name, flag in zip(CLASS_ORDER, output_row)
            if flag == 1.0
        ]
        expected = item["expected_class"]
        if expected in active:
            expected_responded += 1

        if len(active) == 1:
            decision = active[0]
            if decision == expected:
                strict_correct += 1
                result = "unique correct response"
            else:
                unique_wrong += 1
                result = "unique wrong response"
        elif not active:
            no_response += 1
            decision = "none"
            result = "no response"
        else:
            ambiguous += 1
            decision = ",".join(active)
            result = "ambiguous: multiple LTZones fired"

        print(
            f"{index}\t{item['iris_id']}\t{expected}\t"
            f"{decision}\t{result}"
        )

    total = len(manifest)
    print("\nSummary")
    print(f"Samples: {total}")
    print(f"Expected class neuron active: {expected_responded}/{total}")
    print(f"Unique correct response: {strict_correct}/{total}")
    print(f"Unique wrong response: {unique_wrong}")
    print(f"No response: {no_response}")
    print(f"Ambiguous multi-neuron response: {ambiguous}")

    # Exit 2 means the files were valid, but the experiment did not produce
    # exactly one correct active class for every sample.
    return 0 if strict_correct == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
