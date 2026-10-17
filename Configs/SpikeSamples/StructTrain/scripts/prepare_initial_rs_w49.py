#!/usr/bin/env python3
"""Prepare the isolated 20-case initial-Rs diagnostic batch W49.

This is experiment preparation only. The registered 312-case matrix remains
unchanged, and all learning state changes are performed by the C++ trainers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
OFFICIAL_MATRIX = BASE / "TimeLearnerMatrix"
DIAGNOSTIC_MATRIX = OFFICIAL_MATRIX / "diagnostics" / "initial_rs_ratio_w49"


def build_registry() -> dict[str, Any]:
    official = json.loads((OFFICIAL_MATRIX / "matrix.json").read_text(encoding="utf-8"))
    source_ids = {
        "classic": ("W02_CL100_N1_PSIoff", "W02_CL100_N1_PSI25"),
        "branch": ("W04_BR100_N1_PSIoff", "W04_BR100_N1_PSI25"),
    }
    by_id = {case["id"]: case for case in official["cases"]}
    ratios = {
        "classic": (1, 10, 30, 100),
        "branch": (1, 10, 30, 100, 300, 1000),
    }
    cases: list[dict[str, Any]] = []
    for trainer_group in ("classic", "branch"):
        for ratio in ratios[trainer_group]:
            for source_id in source_ids[trainer_group]:
                case = dict(by_id[source_id])
                prefix = "CL" if trainer_group == "classic" else "BR"
                psi = "PSI25" if case["presynaptic_inhibition"] else "PSIoff"
                case["id"] = f"W49_{prefix}100_N1_{psi}_RS{ratio}RM"
                case["wave"] = "W49"
                case["initial_rs_trainable_to_rm"] = float(ratio)
                case["description_ru"] = (
                    f"Диагностика W49: {case['trainer']}, паттерн 100 мс, "
                    f"параметрическая нормализация; начальный Rs/Rm={ratio} "
                    f"только на трёх обучаемых входах, reference anchor и "
                    f"SynapseResistanceBase сохранены на исторических 86 МОм; "
                    f"PSI {'2.5' if case['presynaptic_inhibition'] else 'выключено'}."
                )
                cases.append(case)
    if len(cases) != 20 or len({case["id"] for case in cases}) != 20:
        raise RuntimeError("W49 must contain exactly 20 unique experiment cases")
    template_names = {case["template"] for case in cases}
    return {
        "schema": official["schema"],
        "diagnostic_only": True,
        "purpose_ru": (
            "Изолировать влияние стартового Rs трёх настраиваемых входов на "
            "синхронизацию и результат обучения; последний вход является "
            "reference anchor и остаётся равен SynapseResistanceBase=86 МОм."
        ),
        "source_matrix_sha256": hashlib.sha256(
            (OFFICIAL_MATRIX / "matrix.json").read_bytes()
        ).hexdigest(),
        "queue_order": ["W49"],
        "waves": {
            "W49": {
                "title": "Стартовое Rs/Rm только на обучаемых входах: Classic100 и Branch100, PSI off/on"
            }
        },
        "templates": {
            name: official["templates"][name] for name in sorted(template_names)
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="write immutable W49 Train/Test snapshots")
    parser.add_argument("--refresh", action="store_true", help="refresh only existing W49 input snapshots")
    args = parser.parse_args()
    if args.refresh and not args.prepare:
        parser.error("--refresh requires --prepare")
    DIAGNOSTIC_MATRIX.mkdir(parents=True, exist_ok=True)
    manifest = DIAGNOSTIC_MATRIX / "matrix.json"
    expected = build_registry()
    if manifest.exists():
        existing = json.loads(manifest.read_text(encoding="utf-8"))
        if existing != expected and not args.refresh:
            raise SystemExit(f"refusing to replace a changed W49 manifest: {manifest}")
    if not manifest.exists() or args.refresh:
        manifest.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"matrix": str(manifest), "cases": len(expected["cases"])}, ensure_ascii=False))
    if args.prepare:
        os.environ["TIMELEARNER_MATRIX_DIR"] = str(DIAGNOSTIC_MATRIX.resolve())
        scripts = Path(__file__).resolve().parent
        sys.path.insert(0, str(scripts))
        import timelearner_matrix

        timelearner_matrix.prepare_wave("W49", refresh=args.refresh)
        # The preparation host may have an unrelated Console build. The actual
        # executable SHA is recorded by the queue's immutable run manifest.
        for case in expected["cases"]:
            input_manifest = (
                DIAGNOSTIC_MATRIX / "W49" / "inputs" / case["id"]
                / "matrix_input_manifest.json"
            )
            data = json.loads(input_manifest.read_text(encoding="utf-8"))
            data["console_sha256"] = None
            data["note"] = (
                str(data.get("note", "")).rstrip()
                + " Console SHA is captured per execution in run_manifest.json; "
                "this input snapshot is independent of the preparation host binary."
            )
            input_manifest.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
