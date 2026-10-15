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
import math
import os
import re
import shutil
import subprocess
import sys
import time
import fnmatch
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from matrix_run_safety import (
    CpuLoadSampler,
    active_console_count,
    active_console_pids,
    allocate_case_attempt,
    atomic_write_json,
    exclusive_file_lock,
    logical_cpu_count,
    resolve_runs_base,
)

BASE = Path(__file__).resolve().parents[1]
MANIFEST = BASE / "TimeLearnerMatrix" / "matrix.json"
RUNS_BASE = resolve_runs_base(BASE / "_repro" / "TimeLearnerMatrixRuns")
PV_PATH = BASE / "scripts" / "posttune_verify.py"
CLASS_TAGS = ("NeuronClassName", "MembraneClassName", "SynapseClassName")
INHIBITION_TAGS = ("UsePresynapticInhibition", "InhibitionCoeff")
XML_INPUTS = ("Model_00.xml", "Parameters_00.xml")
TAG_RE = r"(<{tag}\b[^>]*>)(.*?)(</{tag}\s*>)"
RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def run_root() -> Path:
    run_id = os.environ.get("TIMELEARNER_MATRIX_RUN_ID", "").strip()
    if not RUN_ID_RE.fullmatch(run_id):
        raise RuntimeError(
            "set TIMELEARNER_MATRIX_RUN_ID to a unique safe ID before running a matrix case"
        )
    return RUNS_BASE / run_id


def report_path(path: Path) -> str:
    """Render repository paths relative to the checkout and external artifacts absolutely."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(BASE.resolve()))
    except ValueError:
        return str(resolved)


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


def sha256_text_line_ending_variants(path: Path) -> set[str]:
    """Hash exact text plus LF/CRLF checkout variants, excluding binaries."""
    data = path.read_bytes()
    exact = hashlib.sha256(data).hexdigest()
    if b"\0" in data:
        return {exact}
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return {exact}
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    crlf = normalized.replace(b"\n", b"\r\n")
    return {
        exact,
        hashlib.sha256(normalized).hexdigest(),
        hashlib.sha256(crlf).hexdigest(),
    }


def matrix_definition_matches(saved: dict[str, Any], matrix_path: Path) -> bool:
    """Allow Git's LF/CRLF checkout conversion without accepting content edits."""
    expected = {
        str(saved.get("matrix_definition_sha256", "")),
        str(saved.get("matrix_definition_sha256_lf", "")),
    }
    expected.discard("")
    return bool(expected & sha256_text_line_ending_variants(matrix_path))


def verify_prepared_input_snapshot(input_root: Path, manifest: dict[str, Any] | None = None) -> None:
    """Require every prepared input file to match its immutable manifest hash."""
    manifest_path = input_root / "matrix_input_manifest.json"
    if manifest is None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("source_files")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError(f"input manifest has no file hashes: {manifest_path}")
    expected: dict[str, str] = {}
    for entry in entries:
        side = str(entry.get("side", ""))
        relative = PurePosixPath(str(entry.get("file", "")).replace("\\", "/"))
        if side not in {"Train", "Test"} or relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise RuntimeError(f"unsafe input path in manifest: {entry!r}")
        relpath = (Path(side) / Path(*relative.parts)).as_posix()
        if relpath in expected:
            raise RuntimeError(f"duplicate input path in manifest: {relpath}")
        expected[relpath] = str(entry.get("sha256", ""))

    actual: set[str] = set()
    for path in input_root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(input_root)
        if not relative_path.parts or relative_path.parts[0] not in {"Train", "Test"}:
            continue
        if path.is_symlink():
            raise RuntimeError(f"prepared input must not contain symlinks: {path}")
        relpath = relative_path.as_posix()
        actual.add(relpath)
        if relpath not in expected:
            raise RuntimeError(f"unmanifested prepared input file: {path}")
        if expected[relpath] not in sha256_text_line_ending_variants(path):
            raise RuntimeError(f"prepared input SHA-256 mismatch: {path}")
    missing = sorted(set(expected) - actual)
    if missing:
        raise RuntimeError(f"manifested prepared input files are missing: {missing}")


def test_config_hashes_are_provenanced(
    provenance: dict[str, Any],
    result_provenance: dict[str, Any],
    attempt_dir: Path,
) -> bool:
    """Anchor Test inputs to the attempt copy and record allowed runtime transforms.

    The evaluator intentionally merges learned weights and may patch threshold /
    analyzer settings in the attempt-local Test project. Therefore its final XML
    hashes are not expected to equal the pre-run hashes. The immutable attempt
    copy manifest must match the pre-run hashes, and the result must preserve the
    exact before/after hashes from the detailed provenance record.
    """
    before = provenance.get("config_sha256_before") or {}
    after = provenance.get("config_sha256_after") or {}
    result_before = result_provenance.get("config_sha256_before") or {}
    result_after = result_provenance.get("config_sha256_after") or {}
    try:
        attempt_inputs = json.loads((attempt_dir / "inputs_manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    copied_items = attempt_inputs.get("copied")
    if not isinstance(copied_items, list):
        return False
    copied = {
        (str(item.get("side", "")), str(item.get("rel", ""))): item.get("sha256")
        for item in copied_items
        if isinstance(item, dict)
    }
    test_files = ("Parameters_00.xml", "Model_00.xml")
    for filename in test_files:
        path = f"Test/{filename}"
        initial_hash = before.get(path)
        final_hash = after.get(path)
        if not initial_hash or not final_hash:
            return False
        if copied.get(("Test", filename)) != initial_hash:
            return False
        if result_before.get(path) != initial_hash or result_after.get(path) != final_hash:
            return False
    return True


def validate_worker_attempt_directory(attempt_dir: Path) -> None:
    """Allow the queue-owned log file while rejecting stale attempt artifacts."""
    if not attempt_dir.is_dir():
        raise FileNotFoundError(f"attempt directory is missing: {attempt_dir}")
    unexpected = [
        path.name
        for path in attempt_dir.iterdir()
        if path.name != "worker.log" or not path.is_file() or path.is_symlink()
    ]
    if unexpected:
        raise FileExistsError(f"attempt directory contains pre-existing artifacts: {unexpected}")


def effective_train_time_limit_seconds(
    spec: dict[str, Any], templates: dict[str, Any], run_manifest: dict[str, Any]
) -> float:
    """Resolve the matrix default or a fingerprinted diagnostic runtime override."""
    template = templates[spec["template"]]
    default = float(spec.get("train_t", template["train_t"]))
    override = run_manifest.get("runtime", {}).get("train_time_limit_override_seconds")
    value = default if override is None else float(override)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("training time limit must be a finite positive number of seconds")
    return value


def set_project_debug_logging(project_ini: Path, enabled: bool) -> dict[str, str]:
    """Set only the project-wide logger switch, preserving channel settings."""
    original = project_ini.read_text(encoding="utf-8")
    section_re = re.compile(r"(<MultiGeneral\b[^>]*>)(.*?)(</MultiGeneral\s*>)", re.S)
    matches = list(section_re.finditer(original))
    if len(matches) != 1:
        raise ValueError(f"expected one MultiGeneral block in {project_ini}, found {len(matches)}")
    match = matches[0]
    section = match.group(2)
    tag_re = re.compile(r"(<DebugModeFlag\b[^>]*>)(.*?)(</DebugModeFlag\s*>)", re.S)
    updated_section, count = tag_re.subn(
        lambda m: f"{m.group(1)}{1 if enabled else 0}{m.group(3)}", section, count=1
    )
    if count != 1:
        raise ValueError(f"MultiGeneral has no DebugModeFlag in {project_ini}")
    updated = original[:match.start(2)] + updated_section + original[match.end(2):]
    if updated != original:
        project_ini.write_text(updated, encoding="utf-8", newline="")
    return {
        "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        "sha256_after": sha256(project_ini),
        "debug_logging": "1" if enabled else "0",
    }


def make_quiet_debug_input_overlay(
    input_root: Path, attempt_dir: Path, wave: str, case_id: str
) -> tuple[Path, dict[str, Any]]:
    """Copy immutable inputs and disable verbose project logging in the copy."""
    return make_runtime_input_overlay(
        input_root, attempt_dir, wave, case_id,
        quiet_debug_logs=True, branch_gamma_mode=None,
        branch_rs_rm_limit=None, synapse_resistance_step=None,
        accept_quantized_amp_under_target=False,
        branch_segment_rm_profile=None,
        branch_initial_lengths=None,
    )


def _set_or_insert_runtime_tag(
    text: str,
    tag: str,
    value: str,
    after_tag: str,
    *,
    value_type: str = "b",
) -> str:
    if not tag_values(text, tag):
        from repro_cold_lib import ensure_tag_after

        text = ensure_tag_after(
            text, after_tag, tag, value,
            attrs=f' Type="{value_type}" PType="257" IoType="17"',
        )
        if not tag_values(text, tag):
            raise ValueError(f"cannot insert runtime parameter {tag} after {after_tag}")
    return set_all_tags(text, tag, value)


def parse_branch_segment_rm_profile(raw: str | None) -> dict[int, float] | None:
    """Parse diagnostic ``segment=ohms,...`` pairs for attempt-local Branch inputs."""
    if raw is None:
        return None
    profile: dict[int, float] = {}
    for item in raw.split(","):
        segment_text, separator, resistance_text = item.partition("=")
        if not separator:
            raise ValueError("Branch Rm profile entries must use segment=ohms")
        try:
            segment = int(segment_text.strip())
            resistance = float(resistance_text.strip())
        except ValueError as exc:
            raise ValueError(f"invalid Branch Rm profile entry: {item!r}") from exc
        if segment < 1:
            raise ValueError("Branch Rm profile segment indices must be positive")
        if not math.isfinite(resistance) or resistance <= 0.0:
            raise ValueError("Branch Rm profile resistances must be finite and positive")
        if segment in profile:
            raise ValueError(f"duplicate Branch Rm profile segment: {segment}")
        profile[segment] = resistance
    if not profile:
        raise ValueError("Branch Rm profile must contain at least one segment=ohms pair")
    return dict(sorted(profile.items()))


def parse_branch_initial_lengths(raw: str | None) -> list[int] | None:
    """Parse the explicit prebuilt Branch attachment lengths used by the Rm probe."""
    if raw is None:
        return None
    try:
        lengths = [int(item.strip()) for item in raw.split(",")]
    except ValueError as exc:
        raise ValueError("Branch initial lengths must be comma-separated positive integers") from exc
    if len(lengths) < 2 or any(length < 1 for length in lengths):
        raise ValueError("Branch initial lengths must contain at least two positive integers")
    return lengths


def apply_branch_segment_rm_profile(text: str, profile: dict[int, float]) -> str:
    """Use the shared XML editor for the same Rm profile in both Train files."""
    from repro_cold_lib import apply_branch_segment_rm_profile as apply_profile

    updated = apply_profile(text, profile)
    ET.fromstring(updated)
    return updated


def make_runtime_input_overlay(
    input_root: Path,
    attempt_dir: Path,
    wave: str,
    case_id: str,
    *,
    quiet_debug_logs: bool,
    branch_gamma_mode: str | None,
    branch_rs_rm_limit: float | None = None,
    synapse_resistance_step: float | None = None,
    accept_quantized_amp_under_target: bool = False,
    branch_segment_rm_profile: dict[int, float] | None = None,
    branch_initial_lengths: list[int] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Create an attempt-local input copy with recorded diagnostic overrides."""
    if branch_rs_rm_limit is not None and (
        not math.isfinite(branch_rs_rm_limit) or branch_rs_rm_limit < 1.0
    ):
        raise ValueError("Branch Rs/Rm limit must be finite and >= 1")
    if synapse_resistance_step is not None and (
        not math.isfinite(synapse_resistance_step) or synapse_resistance_step <= 0.0
    ):
        raise ValueError("SynapseResistanceStep must be finite and positive")
    if branch_segment_rm_profile is not None:
        if not branch_segment_rm_profile:
            raise ValueError("Branch segment Rm profile must not be empty")
        branch_segment_rm_profile = {
            int(segment): float(resistance)
            for segment, resistance in branch_segment_rm_profile.items()
        }
        if any(
            int(segment) < 1 or not math.isfinite(float(resistance)) or float(resistance) <= 0.0
            for segment, resistance in branch_segment_rm_profile.items()
        ):
            raise ValueError("Branch segment Rm profile must use positive segment IDs and finite positive resistances")
    if branch_initial_lengths is not None and branch_segment_rm_profile is None:
        raise ValueError("Branch prebuilt initial lengths require a segment Rm profile")
    if branch_initial_lengths is not None:
        if len(branch_initial_lengths) < 2 or any(int(length) < 1 for length in branch_initial_lengths):
            raise ValueError("Branch prebuilt initial lengths must contain at least two positive lengths")
        if not set(branch_segment_rm_profile or {}).issubset(set(branch_initial_lengths)):
            raise ValueError("each profiled Branch segment must be an input's prebuilt initial attachment")
    elif branch_segment_rm_profile is not None and set(branch_segment_rm_profile) != {1}:
        raise ValueError(
            "a Branch segment Rm profile without prebuilt initial lengths may only target segment 1, "
            "which survives the standard SoftCold reset"
        )
    overlay = attempt_dir / "runtime-input-overrides" / wave / case_id
    if overlay.exists():
        raise FileExistsError(f"runtime input overlay already exists: {overlay}")
    overlay.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(input_root, overlay)
    changed = []
    if quiet_debug_logs:
        for side in ("Train", "Test"):
            project_ini = overlay / side / "Project.ini"
            if not project_ini.is_file():
                raise FileNotFoundError(project_ini)
            item = set_project_debug_logging(project_ini, enabled=False)
            item.update({"side": side, "file": f"{side}/Project.ini"})
            changed.append(item)
    if branch_gamma_mode is not None:
        gamma_modes = {
            "shared-auto": ("1", "0", "0.05"),
            "per-input-auto": ("1", "1", "0.05"),
            "shared-fixed-005": ("0", "0", "0.05"),
        }
        if branch_gamma_mode not in gamma_modes:
            raise ValueError(f"unsupported Branch gamma diagnostic mode: {branch_gamma_mode}")
        auto_estimate, per_input, gamma = gamma_modes[branch_gamma_mode]
        for filename in ("Model_00.xml", "Parameters_00.xml"):
            path = overlay / "Train" / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            original = path.read_text(encoding="utf-8")
            updated = set_all_tags(original, "AttenuationGamma", gamma)
            updated = _set_or_insert_runtime_tag(
                updated, "AutoEstimateAttenuationGamma", auto_estimate,
                "AttenuationGamma",
            )
            updated = _set_or_insert_runtime_tag(
                updated, "UsePerInputAttenuationGamma", per_input,
                "AutoEstimateAttenuationGamma",
            )
            ET.fromstring(updated)
            path.write_text(updated, encoding="utf-8", newline="")
            changed.append({
                "side": "Train",
                "file": f"Train/{filename}",
                "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "sha256_after": sha256(path),
                "parameters": {
                    "AttenuationGamma": gamma,
                    "AutoEstimateAttenuationGamma": auto_estimate,
                    "UsePerInputAttenuationGamma": per_input,
                },
            })
    if branch_rs_rm_limit is not None:
        for filename in ("Model_00.xml", "Parameters_00.xml"):
            path = overlay / "Train" / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            original = path.read_text(encoding="utf-8")
            updated = _set_or_insert_runtime_tag(
                original,
                "MaxSynapseToMembraneResistanceRatio",
                format(branch_rs_rm_limit, ".17g"),
                "ResistanceMax",
                value_type="d",
            )
            ET.fromstring(updated)
            path.write_text(updated, encoding="utf-8", newline="")
            changed.append({
                "side": "Train",
                "file": f"Train/{filename}",
                "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "sha256_after": sha256(path),
                "parameters": {
                    "MaxSynapseToMembraneResistanceRatio": format(branch_rs_rm_limit, ".17g"),
                },
            })
    if synapse_resistance_step is not None:
        value = format(synapse_resistance_step, ".17g")
        for filename in ("Model_00.xml", "Parameters_00.xml"):
            path = overlay / "Train" / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            original = path.read_text(encoding="utf-8")
            if not tag_values(original, "SynapseResistanceStep"):
                raise ValueError(f"{path} has no SynapseResistanceStep parameter")
            updated = set_all_tags(original, "SynapseResistanceStep", value)
            ET.fromstring(updated)
            path.write_text(updated, encoding="utf-8", newline="")
            changed.append({
                "side": "Train",
                "file": f"Train/{filename}",
                "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "sha256_after": sha256(path),
                "parameters": {"SynapseResistanceStep": value},
            })
    if accept_quantized_amp_under_target:
        for filename in ("Model_00.xml", "Parameters_00.xml"):
            path = overlay / "Train" / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            original = path.read_text(encoding="utf-8")
            updated = _set_or_insert_runtime_tag(
                original,
                "AcceptQuantizedAmpUnderTarget",
                "1",
                "NormalizationMode",
            )
            ET.fromstring(updated)
            path.write_text(updated, encoding="utf-8", newline="")
            changed.append({
                "side": "Train",
                "file": f"Train/{filename}",
                "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "sha256_after": sha256(path),
                "parameters": {"AcceptQuantizedAmpUnderTarget": "1"},
            })
    if branch_segment_rm_profile is not None:
        for filename in ("Model_00.xml", "Parameters_00.xml"):
            path = overlay / "Train" / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            original = path.read_text(encoding="utf-8")
            updated = apply_branch_segment_rm_profile(original, branch_segment_rm_profile)
            path.write_text(updated, encoding="utf-8", newline="")
            changed.append({
                "side": "Train",
                "file": f"Train/{filename}",
                "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "sha256_after": sha256(path),
                "parameters": {
                    "BranchSegmentMembraneResistanceProfile": {
                        str(segment): format(resistance, ".17g")
                        for segment, resistance in sorted(branch_segment_rm_profile.items())
                    },
                    "fields": ["Resistance", "FBResistance", "RestingResistance"],
                    "channels": ["ExcChannel", "InhChannel"],
                },
            })
    if branch_initial_lengths is not None:
        length_text = " ".join(str(int(length)) for length in branch_initial_lengths)
        for filename in ("Model_00.xml", "Parameters_00.xml"):
            path = overlay / "Train" / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            original = path.read_text(encoding="utf-8")
            updated = set_all_tags(original, "DendriteLength", length_text)
            updated = set_all_tags(updated, "IsNeedToTrain", "1")
            updated = _set_or_insert_runtime_tag(
                updated, "ResetToUntrainedState", "0", "IsNeedToTrain", value_type="b"
            )
            updated = set_all_tags(updated, "StructureBuildMode", "2")
            ET.fromstring(updated)
            path.write_text(updated, encoding="utf-8", newline="")
            changed.append({
                "side": "Train",
                "file": f"Train/{filename}",
                "sha256_before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "sha256_after": sha256(path),
                "parameters": {
                    "DendriteLength": branch_initial_lengths,
                    "InitialSomaPotential": "preserved from source configuration",
                    "TipSynapseResistance": "preserved from source configuration",
                    "LTZ threshold settings": "preserved from source configuration",
                    "IsNeedToTrain": 1,
                    "ResetToUntrainedState": 0,
                    "StructureBuildMode": 2,
                    "SoftColdReset": "skipped to preserve the prebuilt diagnostic state",
                },
            })
    record = {
        "mode": "runtime_input_overlay",
        "source_input": str(input_root),
        "source_matrix_manifest_sha256": sha256(input_root / "matrix_input_manifest.json"),
        "quiet_debug_logs": quiet_debug_logs,
        "branch_gamma_mode": branch_gamma_mode,
        "branch_rs_rm_limit": branch_rs_rm_limit,
        "synapse_resistance_step": synapse_resistance_step,
        "accept_quantized_amp_under_target": accept_quantized_amp_under_target,
        "branch_segment_rm_profile": branch_segment_rm_profile,
        "branch_initial_lengths": branch_initial_lengths,
        "branch_segment_rm_profile_application": (
            "after_softcold_skip_cpp_reset_and_build"
            if branch_segment_rm_profile and branch_initial_lengths is None
            else "prebuilt_input_skip_cpp_reset" if branch_segment_rm_profile else None
        ),
        "skip_cpp_reset_to_untrained": branch_segment_rm_profile is not None,
        "skip_cpp_structure_rebuild": branch_segment_rm_profile is not None,
        "overrides": changed,
        "note": (
            "Overrides exist only in this attempt-local copy; canonical matrix inputs remain unchanged. "
            + (
                "A segment-1 profile is reapplied after standard SoftCold reset; "
                "ResetToUntrainedState=0 and StructureBuildMode=2 suppress the known trainer reset/build paths. "
                "Confirm live channel values from the C++ audit."
                if branch_segment_rm_profile and branch_initial_lengths is None
                else "A prebuilt-state profile is applied before launch and C++ "
                "ResetToUntrainedState is disabled to preserve it."
                if branch_segment_rm_profile
                else ""
            )
        ),
    }
    (overlay / "runtime_input_overrides.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return overlay, record


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
    source_norm = source_rel.replace("\\", "/")
    git_source_path = f"Configs/SpikeSamples/StructTrain/{source_norm}"
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
                if not matrix_definition_matches(old, MANIFEST):
                    raise RuntimeError(
                        f"matrix definition differs beyond line endings from this input snapshot: {destination}; "
                        "use an explicit --refresh only after preserving prior run provenance"
                    )
                verify_prepared_input_snapshot(destination, old)
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
        "matrix_definition_sha256_lf": hashlib.sha256(
            MANIFEST.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest(),
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


def load_run_manifest() -> dict[str, Any]:
    path = run_root() / "run_manifest.json"
    if not path.is_file():
        raise RuntimeError(
            f"run manifest missing at {path}; create or resume the run through run_timelearner_matrix_queue.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def case_attempt_result(
    case_root: Path,
    *,
    case_id: str,
    run_manifest: dict[str, Any],
    input_manifest_sha256: str,
) -> tuple[Path, dict[str, Any]] | None:
    """Find a completed immutable attempt with matching run and input provenance."""
    run_id = run_manifest.get("run_id")
    run_fingerprint = run_manifest.get("run_fingerprint")
    case_fingerprint = run_manifest.get("case_fingerprints", {}).get(case_id)
    if not run_id or not run_fingerprint or not case_fingerprint:
        return None
    candidates = sorted(
        (path for path in case_root.glob("attempt-*") if path.is_dir()), reverse=True
    )
    for attempt_dir in candidates:
        result_path = attempt_dir / "matrix_result.json"
        provenance_path = attempt_dir / "provenance.json"
        if not result_path.is_file() or not provenance_path.is_file():
            continue
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        run_provenance = result.get("run_provenance") or {}
        if (
            result.get("case") != case_id
            or result.get("matrix_run_id") != run_id
            or result.get("matrix_run_fingerprint") != run_fingerprint
            or result.get("case_fingerprint") != case_fingerprint
            or result.get("matrix_launcher_sha256") != run_manifest.get("launcher_sha256")
            or result.get("input_manifest_sha256") != input_manifest_sha256
            or run_provenance.get("binary_sha256") != run_manifest.get("binary_sha256")
            or run_provenance.get("root_git") != run_manifest.get("root_git")
            or run_provenance.get("gitlinks") != run_manifest.get("gitlinks")
            or provenance.get("binary_sha256_at_launch") != run_manifest.get("binary_sha256")
            or provenance.get("binary_sha256_after") != run_manifest.get("binary_sha256")
            or provenance.get("root_git") != run_manifest.get("root_git")
            or provenance.get("root_git_at_launch") != run_manifest.get("root_git")
            or provenance.get("gitlinks_at_launch") != run_manifest.get("gitlinks")
            or provenance.get("source_sha256_at_launch") != run_manifest.get("source_sha256")
            or provenance.get("source_sha256_after") != run_manifest.get("source_sha256")
            or provenance.get("source_changed_during_run") is not False
            or provenance.get("binary_changed_during_run") is not False
            or not test_config_hashes_are_provenanced(
                provenance,
                result.get("run_provenance") or {},
                attempt_dir,
            )
            or run_provenance.get("source_sha256") != run_manifest.get("source_sha256")
            or run_provenance.get("source_sha256_after") != run_manifest.get("source_sha256")
            or run_provenance.get("binary_sha256_after") != run_manifest.get("binary_sha256")
            or run_provenance.get("source_changed_during_run") is not False
            or run_provenance.get("binary_changed_during_run") is not False
        ):
            continue
        return attempt_dir, result
    return None


def execute_worker(command: list[str], *, cwd: Path, env: dict[str, str], log_path: Path) -> int:
    """Run one isolated worker process; split out so orchestration can be tested with a stub."""
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            command,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
    return int(proc.returncode)


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


def worker(
    wave: str,
    case_id: str,
    *,
    quiet_debug_logs: bool = False,
    max_polls: int | None = None,
) -> int:
    pv = load_pv()
    data = load_manifest()
    run_manifest = load_run_manifest()
    if case_id not in run_manifest.get("selected_cases", run_manifest.get("case_ids", [])):
        raise RuntimeError(f"case {case_id} is not part of run fingerprint {run_manifest.get('run_fingerprint')}")
    spec = next((c for c in data["cases"] if c["wave"] == wave and c["id"] == case_id), None)
    if spec is None:
        raise ValueError(f"unknown case {wave}/{case_id}")
    train_time_limit = effective_train_time_limit_seconds(spec, data["templates"], run_manifest)
    input_root = BASE / "TimeLearnerMatrix" / wave / "inputs" / case_id
    if not input_root.is_dir():
        raise FileNotFoundError(f"input snapshot missing; run --prepare {wave}: {input_root}")
    input_manifest_path = input_root / "matrix_input_manifest.json"
    input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    verify_prepared_input_snapshot(input_root, input_manifest)
    expected_input_sha = run_manifest.get("input_manifest_sha256", {}).get(case_id)
    if not expected_input_sha or sha256(input_manifest_path) != expected_input_sha:
        raise RuntimeError(f"prepared input manifest no longer matches the run fingerprint: {input_manifest_path}")
    if os.environ.get("TIMELEARNER_MATRIX_QUEUE_LOCKED") != "1":
        raise RuntimeError("direct worker launches are disabled; start cases through run_timelearner_matrix_queue.py")
    attempt_value = os.environ.get("TIMELEARNER_MATRIX_ATTEMPT_DIR", "").strip()
    if not attempt_value:
        raise RuntimeError("worker requires an attempt directory allocated by the queue")
    attempt_dir = Path(attempt_value).resolve()
    expected_case_root = (run_root() / wave / case_id).resolve()
    if attempt_dir.parent != expected_case_root or not attempt_dir.name.startswith("attempt-"):
        raise RuntimeError(f"attempt directory is outside the expected case namespace: {attempt_dir}")
    validate_worker_attempt_directory(attempt_dir)
    runtime_input_root = input_root
    runtime_input_overrides = None
    branch_gamma_mode = run_manifest.get("runtime", {}).get("branch_gamma_mode")
    branch_rs_rm_limit = run_manifest.get("runtime", {}).get("branch_rs_rm_limit")
    synapse_resistance_step = run_manifest.get("runtime", {}).get("synapse_resistance_step")
    accept_quantized_amp_under_target = bool(
        run_manifest.get("runtime", {}).get("accept_quantized_amp_under_target", False)
    )
    branch_segment_rm_profile = run_manifest.get("runtime", {}).get("branch_segment_rm_profile")
    branch_initial_lengths = run_manifest.get("runtime", {}).get("branch_initial_lengths")
    if branch_gamma_mode is not None and spec.get("trainer") != "NNeuronTimeLearnerBranch":
        raise ValueError("Branch gamma diagnostic modes only apply to Branch trainer cases")
    if branch_rs_rm_limit is not None and (
        spec.get("trainer") != "NNeuronTimeLearnerBranch"
        or int(spec.get("normalization_mode", 0)) != 1
    ):
        raise ValueError("Branch Rs/Rm diagnostic limits require parametric Branch cases")
    if synapse_resistance_step is not None and int(spec.get("normalization_mode", 0)) != 0:
        raise ValueError("SynapseResistanceStep diagnostic overrides require structural N0 cases")
    if accept_quantized_amp_under_target and int(spec.get("normalization_mode", 0)) != 0:
        raise ValueError("quantized structural amplitude acceptance requires structural N0 cases")
    if branch_segment_rm_profile is not None and (
        spec.get("trainer") != "NNeuronTimeLearnerBranch"
        or int(spec.get("normalization_mode", 0)) != 1
    ):
        raise ValueError("Branch segment Rm profiles require parametric Branch cases")
    if branch_initial_lengths is not None and (
        spec.get("trainer") != "NNeuronTimeLearnerBranch"
        or int(spec.get("normalization_mode", 0)) != 1
        or branch_segment_rm_profile is None
    ):
        raise ValueError("Branch prebuilt initial lengths require a parametric Branch segment Rm profile")
    if (
        quiet_debug_logs or branch_gamma_mode is not None or branch_rs_rm_limit is not None
        or synapse_resistance_step is not None
        or accept_quantized_amp_under_target
        or branch_segment_rm_profile is not None or branch_initial_lengths is not None
    ):
        runtime_input_root, runtime_input_overrides = make_runtime_input_overlay(
            input_root, attempt_dir, wave, case_id,
            quiet_debug_logs=quiet_debug_logs,
            branch_gamma_mode=branch_gamma_mode,
            branch_rs_rm_limit=branch_rs_rm_limit,
            synapse_resistance_step=synapse_resistance_step,
            accept_quantized_amp_under_target=accept_quantized_amp_under_target,
            branch_segment_rm_profile=branch_segment_rm_profile,
            branch_initial_lengths=branch_initial_lengths,
        )
    template = data["templates"][spec["template"]]
    gold = input_root if spec.get("source_mode") == "historical_exact" else BASE / spec.get(
        "source_config", template.get("paired_source", template["preinh_source"])
    )
    internal_id = spec.get("worker_case", case_id)
    worker_config = {
        "root": runtime_input_root,
        "gold": gold,
        "train_t": train_time_limit,
        "span_ms": int(spec["duration_ms"]),
        "kind": template["kind"],
        "expect_tipr": spec.get("expect_tipr", "canon"),
        "skip_tipr_mid": bool(spec.get("skip_tipr_mid", True)),
        "normalization_mode": int(spec["normalization_mode"]),
        "presynaptic_inhibition": bool(spec["presynaptic_inhibition"]),
        "presynaptic_coefficient": float(spec.get("presynaptic_coefficient", 2.5)),
        "enable_posttrain_tuning": "1" if spec.get("posttrain_tuning", False) else "0",
        "posttrain_tip_resistance_mode": str(spec.get("tipr_mode", 1)),
        "disable_train_statistic_logs": True,
        "branch_segment_rm_profile": branch_segment_rm_profile,
        "branch_initial_lengths": branch_initial_lengths,
        "skip_softcold_reset": branch_initial_lengths is not None,
    }
    if internal_id in pv.CASES:
        pv.CASES[internal_id] = {**pv.CASES[internal_id], **worker_config}
    else:
        pv.CASES[internal_id] = worker_config
    run_dir = attempt_dir
    result = pv.run_case(
        internal_id,
        run_dir=run_dir,
        train_t=train_time_limit,
        max_polls=max_polls,
        max_rs_rm=spec.get("max_rs_rm"),
        disable_train_statistic_logs=True,
    )
    result["worker_case"] = internal_id
    result["case"] = case_id
    result["matrix_factors"] = {k: v for k, v in spec.items() if k not in ("id",)}
    result["input_manifest"] = str(input_root / "matrix_input_manifest.json")
    result["matrix_run_id"] = os.environ.get("TIMELEARNER_MATRIX_RUN_ID")
    result["matrix_run_fingerprint"] = run_manifest["run_fingerprint"]
    result["matrix_launcher_sha256"] = run_manifest.get("launcher_sha256")
    result["case_fingerprint"] = run_manifest["case_fingerprints"][case_id]
    result["attempt_id"] = attempt_dir.name
    result["input_manifest_sha256"] = sha256(input_root / "matrix_input_manifest.json")
    result["runtime_input_overrides"] = runtime_input_overrides
    result["runtime_execution_options"] = {
        "quiet_debug_logs": quiet_debug_logs,
        "disable_train_statistic_logs": True,
        "max_polls": max_polls,
        "branch_gamma_mode": branch_gamma_mode,
        "branch_rs_rm_limit": branch_rs_rm_limit,
        "synapse_resistance_step": synapse_resistance_step,
        "accept_quantized_amp_under_target": accept_quantized_amp_under_target,
        "branch_segment_rm_profile": branch_segment_rm_profile,
        "branch_initial_lengths": branch_initial_lengths,
        "skip_softcold_reset": branch_initial_lengths is not None,
        "branch_segment_rm_profile_application": (
            "after_softcold_skip_cpp_reset_and_build"
            if branch_segment_rm_profile and branch_initial_lengths is None
            else "prebuilt_input_skip_cpp_reset" if branch_segment_rm_profile else None
        ),
        "skip_cpp_reset_to_untrained": branch_segment_rm_profile is not None,
        "skip_cpp_structure_rebuild": branch_segment_rm_profile is not None,
        "train_time_limit_override_seconds": run_manifest.get("runtime", {}).get(
            "train_time_limit_override_seconds"
        ),
    }
    provenance_path = run_dir / "provenance.json"
    if not provenance_path.is_file():
        raise RuntimeError(f"runtime provenance missing for {case_id}: {provenance_path}")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if not provenance.get("root_git") or not provenance.get("binary_sha256"):
        raise RuntimeError(f"runtime provenance lacks root or Console SHA-256 for {case_id}")
    result["run_provenance"] = {
        key: provenance.get(key)
        for key in (
            "root_git",
            "root_git_at_launch",
            "gitlinks",
            "gitlinks_at_launch",
            "binary_sha256",
            "binary_sha256_at_launch",
            "binary_sha256_after",
            "source_sha256",
            "source_sha256_at_launch",
            "source_sha256_after",
            "source_changed_during_run",
            "binary_changed_during_run",
            "training_config_changed_during_run",
            "config_sha256",
            "config_sha256_before",
            "config_sha256_after",
            "inputs_mutated_during_run",
            "train_t_effective",
        )
    }
    result_path = run_dir / "matrix_result.json"
    atomic_write_json(result_path, result, replace=False)
    # A completed experiment writes its outcome regardless of learned quality.
    # The wave runner separately stops on non-convergence or broken evaluation.
    return 0


def run_wave(
    wave: str,
    jobs: int,
    *,
    case_ids: list[str] | None = None,
    quiet_debug_logs: bool = False,
    max_polls: int | None = None,
    train_time_limit_override_seconds: float | None = None,
) -> int:
    if jobs < 1 or jobs > 8:
        raise ValueError("--jobs must be between 1 and 8 for this campaign")
    if train_time_limit_override_seconds is not None and (
        not math.isfinite(train_time_limit_override_seconds) or train_time_limit_override_seconds <= 0
    ):
        raise ValueError("--train-time-limit-override-seconds must be finite and positive")
    data = load_manifest()
    specs = [case for case in data["cases"] if case["wave"] == wave]
    if case_ids is not None:
        requested = set(case_ids)
        unknown = sorted(requested - {case["id"] for case in specs})
        if unknown:
            raise ValueError(f"unknown cases for {wave}: {unknown}")
        specs = [case for case in specs if case["id"] in requested]
    if not specs:
        raise ValueError(f"no cases in manifest for {wave}")
    missing = [s["id"] for s in specs if not (BASE / "TimeLearnerMatrix" / wave / "inputs" / s["id"]).is_dir()]
    if missing:
        raise FileNotFoundError(f"inputs not prepared: {missing}; run --prepare {wave}")
    run_manifest = load_run_manifest()
    manifest_cases = set(run_manifest.get("selected_cases", run_manifest.get("case_ids", [])))
    requested_cases = {case["id"] for case in specs}
    if requested_cases != manifest_cases:
        raise RuntimeError(
            "selected cases do not match the immutable run manifest; invoke the queue with the original case selection"
        )
    input_manifest_shas: dict[str, str] = {}
    for spec in specs:
        case_id = spec["id"]
        input_root = BASE / "TimeLearnerMatrix" / wave / "inputs" / case_id
        input_manifest_path = input_root / "matrix_input_manifest.json"
        input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
        verify_prepared_input_snapshot(input_root, input_manifest)
        input_manifest_shas[case_id] = sha256(input_manifest_path)
        if input_manifest_shas[case_id] != run_manifest.get("input_manifest_sha256", {}).get(case_id):
            raise RuntimeError(f"prepared input manifest changed after run fingerprinting: {input_manifest_path}")
    wave_dir = run_root() / wave
    wave_dir.mkdir(parents=True, exist_ok=True)
    status_path = wave_dir / "wave_status.json"
    status = {
        "wave": wave,
        "jobs": jobs,
        "quiet_debug_logs": quiet_debug_logs,
        "disable_train_statistic_logs": True,
        "max_polls": max_polls,
        "branch_gamma_mode": run_manifest.get("runtime", {}).get("branch_gamma_mode"),
        "branch_rs_rm_limit": run_manifest.get("runtime", {}).get("branch_rs_rm_limit"),
        "branch_segment_rm_profile": run_manifest.get("runtime", {}).get("branch_segment_rm_profile"),
        "branch_initial_lengths": run_manifest.get("runtime", {}).get("branch_initial_lengths"),
        "skip_softcold_reset": run_manifest.get("runtime", {}).get("branch_initial_lengths") is not None,
        "branch_segment_rm_profile_application": run_manifest.get("runtime", {}).get(
            "branch_segment_rm_profile_application"
        ),
        "skip_cpp_reset_to_untrained": run_manifest.get("runtime", {}).get(
            "skip_cpp_reset_to_untrained"
        ),
        "train_time_limit_override_seconds": run_manifest.get("runtime", {}).get(
            "train_time_limit_override_seconds"
        ),
        "selected_cases": [case["id"] for case in specs],
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "cases": {},
    }
    attempt_dirs: dict[str, Path] = {}
    for spec in specs:
        case_id = spec["id"]
        input_manifest_sha256 = input_manifest_shas[case_id]
        case_root = wave_dir / case_id
        saved = case_attempt_result(
            case_root,
            case_id=case_id,
            run_manifest=run_manifest,
            input_manifest_sha256=input_manifest_sha256,
        )
        if saved:
            saved_dir, _ = saved
            status["cases"][case_id] = {
                "status": "completed",
                "result_file": report_path(saved_dir / "matrix_result.json"),
                "attempt_id": saved_dir.name,
                "resumed": True,
            }
        else:
            attempt_id, attempt_dir = allocate_case_attempt(case_root)
            attempt_dirs[case_id] = attempt_dir
            status["cases"][case_id] = {"status": "queued", "attempt_id": attempt_id}
    atomic_write_json(status_path, status)

    def launch(spec: dict[str, Any]) -> tuple[str, int]:
        case_id = spec["id"]
        attempt_dir = attempt_dirs[case_id]
        log_path = attempt_dir / "worker.log"
        command = [sys.executable, "-u", str(Path(__file__).resolve()), "--worker", wave, case_id]
        if quiet_debug_logs:
            command.append("--quiet-debug-logs")
        if max_polls is not None:
            command.extend(("--max-polls", str(max_polls)))
        env = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "TIMELEARNER_MATRIX_ATTEMPT_DIR": str(attempt_dir),
        }
        code = execute_worker(command, cwd=BASE, env=env, log_path=log_path)
        return case_id, code

    rc = 0
    pending_specs = [spec for spec in specs if spec["id"] in attempt_dirs]
    max_total = max(1, logical_cpu_count() - 1)
    worker_cap = max(1, min(jobs, len(pending_specs), max_total))
    baseline_console_pids = active_console_pids()
    cpu_sampler = CpuLoadSampler()
    throttled = False
    low_load_samples = 0
    cpu_samples: list[float] = []
    pending_index = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_cap) as pool:
        futures: dict[concurrent.futures.Future, str] = {}
        while pending_index < len(pending_specs) or futures:
            cpu = cpu_sampler.sample()
            if cpu is not None:
                cpu_samples.append(cpu)
                if cpu > 85.0:
                    throttled = True
                    low_load_samples = 0
                elif throttled and cpu < 70.0:
                    low_load_samples += 1
                    if low_load_samples >= 2:
                        throttled = False
                        low_load_samples = 0
                elif throttled:
                    low_load_samples = 0
            active_now = active_console_count()
            baseline_alive = len(baseline_console_pids.intersection(active_console_pids()))
            estimated_occupied = max(active_now, baseline_alive + len(futures))
            available = max(0, max_total - estimated_occupied)
            can_launch = 0 if throttled else min(
                available,
                worker_cap - len(futures),
                len(pending_specs) - pending_index,
            )
            for _ in range(can_launch):
                spec = pending_specs[pending_index]
                pending_index += 1
                future = pool.submit(launch, spec)
                futures[future] = spec["id"]
                status["cases"][spec["id"]] = {
                    "status": "running",
                    "attempt_id": attempt_dirs[spec["id"]].name,
                    "started_utc": datetime.now(timezone.utc).isoformat(),
                    "active_console_count_at_dispatch": active_now,
                    "cpu_percent_at_dispatch": cpu,
                }
                atomic_write_json(status_path, status)
            if not futures:
                time.sleep(2 if throttled or available == 0 else 0.25)
                continue
            done, _ = concurrent.futures.wait(
                futures,
                timeout=2.0,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            for future in done:
                case_id = futures.pop(future)
                code_case, code = future.result()
                attempt_dir = attempt_dirs[case_id]
                result_file = attempt_dir / "matrix_result.json"
                has_result = case_attempt_result(
                    attempt_dir.parent,
                    case_id=case_id,
                    run_manifest=run_manifest,
                    input_manifest_sha256=sha256(
                        BASE / "TimeLearnerMatrix" / wave / "inputs" / case_id / "matrix_input_manifest.json"
                    ),
                ) is not None
                status["cases"][case_id] = {
                    "status": "completed" if has_result else "worker_infrastructure_error",
                    "worker_exit_code": code,
                    "result_file": report_path(result_file) if has_result else None,
                    "log_file": report_path(attempt_dir / "worker.log"),
                    "attempt_id": attempt_dir.name,
                    "finished_utc": datetime.now(timezone.utc).isoformat(),
                }
                atomic_write_json(status_path, status)
                print(f"{code_case}: worker_exit={code} valid_result={has_result}")
                if not has_result:
                    rc = 2
    status["finished_utc"] = datetime.now(timezone.utc).isoformat()
    all_results = all(
        case_attempt_result(
            wave_dir / spec["id"],
            case_id=spec["id"],
            run_manifest=run_manifest,
            input_manifest_sha256=sha256(
                BASE / "TimeLearnerMatrix" / wave / "inputs" / spec["id"] / "matrix_input_manifest.json"
            ),
        ) is not None
        for spec in specs
    )
    training_stops = 0
    execution_errors = 0
    evaluation_errors = 0
    quality_failures = 0
    if all_results:
        for spec in specs:
            try:
                saved = case_attempt_result(
                    wave_dir / spec["id"],
                    case_id=spec["id"],
                    run_manifest=run_manifest,
                    input_manifest_sha256=sha256(
                        BASE / "TimeLearnerMatrix" / wave / "inputs" / spec["id"] / "matrix_input_manifest.json"
                    ),
                )
                if saved is None:
                    raise FileNotFoundError(f"no valid completed attempt for {spec['id']}")
                result = saved[1]
            except (OSError, json.JSONDecodeError):
                rc = 2
                all_results = False
                break
            convergence = str(result.get("training_convergence") or "")
            training_complete = convergence.startswith("converged")
            if convergence == "execution_error":
                execution_errors += 1
            elif not training_complete:
                training_stops += 1
            elif (
                result.get("gate_evaluated") is False
                or result.get("separation_quality") in {
                    "evaluation_error",
                    "insufficient_data",
                    "not_reached_or_unknown",
                    "not_evaluated_training_incomplete",
                }
                or result.get("detection_quality") in {
                    "evaluation_error",
                    "insufficient_data",
                    "not_evaluated_training_incomplete",
                }
            ):
                evaluation_errors += 1
            elif result.get("row_fail"):
                # Weak separation/detection is a research result, not a reason
                # to suppress later matrix cells.
                quality_failures += 1
    status["case_data_failures"] = (
        training_stops + execution_errors + evaluation_errors + quality_failures
    )
    status["process_limit"] = max_total
    status["requested_jobs"] = jobs
    status["existing_console_count_at_start"] = len(baseline_console_pids)
    status["cpu_percent_samples"] = cpu_samples
    status["cpu_throttle_applied"] = any(value > 85.0 for value in cpu_samples)
    status["training_stop_cases"] = training_stops
    status["execution_error_cases"] = execution_errors
    status["evaluation_error_cases"] = evaluation_errors
    status["quality_failure_cases"] = quality_failures
    status["run_complete"] = all_results
    status["stop_before_next_wave"] = bool(
        rc == 2 or training_stops or execution_errors or evaluation_errors
    )
    atomic_write_json(status_path, status)
    if rc == 2 or not all_results:
        return 2
    if execution_errors:
        return 4
    if evaluation_errors:
        return 3
    return 1 if training_stops else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wave", nargs="?")
    parser.add_argument("--prepare", metavar="WAVE", help="prepare immutable input snapshots for a wave")
    parser.add_argument("--run", metavar="WAVE", help="run a prepared wave")
    parser.add_argument("--case", nargs=2, metavar=("WAVE", "CASE"), help=argparse.SUPPRESS)
    parser.add_argument("--case-ids", nargs="+", help=argparse.SUPPRESS)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument(
        "--quiet-debug-logs",
        action="store_true",
        help="suppress project-wide per-step debug logging while retaining trainer iteration audits",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        help="override the worker polling ceiling (30 seconds per poll); useful for slow local simulations",
    )
    parser.add_argument(
        "--train-time-limit-override-seconds",
        type=float,
        help="diagnostic C++ runtime limit override; recorded in the immutable run fingerprint",
    )
    parser.add_argument("--refresh", action="store_true", help="regenerate an existing input snapshot after an explicit design change")
    parser.add_argument("--worker", nargs=2, metavar=("WAVE", "CASE"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(
            *args.worker,
            quiet_debug_logs=args.quiet_debug_logs,
            max_polls=args.max_polls,
        )
    if args.case:
        raise SystemExit("direct single-case launches are disabled; use run_timelearner_matrix_queue.py --case CASE --no-commit")
    if args.prepare:
        if os.environ.get("TIMELEARNER_MATRIX_QUEUE_LOCKED") == "1":
            prepare_wave(args.prepare, refresh=args.refresh)
        else:
            queue_lock = BASE / "_repro" / ".timelearner_matrix_queue.lock"
            with exclusive_file_lock(queue_lock, purpose=f"prepare matrix inputs {args.prepare}"):
                prepare_wave(args.prepare, refresh=args.refresh)
        return 0
    if args.run:
        if os.environ.get("TIMELEARNER_MATRIX_QUEUE_LOCKED") != "1":
            raise SystemExit("direct matrix launches are disabled; use run_timelearner_matrix_queue.py")
        return run_wave(
            args.run,
            args.jobs,
            case_ids=args.case_ids,
            quiet_debug_logs=args.quiet_debug_logs,
            max_polls=args.max_polls,
            train_time_limit_override_seconds=args.train_time_limit_override_seconds,
        )
    parser.error("use --prepare WAVE or --run WAVE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
