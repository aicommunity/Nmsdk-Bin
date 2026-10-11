#!/usr/bin/env python3
"""Run the registered wave queue, updating docs and committing each completed wave."""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def git_add_commit(wave: str) -> None:
    struct_rel = Path("Configs/SpikeSamples/StructTrain")
    bin_paths = [
        str(struct_rel / "EXPERIMENTS.md"),
        str(struct_rel / "SUCCESSFUL_EXPERIMENTS.md"),
        str(struct_rel / "TimeLearnerMatrix" / wave / "results.json"),
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
    parser.add_argument("--run-id", help="unique output namespace; reuse only to resume this run")
    parser.add_argument("--waves", nargs="+", required=True, help="run one wave, then stop for result analysis")
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 8:
        raise SystemExit("--jobs must be between 1 and 8")
    run_id = args.run_id or os.environ.get("TIMELEARNER_MATRIX_RUN_ID") or (
        "matrix-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"
    )
    runs = run_root(run_id)
    registry = json.loads((MATRIX / "matrix.json").read_text(encoding="utf-8"))
    waves = args.waves
    if len(waves) != 1:
        raise SystemExit("run exactly one wave per invocation so its results can be reviewed before continuing")
    unknown_waves = [wave for wave in waves if wave not in registry.get("queue_order", [])]
    if unknown_waves:
        raise SystemExit(f"unknown wave(s): {unknown_waves}")
    ensure_wave_paths_clean(waves[0])
    ensure_no_staged_changes(BIN_ROOT)
    ensure_no_staged_changes(ROOT)
    status_path = runs / "queue_status.json"
    overall = {
        "run_id": run_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "jobs": args.jobs,
        "waves": {},
    }
    status_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Run ID: {run_id}", flush=True)
    for wave in waves:
        print(f"=== {wave} prepare ===", flush=True)
        run([sys.executable, str(RUNNER), "--prepare", wave], BASE)
        print(f"=== {wave} run ===", flush=True)
        run_result = run([sys.executable, str(RUNNER), "--run", wave, "--jobs", str(args.jobs)], BASE, check=False)
        wave_status_file = runs / wave / "wave_status.json"
        wave_status = json.loads(wave_status_file.read_text(encoding="utf-8")) if wave_status_file.exists() else {}
        all_results = all(
            (runs / wave / case["id"] / "matrix_result.json").is_file()
            for case in registry["cases"] if case["wave"] == wave
        )
        if not all_results:
            print(f"=== {wave} partial report and commits ===", flush=True)
            run([sys.executable, str(UPDATER), wave], BASE)
            git_add_commit(wave)
            overall["waves"][wave] = {
                "status": "paused_infrastructure_or_incomplete_results",
                "runner_exit": run_result.returncode,
                "run_complete": wave_status.get("run_complete"),
                "all_results_saved": all_results,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            overall["status"] = "paused_infrastructure_or_incomplete_results"
            overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
            status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
            print(f"PAUSED after {wave}: infrastructure or incomplete results", flush=True)
            return 2
        print(f"=== {wave} report and commits ===", flush=True)
        run([sys.executable, str(UPDATER), wave], BASE)
        git_add_commit(wave)
        training_stops = int(wave_status.get("training_stop_cases", 0))
        evaluation_errors = int(wave_status.get("evaluation_error_cases", 0))
        quality_failures = int(wave_status.get("quality_failure_cases", 0))
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
        status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
        if run_result.returncode != 0 or training_stops or evaluation_errors:
            print(f"PAUSED after {wave}: training non-convergence/refusal or evaluation error; wave was reported and committed", flush=True)
            overall["status"] = "paused_after_training_or_evaluation_issue"
            overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
            status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
            return run_result.returncode or 1
        print(f"WAVE REPORTED AND COMMITTED {wave}; quality failures={quality_failures}; review before the next invocation", flush=True)
    overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
    overall["status"] = "queue_completed"
    status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
    print("QUEUE COMPLETED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
