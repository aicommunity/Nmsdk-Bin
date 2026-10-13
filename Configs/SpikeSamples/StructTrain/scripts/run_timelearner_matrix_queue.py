#!/usr/bin/env python3
"""Run the registered wave queue, updating docs and committing each completed wave."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from matrix_run_safety import (
    atomic_write_json,
    exclusive_file_lock,
    reserve_run_root,
    sha256_file,
    sha256_json,
    verify_run_manifest,
)

BASE = Path(__file__).resolve().parents[1]
BIN_ROOT = BASE.parents[2]
ROOT = BIN_ROOT.parent
RUNS_BASE = BASE / "_repro" / "TimeLearnerMatrixRuns"
MATRIX = BASE / "TimeLearnerMatrix"
METRICS = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "evidence" / "metrics" / "TIMELEARNER_MATRIX_WAVES_20261010.md"
WAVE_PLAN = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "plans" / "TimeLearner-full-matrix-waves-20261010.ru.md"
FULL_MATRIX_REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "TIMELEARNER_FULL_MATRIX_AND_HISTORY_2026-10-10.ru.md"
RUNNER = BASE / "scripts" / "timelearner_matrix.py"
UPDATER = BASE / "scripts" / "update_timelearner_matrix_report.py"
QUEUE_LOCK = BASE / "_repro" / ".timelearner_matrix_queue.lock"


def run(command: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, text=True, check=check)


def git_text(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def ensure_no_staged_changes(path: Path) -> None:
    staged = git_text(path, "diff", "--cached", "--name-only")
    if staged:
        raise SystemExit(
            f"refusing to mix pre-staged changes into a wave commit in {path}:\n{staged}"
        )


def ensure_wave_paths_clean(wave: str) -> None:
    struct_rel = Path("Configs/SpikeSamples/StructTrain")
    bin_paths = [
        struct_rel / "EXPERIMENTS.md",
        struct_rel / "SUCCESSFUL_EXPERIMENTS.md",
        struct_rel / "TimeLearnerMatrix" / wave / "results.json",
    ]
    root_paths = [
        Path("Bin"),
        METRICS.relative_to(ROOT),
        WAVE_PLAN.relative_to(ROOT),
        FULL_MATRIX_REPORT.relative_to(ROOT),
    ]
    for repo, paths in ((BIN_ROOT, bin_paths), (ROOT, root_paths)):
        dirty = git_text(repo, "status", "--porcelain", "--", *map(str, paths))
        if dirty:
            raise SystemExit(
                f"refusing to overwrite or commit pre-existing wave report changes in {repo}:\n{dirty}"
            )


def run_root(run_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_id):
        raise SystemExit("--run-id must use only letters, digits, dot, underscore, or hyphen")
    os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id
    return RUNS_BASE / run_id


def git_head(path: Path) -> str | None:
    try:
        return git_text(path, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        return None


def make_run_fingerprint(wave: str, specs: list[dict], args: argparse.Namespace) -> dict:
    spec = importlib.util.spec_from_file_location(
        "posttune_verify_matrix_fingerprint", BASE / "scripts" / "posttune_verify.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load posttune_verify.py for run provenance")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    source_paths = [module.NMSDK_ROOT / rel for rel in module.PROVENANCE_SOURCE_REL]
    source_hashes = module.sha256_paths(source_paths)
    console = Path(module.NM)
    if not console.is_file():
        raise FileNotFoundError(f"NeuroModelerConsole is missing: {console}")
    console_sha = sha256_file(console)
    code_paths = [
        Path(__file__).resolve(),
        RUNNER.resolve(),
        (BASE / "scripts" / "matrix_run_safety.py").resolve(),
        (BASE / "scripts" / "posttune_verify.py").resolve(),
        (BASE / "scripts" / "repro_cold_lib.py").resolve(),
    ]
    launcher_hashes = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in code_paths
        if path.is_file() and path.is_relative_to(ROOT)
    }
    condition_runtime = {
        "quiet_debug_logs": bool(args.quiet_debug_logs),
        "max_polls": args.max_polls,
    }
    case_fingerprints = {}
    input_hashes = {}
    for case in specs:
        case_id = case["id"]
        input_manifest = MATRIX / wave / "inputs" / case_id / "matrix_input_manifest.json"
        if not input_manifest.is_file():
            raise FileNotFoundError(f"prepared input manifest missing: {input_manifest}")
        manifest_sha = sha256_file(input_manifest)
        input_hashes[case_id] = manifest_sha
        case_fingerprints[case_id] = sha256_json(
            {
                "wave": wave,
                "case": case,
                "matrix_definition_sha256": sha256_file(MATRIX / "matrix.json"),
                "input_manifest_sha256": manifest_sha,
                "source_hashes": source_hashes,
                "console_sha256": console_sha,
                "launcher_sha256": launcher_hashes,
                "execution_options": condition_runtime,
            }
        )
    bin_root = BIN_ROOT
    pulse_root = ROOT / "Libraries" / "Nmsdk-PulseLib"
    pulse_libs = {
        name: git_head(ROOT / name)
        for name in ("Libraries/Nmsdk-PulseLib", "Bin", "Rdk")
    }
    payload = {
        "schema": 1,
        "wave": wave,
        "case_ids": [case["id"] for case in specs],
        "case_fingerprints": case_fingerprints,
        "input_manifest_sha256": input_hashes,
        "matrix_definition_sha256": sha256_file(MATRIX / "matrix.json"),
        "source_sha256": source_hashes,
        "launcher_sha256": launcher_hashes,
        "console_path": str(console.resolve()),
        "console_sha256": console_sha,
        "condition_runtime": condition_runtime,
        "root_git": git_head(ROOT),
        "gitlinks": pulse_libs,
        "bin_git": git_head(bin_root),
        "pulse_git": git_head(pulse_root),
        "runtime": {
            "jobs": args.jobs,
            "quiet_debug_logs": bool(args.quiet_debug_logs),
            "max_polls": args.max_polls,
            "no_commit": bool(args.no_commit),
        },
    }
    # Root/Bin commits move when result documents are committed. The conditions
    # are identified by the actual experiment inputs, C++/trainer source hashes,
    # Console and algorithm-bearing submodule gitlinks; full commits remain in
    # provenance for audit.
    condition_payload = {
        "wave": payload["wave"],
        "case_ids": payload["case_ids"],
        "case_fingerprints": payload["case_fingerprints"],
        "input_manifest_sha256": payload["input_manifest_sha256"],
        "matrix_definition_sha256": payload["matrix_definition_sha256"],
        "source_sha256": payload["source_sha256"],
        "launcher_sha256": payload["launcher_sha256"],
        "console_path": payload["console_path"],
        "console_sha256": payload["console_sha256"],
        "condition_runtime": payload["condition_runtime"],
        "pulse_git": payload["pulse_git"],
        "rdk_git": payload["gitlinks"].get("Rdk"),
    }
    payload["experiment_fingerprint"] = sha256_json(condition_payload)
    payload["run_fingerprint"] = sha256_json(
        {key: value for key, value in payload.items() if key != "experiment_fingerprint"}
    )
    return payload


def find_duplicate_run(fingerprint: dict, *, exclude_run_id: str | None = None) -> str | None:
    target = fingerprint["experiment_fingerprint"]
    if not RUNS_BASE.is_dir():
        return None
    for manifest_path in RUNS_BASE.glob("*/run_manifest.json"):
        run_id = manifest_path.parent.name
        if run_id == exclude_run_id:
            continue
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if previous.get("experiment_fingerprint", previous.get("run_fingerprint")) == target:
            return run_id
    return None


def find_duplicate_result(wave: str, specs: list[dict], fingerprint: dict) -> dict | None:
    """Find a published result whose full condition provenance matches this selection."""
    expected_case_ids = {case["id"] for case in specs}
    for case_id in expected_case_ids:
        expected_spec = next(case for case in specs if case["id"] == case_id)
        paths = [MATRIX / wave / "results.json", *sorted((MATRIX / wave / "run_results").glob("*.json"))]
        for path in paths:
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for item in document.get("cases", []):
                if item.get("case") != case_id:
                    continue
                factors = item.get("factors")
                result = item.get("result") or {}
                if not factors:
                    factors = result.get("matrix_factors")
                    if factors and "id" not in factors:
                        factors = {"id": case_id, **factors}
                if factors != expected_spec or not result.get("training_convergence"):
                    continue
                provenance = result.get("run_provenance") or {}
                config_before = provenance.get("config_sha256_before") or {}
                config_after = provenance.get("config_sha256_after") or {}
                test_configs_unchanged = all(
                    config_before.get(name) and config_before[name] == config_after.get(name)
                    for name in ("Test/Parameters_00.xml", "Test/Model_00.xml")
                )
                if (
                    result.get("input_manifest_sha256")
                    == fingerprint["input_manifest_sha256"].get(case_id)
                    and result.get("matrix_launcher_sha256") == fingerprint.get("launcher_sha256")
                    and {
                        "quiet_debug_logs": (result.get("runtime_execution_options") or {}).get("quiet_debug_logs"),
                        "max_polls": (result.get("runtime_execution_options") or {}).get("max_polls"),
                    } == fingerprint.get("condition_runtime")
                    and provenance.get("binary_sha256") == fingerprint["console_sha256"]
                    and provenance.get("binary_sha256_after") == fingerprint["console_sha256"]
                    and provenance.get("source_sha256") == fingerprint["source_sha256"]
                    and provenance.get("source_sha256_after") == fingerprint["source_sha256"]
                    and provenance.get("binary_changed_during_run") is False
                    and provenance.get("source_changed_during_run") is False
                    and test_configs_unchanged
                    and (provenance.get("gitlinks") or {}).get("Libraries/Nmsdk-PulseLib")
                    == fingerprint["gitlinks"].get("Libraries/Nmsdk-PulseLib")
                    and (provenance.get("gitlinks") or {}).get("Rdk")
                    == fingerprint["gitlinks"].get("Rdk")
                ):
                    return {
                        "case": case_id,
                        "run_id": result.get("matrix_run_id") or document.get("run_id"),
                        "report": str(path),
                    }
    return None


def allocate_queue_status_attempt(run_root_path: Path) -> tuple[str, Path]:
    attempts = run_root_path / "queue_status_attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        attempt_id = f"attempt-{index:04d}"
        path = attempts / f"{attempt_id}.json"
        if not path.exists():
            return attempt_id, path
        index += 1


def save_queue_status(run_root_path: Path, attempt_path: Path, status: dict) -> None:
    atomic_write_json(attempt_path, status)
    atomic_write_json(run_root_path / "queue_status.json", status)


def completed_wave_matches_current(wave: str, args: argparse.Namespace) -> tuple[bool, dict]:
    registry = json.loads((MATRIX / "matrix.json").read_text(encoding="utf-8"))
    specs = [case for case in registry["cases"] if case["wave"] == wave]
    if not specs:
        return False, {"reason": "unknown_wave", "wave": wave}
    report = MATRIX / wave / "results.json"
    latest = None
    try:
        latest = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, {"reason": "missing_or_invalid_report", "wave": wave}
    run_id = latest.get("run_id")
    if not run_id or not latest.get("run_complete"):
        return False, {"reason": "report_not_complete", "wave": wave, "run_id": run_id}
    manifest_path = RUNS_BASE / run_id / "run_manifest.json"
    try:
        run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, {"reason": "run_manifest_missing", "wave": wave, "run_id": run_id}
    expected = make_run_fingerprint(wave, specs, args)
    if (
        run_manifest.get("experiment_fingerprint") != expected.get("experiment_fingerprint")
        or latest.get("run_fingerprint") != run_manifest.get("run_fingerprint")
        or set(run_manifest.get("selected_cases", [])) != {case["id"] for case in specs}
    ):
        return False, {"reason": "provenance_mismatch", "wave": wave, "run_id": run_id}
    status_path = RUNS_BASE / run_id / "queue_status.json"
    try:
        queue_status = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, {"reason": "queue_status_missing", "wave": wave, "run_id": run_id}
    if queue_status.get("status") not in {
        "queue_completed",
        "queue_completed_no_commit",
        "paused_after_training_or_evaluation_issue",
    }:
        return False, {"reason": "queue_not_terminal", "wave": wave, "run_id": run_id}
    for case in specs:
        input_manifest = MATRIX / wave / "inputs" / case["id"] / "matrix_input_manifest.json"
        if not input_manifest.is_file() or case_attempt_result(
            RUNS_BASE / run_id / wave / case["id"],
            case_id=case["id"],
            run_manifest=run_manifest,
            input_manifest_sha256=sha256_file(input_manifest),
        ) is None:
            return False, {"reason": "case_result_missing_or_stale", "wave": wave, "run_id": run_id, "case": case["id"]}
    return True, {"reason": "exact_current_provenance", "wave": wave, "run_id": run_id}


def git_add_commit(wave: str, run_id: str) -> None:
    struct_rel = Path("Configs/SpikeSamples/StructTrain")
    bin_paths = [
        str(struct_rel / "EXPERIMENTS.md"),
        str(struct_rel / "SUCCESSFUL_EXPERIMENTS.md"),
        str(struct_rel / "TimeLearnerMatrix" / wave / "results.json"),
        *[
            str(path.relative_to(BIN_ROOT))
            for path in sorted((MATRIX / wave / "run_results").glob(f"{run_id}-*.json"))
        ],
    ]
    ensure_no_staged_changes(BIN_ROOT)
    ensure_no_staged_changes(ROOT)
    run(["git", "add", "--", *bin_paths], BIN_ROOT)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BIN_ROOT)
    if staged.returncode != 0:
        run(["git", "commit", "-m", f"research(TimeLearner): record {wave} results"], BIN_ROOT)

    root_paths = [
        Path("Bin"),
        METRICS.relative_to(ROOT),
        WAVE_PLAN.relative_to(ROOT),
        FULL_MATRIX_REPORT.relative_to(ROOT),
    ]
    run(["git", "add", "--", *map(str, root_paths)], ROOT)
    staged_root = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged_root.returncode != 0:
        run(["git", "commit", "-m", f"research(TimeLearner): pin {wave} report"], ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--run-id", help="new unique output namespace; existing IDs require --resume")
    parser.add_argument("--resume", action="store_true", help="resume an existing run only after exact fingerprint validation")
    parser.add_argument("--allow-repeat", action="store_true", help="explicitly allow repeating an identical completed/incomplete condition in a new RUN_ID")
    parser.add_argument("--case", help="run one registered case from the selected wave (requires --no-commit)")
    parser.add_argument("--waves", nargs="+", help="run one wave, then stop for result analysis")
    parser.add_argument("--check-completed", metavar="WAVE", help="read-only exact-provenance validation used before skipping a prior wave")
    parser.add_argument("--quiet-debug-logs", action="store_true")
    parser.add_argument("--max-polls", type=int)
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="prepare+run only; skip updater and git commits (dual-host: train on remote, commit on local)",
    )
    args = parser.parse_args()
    if args.check_completed:
        valid, detail = completed_wave_matches_current(args.check_completed, args)
        print(json.dumps(detail, ensure_ascii=False, sort_keys=True), flush=True)
        return 0 if valid else 1
    if not args.waves:
        parser.error("--waves is required unless --check-completed is used")
    if args.jobs < 1 or args.jobs > 8:
        raise SystemExit("--jobs must be between 1 and 8; effective process count is capped at logical CPUs minus one")
    if args.max_polls is not None and args.max_polls < 1:
        raise SystemExit("--max-polls must be positive")
    if args.resume and not args.run_id:
        raise SystemExit("--resume requires an explicit --run-id")
    if args.resume and args.allow_repeat:
        raise SystemExit("--resume and --allow-repeat are mutually exclusive")
    run_id = args.run_id or os.environ.get("TIMELEARNER_MATRIX_RUN_ID") or (
        "matrix-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + f"-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    )
    registry = json.loads((MATRIX / "matrix.json").read_text(encoding="utf-8"))
    waves = args.waves
    if len(waves) != 1:
        raise SystemExit("run exactly one wave per invocation so its results can be reviewed before continuing")
    unknown_waves = [wave for wave in waves if wave not in registry.get("queue_order", [])]
    if unknown_waves:
        raise SystemExit(f"unknown wave(s): {unknown_waves}")
    wave = waves[0]
    specs = [case for case in registry["cases"] if case["wave"] == wave]
    if args.case:
        specs = [case for case in specs if case["id"] == args.case]
        if not specs:
            raise SystemExit(f"unknown case for {wave}: {args.case}")
        if not args.no_commit:
            raise SystemExit("single-case diagnostics require --no-commit")
    selected_ids = [case["id"] for case in specs]
    if args.resume:
        # Explicit, exact-resume is checked after preparation so the input hashes are fresh.
        pass
    elif (RUNS_BASE / run_id).exists():
        raise SystemExit(f"RUN_ID is already reserved: {RUNS_BASE / run_id}; choose a new ID or use --resume")
    if not args.no_commit:
        ensure_wave_paths_clean(wave)
        ensure_no_staged_changes(BIN_ROOT)
        ensure_no_staged_changes(ROOT)
    else:
        ensure_no_staged_changes(BIN_ROOT)
        ensure_no_staged_changes(ROOT)
    with exclusive_file_lock(QUEUE_LOCK, purpose=f"matrix run {run_id}"):
        os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id
        os.environ["TIMELEARNER_MATRIX_QUEUE_LOCKED"] = "1"
        print(f"Run ID: {run_id}", flush=True)
        print(f"Selected cases ({len(selected_ids)}): {', '.join(selected_ids)}", flush=True)
        print(f"=== {wave} prepare ===", flush=True)
        run([sys.executable, str(RUNNER), "--prepare", wave], BASE)
        fingerprint = make_run_fingerprint(wave, specs, args)
        runs = RUNS_BASE / run_id
        manifest_path = runs / "run_manifest.json"
        if args.resume:
            if not manifest_path.is_file():
                raise SystemExit(f"resume refused: run manifest does not exist: {manifest_path}")
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            verify_run_manifest(previous, fingerprint, run_id)
        else:
            duplicate = find_duplicate_run(fingerprint)
            duplicate_result = find_duplicate_result(wave, specs, fingerprint)
            if duplicate_result and not args.allow_repeat:
                raise SystemExit(
                    "matching completed result with exact code/Console/input provenance already exists: "
                    f"{duplicate_result}; inspect it or pass --allow-repeat with a new RUN_ID"
                )
            if duplicate and not args.allow_repeat:
                raise SystemExit(
                    f"identical experiment fingerprint already exists as RUN_ID={duplicate}; "
                    "inspect/reuse that run, or pass --allow-repeat with a new RUN_ID for a deliberate replicate"
                )
            runs = reserve_run_root(RUNS_BASE, run_id)
            manifest = {
                **fingerprint,
                "run_id": run_id,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "binary_sha256": fingerprint["console_sha256"],
                "selected_cases": selected_ids,
            }
            atomic_write_json(manifest_path, manifest, replace=False)
        os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id
        os.environ["TIMELEARNER_MATRIX_RUN_FINGERPRINT"] = fingerprint["run_fingerprint"]
        os.environ["TIMELEARNER_MATRIX_QUEUE_LOCKED"] = "1"
        queue_attempt_id, status_path = allocate_queue_status_attempt(runs)
        overall = {
            "run_id": run_id,
            "run_fingerprint": fingerprint["run_fingerprint"],
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "jobs": args.jobs,
            "no_commit": bool(args.no_commit),
            "selected_cases": selected_ids,
            "resumed": bool(args.resume),
            "queue_attempt": queue_attempt_id,
            "waves": {},
        }
        save_queue_status(runs, status_path, overall)
        print(f"Run fingerprint: {fingerprint['run_fingerprint']}", flush=True)
        if args.no_commit:
            print("Mode: --no-commit (prepare+run only; no updater/git)", flush=True)
        runner_command = [sys.executable, str(RUNNER), "--run", wave, "--jobs", str(args.jobs)]
        if args.case:
            runner_command.extend(("--case-ids", args.case))
        if args.quiet_debug_logs:
            runner_command.append("--quiet-debug-logs")
        if args.max_polls is not None:
            runner_command.extend(("--max-polls", str(args.max_polls)))
        run_result = run(runner_command, BASE, check=False)
        wave_status_file = runs / wave / "wave_status.json"
        wave_status = json.loads(wave_status_file.read_text(encoding="utf-8")) if wave_status_file.exists() else {}
        all_results = all(
            case_attempt_result(
                runs / wave / case["id"],
                case_id=case["id"],
                run_manifest={**fingerprint, "run_id": run_id, "binary_sha256": fingerprint["console_sha256"]},
                input_manifest_sha256=sha256_file(
                    MATRIX / wave / "inputs" / case["id"] / "matrix_input_manifest.json"
                ),
            ) is not None
            for case in specs
        )
        training_stops = int(wave_status.get("training_stop_cases", 0))
        evaluation_errors = int(wave_status.get("evaluation_error_cases", 0))
        quality_failures = int(wave_status.get("quality_failure_cases", 0))
        if args.no_commit:
            if not all_results:
                overall["waves"][wave] = {
                    "status": "paused_infrastructure_or_incomplete_results",
                    "runner_exit": run_result.returncode,
                    "run_complete": wave_status.get("run_complete"),
                    "all_results_saved": all_results,
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                }
                overall["status"] = "paused_infrastructure_or_incomplete_results"
                overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
                save_queue_status(runs, status_path, overall)
                print(f"PAUSED after {wave}: infrastructure or incomplete results (--no-commit)", flush=True)
                return 2
            overall["waves"][wave] = {
                "status": (
                    "completed_checkpoint_required"
                    if training_stops or evaluation_errors
                    else "completed_awaiting_local_commit"
                ),
                "runner_exit": run_result.returncode,
                "training_stop_cases": training_stops,
                "evaluation_error_cases": evaluation_errors,
                "quality_failure_cases": quality_failures,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            save_queue_status(runs, status_path, overall)
            if run_result.returncode != 0 or training_stops or evaluation_errors:
                print(
                    f"PAUSED after {wave}: training non-convergence/refusal or evaluation error "
                    f"(--no-commit; rsync RUN_ID then updater+commit on local)",
                    flush=True,
                )
                overall["status"] = "paused_after_training_or_evaluation_issue"
                overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
                save_queue_status(runs, status_path, overall)
                return run_result.returncode or 1
            print(
                f"WAVE RUN COMPLETE {wave}; quality failures={quality_failures}; "
                f"--no-commit: rsync {runs} then update+commit on local",
                flush=True,
            )
            overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
            overall["status"] = "queue_completed_no_commit"
            save_queue_status(runs, status_path, overall)
            return 0
        if not all_results:
            print(f"=== {wave} incomplete; preserve artifacts for exact resume ===", flush=True)
            if args.case:
                save_queue_status(runs, status_path, overall)
                print("PARTIAL CASE NOT REPORTED/COMMITTED; inspect RUN_ID artifacts", flush=True)
                return 2
            overall["waves"][wave] = {
                "status": "paused_infrastructure_or_incomplete_results",
                "runner_exit": run_result.returncode,
                "run_complete": wave_status.get("run_complete"),
                "all_results_saved": all_results,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            overall["status"] = "paused_infrastructure_or_incomplete_results"
            overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
            save_queue_status(runs, status_path, overall)
            print(
                f"PAUSED after {wave}: infrastructure or incomplete results; nothing committed, "
                "resume this RUN_ID only if the full fingerprint still matches",
                flush=True,
            )
            return 2
        print(f"=== {wave} report and commits ===", flush=True)
        if args.case:
            save_queue_status(runs, status_path, overall)
            print("PARTIAL CASE NOT REPORTED/COMMITTED; inspect RUN_ID artifacts", flush=True)
            return 0
        run([sys.executable, str(UPDATER), wave], BASE)
        git_add_commit(wave, run_id)
        overall["waves"][wave] = {
            "status": "completed_and_committed_checkpoint_required" if training_stops or evaluation_errors else "completed_and_committed",
            "runner_exit": run_result.returncode,
            "training_stop_cases": training_stops,
            "evaluation_error_cases": evaluation_errors,
            "quality_failure_cases": quality_failures,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "bin_head": git_text(BIN_ROOT, "rev-parse", "HEAD"),
            "root_head": git_text(ROOT, "rev-parse", "HEAD"),
        }
        save_queue_status(runs, status_path, overall)
        if run_result.returncode != 0 or training_stops or evaluation_errors:
            print(f"PAUSED after {wave}: training non-convergence/refusal or evaluation error; wave was reported and committed", flush=True)
            overall["status"] = "paused_after_training_or_evaluation_issue"
            overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
            save_queue_status(runs, status_path, overall)
            return run_result.returncode or 1
        print(f"WAVE REPORTED AND COMMITTED {wave}; quality failures={quality_failures}; review before the next invocation", flush=True)
        overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
        overall["status"] = "queue_completed"
        save_queue_status(runs, status_path, overall)
        print("QUEUE COMPLETED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
