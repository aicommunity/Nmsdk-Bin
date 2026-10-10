#!/usr/bin/env python3
"""Run the registered wave queue, updating docs and committing each completed wave."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BIN_ROOT = BASE.parents[2]
ROOT = BIN_ROOT.parent
RUNS = BASE / "_repro" / "TimeLearnerMatrixRuns"
MATRIX = BASE / "TimeLearnerMatrix"
METRICS = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "evidence" / "metrics" / "TIMELEARNER_MATRIX_WAVES_20261010.md"
RUNNER = BASE / "scripts" / "timelearner_matrix.py"
UPDATER = BASE / "scripts" / "update_timelearner_matrix_report.py"


def run(command: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, text=True, check=check)


def git_text(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def git_add_commit(wave: str) -> None:
    struct_rel = Path("Configs/SpikeSamples/StructTrain")
    bin_paths = [
        str(struct_rel / "EXPERIMENTS.md"),
        str(struct_rel / "SUCCESSFUL_EXPERIMENTS.md"),
        str(struct_rel / "TimeLearnerMatrix"),
        str(struct_rel / "scripts/timelearner_matrix.py"),
        str(struct_rel / "scripts/posttune_verify.py"),
        str(struct_rel / "scripts/update_timelearner_matrix_report.py"),
        str(struct_rel / "scripts/run_timelearner_matrix_queue.py"),
    ]
    run(["git", "add", "--", *bin_paths], BIN_ROOT)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BIN_ROOT)
    if staged.returncode != 0:
        run(["git", "commit", "-m", f"research(TimeLearner): record {wave} results"], BIN_ROOT)

    run(["git", "add", "--", "Bin", str(METRICS.relative_to(ROOT))], ROOT)
    staged_root = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged_root.returncode != 0:
        run(["git", "commit", "-m", f"research(TimeLearner): pin {wave} report"], ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--from-wave", help="start from this wave; prior results are preserved")
    parser.add_argument("--waves", nargs="*", help="optional explicit wave ids")
    args = parser.parse_args()
    registry = json.loads((MATRIX / "matrix.json").read_text(encoding="utf-8"))
    waves = args.waves or registry.get("queue_order", [])
    if args.from_wave:
        if args.from_wave not in waves:
            raise SystemExit(f"wave {args.from_wave} not in queue: {waves}")
        waves = waves[waves.index(args.from_wave):]
    if not waves:
        raise SystemExit("matrix queue is empty")
    status_path = RUNS / "queue_status.json"
    overall = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "jobs": args.jobs,
        "waves": {},
    }
    status_path.parent.mkdir(parents=True, exist_ok=True)
    for wave in waves:
        print(f"=== {wave} prepare ===", flush=True)
        run([sys.executable, str(RUNNER), "--prepare", wave], BASE)
        print(f"=== {wave} run ===", flush=True)
        run_result = run([sys.executable, str(RUNNER), "--run", wave, "--jobs", str(args.jobs)], BASE, check=False)
        wave_status_file = RUNS / wave / "wave_status.json"
        wave_status = json.loads(wave_status_file.read_text(encoding="utf-8")) if wave_status_file.exists() else {}
        all_results = all(
            (RUNS / wave / case["id"] / "matrix_result.json").is_file()
            for case in registry["cases"] if case["wave"] == wave
        )
        if run_result.returncode != 0 or not wave_status.get("run_complete") or not all_results:
            overall["waves"][wave] = {
                "status": "paused_infrastructure_or_incomplete_results",
                "runner_exit": run_result.returncode,
                "run_complete": wave_status.get("run_complete"),
                "all_results_saved": all_results,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
            print(f"PAUSED after {wave}: infrastructure or incomplete results", flush=True)
            return 2
        print(f"=== {wave} report and commits ===", flush=True)
        run([sys.executable, str(UPDATER), wave], BASE)
        git_add_commit(wave)
        overall["waves"][wave] = {
            "status": "completed_and_committed",
            "runner_exit": run_result.returncode,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "bin_head": git_text(BIN_ROOT, "rev-parse", "HEAD"),
            "root_head": git_text(ROOT, "rev-parse", "HEAD"),
        }
        status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
        print(f"COMMITTED {wave}", flush=True)
    overall["finished_utc"] = datetime.now(timezone.utc).isoformat()
    overall["status"] = "queue_completed"
    status_path.write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
    print("QUEUE COMPLETED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
