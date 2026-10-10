#!/usr/bin/env python3
"""Prepare and run controlled TimeLearner experiment waves.

This module only prepares immutable experiment inputs, starts the existing C++
trainer through posttune_verify.py, and summarizes its outputs. Learning logic
remains in NeuroModelerConsole.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
MANIFEST = BASE / "TimeLearnerMatrix" / "matrix.json"
RUNS = BASE / "_repro" / "TimeLearnerMatrixRuns"
PV_PATH = BASE / "scripts" / "posttune_verify.py"
CLASS_TAGS = ("NeuronClassName", "MembraneClassName", "SynapseClassName")
INHIBITION_TAGS = ("UsePresynapticInhibition", "InhibitionCoeff")
XML_INPUTS = ("Model_00.xml", "Parameters_00.xml")
TAG_RE = r"(<{tag}\b[^>]*>)(.*?)(</{tag}\s*>)"


def load_pv():
    spec = importlib.util.spec_from_file_location("posttune_verify_matrix", PV_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {PV_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tag_values(text: str, tag: str) -> list[str]:
    pattern = re.compile(TAG_RE.format(tag=re.escape(tag)), re.S)
    return [m.group(2).strip() for m in pattern.finditer(text)]


def set_tag_values(text: str, tag: str, values: list[str]) -> str:
    pattern = re.compile(TAG_RE.format(tag=re.escape(tag)), re.S)
    found = 0

    def replace(match):
        nonlocal found
        if found >= len(values):
            raise ValueError(f"too many {tag} nodes")
        value = values[found]
        found += 1
        return match.group(1) + value + match.group(3)

    result = re.sub(pattern, replace, text)
    if found != len(values):
        raise ValueError(f"{tag}: replaced {found}, expected {len(values)}")
    return result


def set_all_tags(text: str, tag: str, value: str, *, required: bool = True) -> str:
    vals = tag_values(text, tag)
    if required and not vals:
        raise ValueError(f"required XML tag missing: {tag}")
    return set_tag_values(text, tag, [value] * len(vals)) if vals else text


def toggle_inhibition(base_text: str, template_text: str, enabled: bool, coeff: float, *, require_flags: bool = False) -> str:
    out = base_text
    for tag in CLASS_TAGS:
        base_values = tag_values(base_text, tag)
        template_values = tag_values(template_text, tag)
        if len(base_values) != len(template_values):
            raise ValueError(f"{tag} node count differs: {len(base_values)} vs {len(template_values)}")
        mapped = []
        for base_value, template_value in zip(base_values, template_values):
            if enabled:
                mapped.append(template_value if "Preinh" in template_value else base_value)
            else:
                mapped.append(re.sub(r"Preinh[0-9]+_[0-9]+", "", base_value))
        out = set_tag_values(out, tag, mapped)
    expected_use = "1" if enabled else "0"
    expected_coeff = format(coeff if enabled else 0.0, ".17g")
    for tag, value in (("UsePresynapticInhibition", expected_use), ("InhibitionCoeff", expected_coeff)):
        vals = tag_values(out, tag)
        if not vals:
            if require_flags:
                raise ValueError(f"required inhibition tag missing: {tag}")
            continue
        out = set_all_tags(out, tag, value)
    return out


def prepare_case(spec: dict[str, Any], templates: dict[str, Any], pv, *, refresh: bool = False) -> dict[str, Any]:
    case_id = spec["id"]
    template = templates[spec["template"]]
    source = BASE / template.get("paired_source", template["preinh_source"])
    preinh_source = BASE / template["preinh_source"]
    destination = BASE / "TimeLearnerMatrix" / spec["wave"] / "inputs" / case_id
    if destination.exists():
        saved = destination / "matrix_input_manifest.json"
        if saved.is_file() and not refresh:
            old = json.loads(saved.read_text(encoding="utf-8"))
            if old.get("factors") == {k: v for k, v in spec.items() if k not in ("id", "wave")}:
                return old
            raise RuntimeError(f"config factors changed; use --refresh to regenerate {destination}")
        if not saved.is_file():
            raise FileExistsError(f"refusing to overwrite incomplete config snapshot: {destination}")
    if not source.is_dir() or not preinh_source.is_dir():
        raise FileNotFoundError(f"missing source/template for {case_id}: {source} / {preinh_source}")

    copied = []
    for side in ("Train", "Test"):
        dst_side = destination / side
        dst_side.mkdir(parents=True, exist_ok=True)
        for rel in pv.ALLOWLIST_INPUTS:
            src_file = source / side / rel
            companion = preinh_source / side / rel
            if not src_file.is_file():
                raise FileNotFoundError(src_file)
            shutil.copy2(src_file, dst_side / rel)
            if rel.endswith(".xml"):
                text = src_file.read_text(encoding="utf-8")
                if rel in XML_INPUTS:
                    if not companion.is_file():
                        raise FileNotFoundError(companion)
                    text = toggle_inhibition(
                        text,
                        companion.read_text(encoding="utf-8"),
                        bool(spec["presynaptic_inhibition"]),
                        float(spec.get("presynaptic_coefficient", 2.5)),
                        require_flags=(side == "Train"),
                    )
                    text = set_all_tags(text, "NormalizationMode", str(spec["normalization_mode"]))
                    if side == "Train":
                        from repro_cold_lib import ensure_tag_after, set_tag
                        enabled = "1" if spec.get("posttrain_tuning", False) else "0"
                        text = ensure_tag_after(text, "IsNeedToTrain", "EnablePostTrainTuning", enabled)
                        text = set_tag(text, "EnablePostTrainTuning", enabled, 1)
                        text = ensure_tag_after(text, "IterationGap", "AutoScaleIterationGap", "1")
                        text = set_tag(text, "AutoScaleIterationGap", "1", 1)
                        if enabled == "1":
                            tip_mode = str(spec.get("tipr_mode", 1))
                            text = ensure_tag_after(text, "EnablePostTrainTuning", "EnablePostTrainMidThreshold", "1")
                            text = set_tag(text, "EnablePostTrainMidThreshold", "1", 1)
                            text = ensure_tag_after(text, "EnablePostTrainMidThreshold", "PostTrainTipResistanceMode", tip_mode, ' Type="i" PType="257" IoType="17"')
                            text = set_tag(text, "PostTrainTipResistanceMode", tip_mode, 1)
                            text = ensure_tag_after(text, "PostTrainTipResistanceMode", "PostTrainSilentThreshold", "1", ' Type="d" PType="257" IoType="17"')
                            text = set_tag(text, "PostTrainSilentThreshold", "1", 1)
                ET.fromstring(text)
                (dst_side / rel).write_text(text, encoding="utf-8")
            copied.append({"side": side, "file": rel, "sha256": sha256(dst_side / rel)})
        for pattern in pv.ALLOWLIST_OPTIONAL_GLOBS:
            for src_file in sorted((source / side).glob(pattern)):
                if src_file.is_file():
                    shutil.copy2(src_file, dst_side / src_file.name)
                    copied.append({"side": side, "file": src_file.name, "sha256": sha256(dst_side / src_file.name)})

    def git_head(path: Path) -> str | None:
        try:
            return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        except Exception:
            return None

    pulse = BASE.parents[2] / "Libraries" / "Nmsdk-PulseLib"
    record = {
        "case": case_id,
        "wave": spec["wave"],
        "factors": {k: v for k, v in spec.items() if k not in ("id", "wave")},
        "source": str(source.relative_to(BASE)),
        "legacy_noninhibited_template": template["source"],
        "presynaptic_class_template": str(preinh_source.relative_to(BASE)),
        "source_files": copied,
        "source_commits": {
            "root": git_head(BASE.parents[2].parent),
            "Bin": git_head(BASE.parents[2]),
            "PulseLib": git_head(pulse),
        },
        "console_sha256": sha256(pv.NM) if Path(pv.NM).is_file() else None,
        "matrix_definition_sha256": sha256(MANIFEST),
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Each matched pair starts from the same historical presynaptic-inhibition topology, segment lengths and fixed threshold. The off arm strips the inhibition class suffix and clears inhibition flags; only inhibition and NormalizationMode differ within a pair.",
    }
    (destination / "matrix_input_manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported matrix manifest schema")
    return data


def prepare_wave(wave: str, *, refresh: bool = False) -> None:
    pv = load_pv()
    data = load_manifest()
    specs = [case for case in data["cases"] if case["wave"] == wave]
    if not specs:
        raise ValueError(f"no cases in manifest for {wave}")
    templates = data["templates"]
    prepared = []
    for spec in specs:
        prepared.append(prepare_case(spec, templates, pv, refresh=refresh))
    print(json.dumps({"wave": wave, "prepared": len(prepared), "cases": [x["case"] for x in prepared]}, indent=2))


def worker(wave: str, case_id: str) -> int:
    pv = load_pv()
    data = load_manifest()
    spec = next((c for c in data["cases"] if c["wave"] == wave and c["id"] == case_id), None)
    if spec is None:
        raise ValueError(f"unknown case {wave}/{case_id}")
    input_root = BASE / "TimeLearnerMatrix" / wave / "inputs" / case_id
    if not input_root.is_dir():
        raise FileNotFoundError(f"input snapshot missing; run --prepare {wave}: {input_root}")
    template = data["templates"][spec["template"]]
    gold = BASE / template.get("paired_source", template["preinh_source"])
    pv.CASES[case_id] = {
        "root": input_root,
        "gold": gold,
        "train_t": float(spec.get("train_t", template["train_t"])),
        "span_ms": int(spec["duration_ms"]),
        "kind": template["kind"],
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
        "normalization_mode": int(spec["normalization_mode"]),
        "presynaptic_inhibition": bool(spec["presynaptic_inhibition"]),
        "presynaptic_coefficient": float(spec.get("presynaptic_coefficient", 2.5)),
        "enable_posttrain_tuning": bool(spec.get("posttrain_tuning", True)),
        "posttrain_tip_resistance_mode": str(spec.get("tipr_mode", 1)),
    }
    result_dir = RUNS / wave
    result_dir.mkdir(parents=True, exist_ok=True)
    run_dir = result_dir / case_id
    run_dir.mkdir(parents=True, exist_ok=True)
    result = pv.run_case(case_id, run_dir=run_dir)
    result["matrix_factors"] = {k: v for k, v in spec.items() if k not in ("id",)}
    result["input_manifest"] = str(input_root / "matrix_input_manifest.json")
    result_path = run_dir / "matrix_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if not result.get("row_fail") else 1


def run_wave(wave: str, jobs: int) -> int:
    data = load_manifest()
    specs = [case for case in data["cases"] if case["wave"] == wave]
    if not specs:
        raise ValueError(f"no cases in manifest for {wave}")
    missing = [s["id"] for s in specs if not (BASE / "TimeLearnerMatrix" / wave / "inputs" / s["id"]).is_dir()]
    if missing:
        raise FileNotFoundError(f"inputs not prepared: {missing}; run --prepare {wave}")
    run_dir = RUNS / wave
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "wave_status.json"
    if status_path.is_file():
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["jobs"] = jobs
    else:
        status = {
            "wave": wave,
            "jobs": jobs,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "cases": {},
        }
    for spec in specs:
        case_id = spec["id"]
        saved_result = run_dir / case_id / "matrix_result.json"
        status.setdefault("cases", {})[case_id] = (
            {"status": "completed", "result_file": str(saved_result.relative_to(BASE)), "resumed": True}
            if saved_result.is_file()
            else {"status": "queued"}
        )
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    def launch(spec: dict[str, Any]) -> tuple[str, int]:
        case_id = spec["id"]
        log_path = run_dir / f"{case_id}.log"
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", wave, case_id]
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.run(command, cwd=BASE, stdout=log, stderr=subprocess.STDOUT, text=True)
        return case_id, int(proc.returncode)

    rc = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(jobs, len(specs)))) as pool:
        pending = [spec for spec in specs if not (run_dir / spec["id"] / "matrix_result.json").is_file()]
        futures = {pool.submit(launch, spec): spec["id"] for spec in pending}
        for future in concurrent.futures.as_completed(futures):
            case_id, code = future.result()
            result_file = run_dir / case_id / "matrix_result.json"
            has_result = result_file.is_file()
            status["cases"][case_id] = {
                "status": "completed" if has_result else "worker_infrastructure_error",
                "worker_exit_code": code,
                "result_file": str(result_file.relative_to(BASE)) if has_result else None,
                "log_file": str((run_dir / f"{case_id}.log").relative_to(BASE)),
                "finished_utc": datetime.now(timezone.utc).isoformat(),
            }
            status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
            print(f"{case_id}: worker_exit={code}")
            if not has_result:
                rc = 2
    status["finished_utc"] = datetime.now(timezone.utc).isoformat()
    status["run_complete"] = rc == 0 and all(
        (run_dir / spec["id"] / "matrix_result.json").is_file() for spec in specs
    )
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wave", nargs="?")
    parser.add_argument("--prepare", metavar="WAVE", help="prepare immutable input snapshots for a wave")
    parser.add_argument("--run", metavar="WAVE", help="run a prepared wave")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--refresh", action="store_true", help="regenerate an existing input snapshot after an explicit design change")
    parser.add_argument("--worker", nargs=2, metavar=("WAVE", "CASE"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(*args.worker)
    if args.prepare:
        prepare_wave(args.prepare, refresh=args.refresh)
        return 0
    if args.run:
        return run_wave(args.run, args.jobs)
    parser.error("use --prepare WAVE or --run WAVE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
