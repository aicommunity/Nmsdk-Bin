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
import fnmatch
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


def apply_xml_factors(
    text: str,
    spec: dict[str, Any],
    *,
    side: str | None = None,
    membrane_resistance: float | None = None,
) -> str:
    for tag, value in (spec.get("xml_overrides") or {}).items():
        if tag_values(text, str(tag)):
            text = set_all_tags(text, str(tag), str(value), required=True)
    for tag, factor in (spec.get("relative_overrides") or {}).items():
        values = tag_values(text, str(tag))
        if not values:
            continue
        updated = []
        for raw in values:
            value = float(raw.replace(",", ".")) * float(factor)
            updated.append(format(value, ".17g"))
        text = set_tag_values(text, str(tag), updated)
    if spec.get("initial_rs_to_rm") is not None and side == "Train":
        if membrane_resistance is None or membrane_resistance <= 0:
            raise ValueError("initial Rs experiment requires a positive membrane resistance")
        if tag_values(text, "SynapseResistanceBase"):
            rs = membrane_resistance * float(spec["initial_rs_to_rm"])
            text = set_all_tags(text, "SynapseResistanceBase", format(rs, ".17g"))
    if spec.get("reverse_pattern_order"):
        matrix_re = re.compile(r'(<MatrixData\b[^>]*Rows="4"[^>]*>)(.*?)(</MatrixData\s*>)', re.S)
        found = 0
        def reverse_matrix(match):
            nonlocal found
            found += 1
            values = match.group(2).split()
            if len(values) != 4:
                raise ValueError(f"expected four MatrixData values, got {len(values)}")
            return match.group(1) + "\n".join(reversed(values)) + match.group(3)
        text = matrix_re.sub(reverse_matrix, text)
    return text


def copy_historical_git_source(source_rel: str, destination: Path, commit: str) -> list[Path]:
    """Copy only runnable Train/Test inputs from an immutable Bin git snapshot."""
    bin_root = BASE.parents[2]
    git_source_path = f"Configs/SpikeSamples/StructTrain/{source_rel.replace('\\', '/')}"
    git_source = f"{commit}:{git_source_path}"
    listing = subprocess.check_output(
        ["git", "-C", str(bin_root), "ls-tree", "-r", "--name-only", git_source],
        text=True,
    ).splitlines()
    selected: list[Path] = []
    for git_path in listing:
        relative = Path(git_path.replace("/", os.sep))
        if not relative.parts or relative.parts[0] not in ("Train", "Test"):
            continue
        name = relative.name
        if name not in ("Model_00.xml", "Parameters_00.xml", "Project.ini", "Interface.xml") and not any(
            fnmatch.fnmatch(name, pattern) for pattern in ("Matrix*.xml", "Pack*.xml", "*.pack")
        ):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as out:
            subprocess.run(
                ["git", "-C", str(bin_root), "cat-file", "blob", f"{commit}:{git_source_path}/{git_path}"],
                stdout=out,
                check=True,
            )
        selected.append(relative)
    for side in ("Train", "Test"):
        if not (destination / side / "Project.ini").is_file():
            raise FileNotFoundError(f"historical snapshot lacks {side}/Project.ini: {source_rel}@{commit}")
    return selected


def toggle_inhibition(
    base_text: str,
    topology_text: str,
    enabled: bool,
    coeff: float,
    *,
    class_template_text: str | None = None,
    require_flags: bool = False,
    force_presynaptic_classes: bool = False,
) -> str:
    out = base_text
    class_template_text = class_template_text or topology_text
    for tag in CLASS_TAGS:
        base_values = tag_values(base_text, tag)
        topology_values = tag_values(topology_text, tag)
        coefficient_values = tag_values(class_template_text, tag)
        if len(base_values) != len(topology_values):
            raise ValueError(f"{tag} topology node count differs: {len(base_values)} vs {len(topology_values)}")
        coefficient_classes: dict[str, str] = {}
        for value in coefficient_values:
            value = value.strip()
            match = re.fullmatch(r"(.*)Preinh[0-9]+_[0-9]+", value)
            if match:
                prefix = match.group(1)
                previous = coefficient_classes.setdefault(prefix, value)
                if previous != value:
                    raise ValueError(f"multiple pre-inhibition classes for {prefix} in {tag}")
        mapped = []
        coeff_suffix = format(float(coeff), ".1f").replace(".", "_")
        for base_value, topology_value in zip(base_values, topology_values):
            base_value = base_value.strip()
            topology_value = topology_value.strip()
            if enabled:
                if force_presynaptic_classes and tag == "SynapseClassName":
                    current = re.fullmatch(r"(.*)Preinh[0-9]+_[0-9]+", base_value)
                    prefix = current.group(1) if current else base_value
                    target = f"{prefix}Preinh{coeff_suffix}"
                    if target not in coefficient_classes.values():
                        raise ValueError(f"no coefficient-specific class {target} for forced {tag} mapping")
                    mapped.append(target)
                    continue
                topology_preinh = re.fullmatch(r"(.*)Preinh[0-9]+_[0-9]+", topology_value)
                base_preinh = re.fullmatch(r"(.*)Preinh[0-9]+_[0-9]+", base_value)
                if topology_preinh or base_preinh:
                    prefix = (topology_preinh or base_preinh).group(1)
                    target = f"{prefix}Preinh{coeff_suffix}"
                    if target not in coefficient_classes.values():
                        if tag == "SynapseClassName":
                            raise ValueError(f"no coefficient-specific class {target} for {tag}")
                        mapped.append(topology_value)
                        continue
                    mapped.append(target)
                else:
                    mapped.append(base_value)
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
    source_rel = spec.get("source_config") or template.get("paired_source", template["preinh_source"])
    source = BASE / source_rel
    preinh_rel = spec.get("preinh_topology_source") or template["preinh_source"]
    preinh_source = BASE / preinh_rel
    class_source_rel = spec.get("preinh_class_source") or preinh_rel
    class_source = BASE / class_source_rel
    destination = BASE / "TimeLearnerMatrix" / spec["wave"] / "inputs" / case_id
    if destination.exists():
        saved = destination / "matrix_input_manifest.json"
        if saved.is_file() and not refresh:
            old = json.loads(saved.read_text(encoding="utf-8"))
            if old.get("factors") == {k: v for k, v in spec.items() if k not in ("id", "wave")}:
                current_matrix_hash = sha256(MANIFEST)
                if old.get("matrix_definition_sha256") != current_matrix_hash:
                    old["matrix_definition_sha256"] = current_matrix_hash
                    old["registry_refreshed_utc"] = datetime.now(timezone.utc).isoformat()
                    saved.write_text(json.dumps(old, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                return old
            raise RuntimeError(f"config factors changed; use --refresh to regenerate {destination}")
        if not saved.is_file():
            if not refresh:
                raise FileExistsError(f"refusing to overwrite incomplete config snapshot: {destination}")
            allowed_names = {"Model_00.xml", "Parameters_00.xml", "Project.ini", "Interface.xml"}
            allowed_globs = ("Matrix*.xml", "Pack*.xml", "*.pack")
            for existing in destination.rglob("*"):
                if existing.is_dir():
                    continue
                rel = existing.relative_to(destination)
                if not rel.parts or rel.parts[0] not in ("Train", "Test"):
                    raise RuntimeError(f"refusing to refresh snapshot with non-input data: {existing}")
                if existing.name not in allowed_names and not any(fnmatch.fnmatch(existing.name, pattern) for pattern in allowed_globs):
                    raise RuntimeError(f"refusing to refresh snapshot with unrecognized input file: {existing}")
    if not source.is_dir() or not preinh_source.is_dir() or not class_source.is_dir():
        raise FileNotFoundError(f"missing source/template for {case_id}: {source} / {preinh_source} / {class_source}")

    copied = []
    historical_exact = spec.get("source_mode") == "historical_exact"
    historical_source_commit = spec.get("source_commit")
    if historical_exact and historical_source_commit:
        selected = copy_historical_git_source(
            str(spec["source_config"]), destination, str(historical_source_commit)
        )
        copied = [{"side": rel.parts[0], "file": str(Path(*rel.parts[1:])), "sha256": sha256(destination / rel)} for rel in selected]
    else:
        membrane_resistance = None
        if spec.get("initial_rs_to_rm") is not None:
            for rel in XML_INPUTS:
                source_xml = source / "Train" / rel
                if not source_xml.is_file():
                    continue
                content = source_xml.read_text(encoding="utf-8")
                values = tag_values(content, "ExcMembraneResistance") or tag_values(content, "RestingResistance")
                if values:
                    membrane_resistance = float(values[0].replace(",", "."))
                    break
            if membrane_resistance is None:
                raise ValueError(f"cannot determine membrane resistance for initial Rs case {case_id}")
        for side in ("Train", "Test"):
            dst_side = destination / side
            dst_side.mkdir(parents=True, exist_ok=True)
            for rel in pv.ALLOWLIST_INPUTS:
                src_file = source / side / rel
                companion = preinh_source / side / rel
                class_companion = class_source / side / rel
                if not src_file.is_file():
                    raise FileNotFoundError(src_file)
                shutil.copy2(src_file, dst_side / rel)
                if rel.endswith(".xml"):
                    text = src_file.read_text(encoding="utf-8")
                    if rel in XML_INPUTS:
                        if not companion.is_file():
                            raise FileNotFoundError(companion)
                        if not class_companion.is_file():
                            raise FileNotFoundError(class_companion)
                        if not spec.get("preserve_classes"):
                            sibling = "Parameters_00.xml" if rel == "Model_00.xml" else "Model_00.xml"
                            class_template = class_companion.read_text(encoding="utf-8")
                            sibling_file = class_source / side / sibling
                            if sibling_file.is_file():
                                class_template += "\n" + sibling_file.read_text(encoding="utf-8")
                            text = toggle_inhibition(
                                text,
                                companion.read_text(encoding="utf-8"),
                                bool(spec["presynaptic_inhibition"]),
                                float(spec.get("presynaptic_coefficient", 2.5)),
                                class_template_text=class_template,
                                require_flags=(side == "Train"),
                                force_presynaptic_classes=bool(spec.get("force_presynaptic_classes")),
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
                    text = apply_xml_factors(text, spec, side=side, membrane_resistance=membrane_resistance)
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

    pulse = BASE.parents[3] / "Libraries" / "Nmsdk-PulseLib"
    record = {
        "case": case_id,
        "wave": spec["wave"],
        "factors": {k: v for k, v in spec.items() if k not in ("id", "wave")},
        "source": str(source.relative_to(BASE)),
        "legacy_noninhibited_template": str(template.get("source", "")),
        "presynaptic_topology_template": str(preinh_source.relative_to(BASE)),
        "presynaptic_class_template": str(class_source.relative_to(BASE)),
        "source_mode": spec.get("source_mode", "factor_variant"),
        "source_commit": spec.get("source_commit"),
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
    if data.get("schema") not in {1, 2}:
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
    gold = input_root if spec.get("source_mode") == "historical_exact" else BASE / spec.get(
        "source_config", template.get("paired_source", template["preinh_source"])
    )
    internal_id = spec.get("worker_case", case_id)
    worker_config = {
        "root": input_root,
        "gold": gold,
        "train_t": float(spec.get("train_t", template["train_t"])),
        "span_ms": int(spec["duration_ms"]),
        "kind": template["kind"],
        "expect_tipr": spec.get("expect_tipr", "canon"),
        "skip_tipr_mid": bool(spec.get("skip_tipr_mid", True)),
        "normalization_mode": int(spec["normalization_mode"]),
        "presynaptic_inhibition": bool(spec["presynaptic_inhibition"]),
        "presynaptic_coefficient": float(spec.get("presynaptic_coefficient", 2.5)),
        "enable_posttrain_tuning": "1" if spec.get("posttrain_tuning", False) else "0",
        "posttrain_tip_resistance_mode": str(spec.get("tipr_mode", 1)),
    }
    if internal_id in pv.CASES:
        pv.CASES[internal_id] = {**pv.CASES[internal_id], **worker_config}
    else:
        pv.CASES[internal_id] = worker_config
    result_dir = RUNS / wave
    result_dir.mkdir(parents=True, exist_ok=True)
    run_dir = result_dir / case_id
    run_dir.mkdir(parents=True, exist_ok=True)
    result = pv.run_case(
        internal_id,
        run_dir=run_dir,
        train_t=float(spec.get("train_t", template["train_t"])),
        max_rs_rm=spec.get("max_rs_rm"),
    )
    result["worker_case"] = internal_id
    result["case"] = case_id
    result["matrix_factors"] = {k: v for k, v in spec.items() if k not in ("id",)}
    result["input_manifest"] = str(input_root / "matrix_input_manifest.json")
    result_path = run_dir / "matrix_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if not result.get("row_fail") else 1


def run_wave(wave: str, jobs: int) -> int:
    if jobs < 1 or jobs > 8:
        raise ValueError("--jobs must be between 1 and 8 for this campaign")
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
    status = {
        "wave": wave,
        "jobs": jobs,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "cases": {},
    }
    for spec in specs:
        case_id = spec["id"]
        saved_result = run_dir / case_id / "matrix_result.json"
        status["cases"][case_id] = (
            {"status": "completed", "result_file": str(saved_result.relative_to(BASE)), "resumed": True}
            if saved_result.is_file()
            else {"status": "queued"}
        )
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    def launch(spec: dict[str, Any]) -> tuple[str, int]:
        case_id = spec["id"]
        log_path = run_dir / f"{case_id}.log"
        command = [sys.executable, "-u", str(Path(__file__).resolve()), "--worker", wave, case_id]
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.run(
                command, cwd=BASE, stdout=log, stderr=subprocess.STDOUT, text=True, env=env
            )
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
    all_results = all(
        (run_dir / spec["id"] / "matrix_result.json").is_file() for spec in specs
    )
    data_failures = 0
    if all_results:
        for spec in specs:
            try:
                result = json.loads((run_dir / spec["id"] / "matrix_result.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                rc = 2
                all_results = False
                break
            if result.get("row_fail"):
                data_failures += 1
    status["case_data_failures"] = data_failures
    status["run_complete"] = all_results
    status["stop_before_next_wave"] = bool(rc == 2 or data_failures)
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    if rc == 2 or not all_results:
        return 2
    return 1 if data_failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wave", nargs="?")
    parser.add_argument("--prepare", metavar="WAVE", help="prepare immutable input snapshots for a wave")
    parser.add_argument("--run", metavar="WAVE", help="run a prepared wave")
    parser.add_argument("--case", nargs=2, metavar=("WAVE", "CASE"), help="run one prepared case")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--refresh", action="store_true", help="regenerate an existing input snapshot after an explicit design change")
    parser.add_argument("--worker", nargs=2, metavar=("WAVE", "CASE"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(*args.worker)
    if args.case:
        return worker(*args.case)
    if args.prepare:
        prepare_wave(args.prepare, refresh=args.refresh)
        return 0
    if args.run:
        return run_wave(args.run, args.jobs)
    parser.error("use --prepare WAVE or --run WAVE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
