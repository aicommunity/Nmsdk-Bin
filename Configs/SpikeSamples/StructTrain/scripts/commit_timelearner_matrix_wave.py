#!/usr/bin/env python3
"""Commit one finished TimeLearner matrix wave on the local commit-host.

Train hosts use ``run_timelearner_matrix_queue.py --no-commit``. After a wave
finishes (local RUN_ID or rsync from .17), call this script once per wave:

  TIMELEARNER_MATRIX_RUN_ID=run-17-… \\
    python3 scripts/commit_timelearner_matrix_wave.py W04 --host-tag host=17

  python3 scripts/commit_timelearner_matrix_wave.py W02 \\
    --run-id run-local-… --host-tag host=local --push

Uses ``_repro/.matrix_commit.lock`` so only one updater/commit runs at a time.
Does **not** require a clean Bin gitlink (untracked clutter OK); only refuses
pre-staged changes in Bin/root.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from matrix_run_safety import resolve_runs_base

BASE = Path(__file__).resolve().parents[1]
BIN_ROOT = BASE.parents[2]
ROOT = BIN_ROOT.parent
RUNS_BASE = resolve_runs_base(BASE / "_repro" / "TimeLearnerMatrixRuns")
UPDATER = BASE / "scripts" / "update_timelearner_matrix_report.py"
LOCK = BASE / "_repro" / ".matrix_commit.lock"
METRICS = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "evidence" / "metrics" / "TIMELEARNER_MATRIX_WAVES_20261010.md"
WAVE_PLAN = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "plans" / "TimeLearner-full-matrix-waves-20261010.ru.md"
FULL_MATRIX_REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "TIMELEARNER_FULL_MATRIX_AND_HISTORY_2026-10-10.ru.md"


def run(cmd: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=str(cwd), check=check)


def git_text(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def ensure_no_staged(path: Path) -> None:
    staged = git_text(path, "diff", "--cached", "--name-only")
    if staged:
        raise SystemExit(f"refusing pre-staged changes in {path}:\n{staged}")


def acquire_lock(timeout_s: int = 7200) -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout_s
    while True:
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, f"pid={os.getpid()}\n".encode())
            os.close(fd)
            return
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"commit lock busy: {LOCK}")
            time.sleep(2)


def release_lock() -> None:
    try:
        LOCK.unlink(missing_ok=True)
    except TypeError:
        if LOCK.exists():
            LOCK.unlink()


def rsync_from_17(run_id: str, ssh_host: str) -> None:
    src = f"{ssh_host}:/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/{run_id}/"
    dst = RUNS_BASE / run_id
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.mkdir(exist_ok=False)
    if os.environ.get("SSHPASS"):
        cmd = ["sshpass", "-e", "rsync", "-a", "-e", "ssh -o StrictHostKeyChecking=accept-new", src, str(dst) + "/"]
    else:
        cmd = ["rsync", "-a", src, str(dst) + "/"]
    run(cmd, ROOT)


def git_add_commit(wave: str, host_tag: str, run_id: str) -> None:
    struct_rel = Path("Configs/SpikeSamples/StructTrain")
    bin_paths = [
        str(struct_rel / "EXPERIMENTS.md"),
        str(struct_rel / "SUCCESSFUL_EXPERIMENTS.md"),
        str(struct_rel / "TimeLearnerMatrix" / wave / "results.json"),
        *[
            str(path.relative_to(BIN_ROOT))
            for path in sorted((BASE / "TimeLearnerMatrix" / wave / "run_results").glob(f"{run_id}-*.json"))
        ],
    ]
    ensure_no_staged(BIN_ROOT)
    ensure_no_staged(ROOT)
    run(["git", "add", "--", *bin_paths], BIN_ROOT)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BIN_ROOT)
    suffix = f" ({host_tag})" if host_tag else ""
    if staged.returncode != 0:
        run(["git", "commit", "-m", f"research(TimeLearner): record {wave} results{suffix}"], BIN_ROOT)

    root_paths = [
        "Bin",
        str(METRICS.relative_to(ROOT)),
        str(WAVE_PLAN.relative_to(ROOT)),
        str(FULL_MATRIX_REPORT.relative_to(ROOT)),
    ]
    run(["git", "add", "--", *root_paths], ROOT)
    staged_root = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged_root.returncode != 0:
        run(["git", "commit", "-m", f"research(TimeLearner): pin {wave} report{suffix}"], ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wave", help="e.g. W04")
    ap.add_argument("--run-id", help="defaults to TIMELEARNER_MATRIX_RUN_ID")
    ap.add_argument("--host-tag", default="", help="suffix in commit message, e.g. host=17")
    ap.add_argument("--rsync-from-17", action="store_true", help="rsync RUN_ID from .17 before updater")
    ap.add_argument("--ssh-host", default=os.environ.get("TIMELEARNER_MATRIX_SSH", "user@10.245.1.17"))
    ap.add_argument("--push", action="store_true", help="git push Bin then root after commit")
    ap.add_argument("--skip-lock", action="store_true")
    args = ap.parse_args()

    run_id = args.run_id or os.environ.get("TIMELEARNER_MATRIX_RUN_ID", "").strip()
    if not run_id:
        raise SystemExit("--run-id or TIMELEARNER_MATRIX_RUN_ID required")
    os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id

    if args.rsync_from_17:
        rsync_from_17(run_id, args.ssh_host)

    run_dir = RUNS_BASE / run_id
    if not (run_dir / args.wave).is_dir():
        raise SystemExit(f"missing wave dir: {run_dir / args.wave}")
    manifest = run_dir / "run_manifest.json"
    status = run_dir / "queue_status.json"
    if not manifest.is_file() or not status.is_file():
        raise SystemExit(f"refuse to report a run without immutable provenance/status: {run_dir}")
    run_manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    wave_status_path = run_dir / args.wave / "wave_status.json"
    wave_status_data = json.loads(wave_status_path.read_text(encoding="utf-8")) if wave_status_path.is_file() else {}
    registry = json.loads((BASE / "TimeLearnerMatrix" / "matrix.json").read_text(encoding="utf-8"))
    expected_cases = {case["id"] for case in registry.get("cases", []) if case.get("wave") == args.wave}
    if set(run_manifest_data.get("selected_cases", [])) != expected_cases:
        raise SystemExit("refuse to publish a partial case selection as a completed wave")
    if not wave_status_data.get("run_complete"):
        raise SystemExit("refuse to report a wave with missing/invalid case results")

    if not args.skip_lock:
        acquire_lock()
    try:
        run([sys.executable, str(UPDATER), args.wave], BASE)
        git_add_commit(args.wave, args.host_tag, run_id)
    finally:
        if not args.skip_lock:
            release_lock()

    if args.push:
        run(["git", "push", "origin", "HEAD"], BIN_ROOT, check=False)
        run(["git", "push", "origin", "HEAD"], ROOT, check=False)

    print(f"COMMITTED {args.wave} from {run_id}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
