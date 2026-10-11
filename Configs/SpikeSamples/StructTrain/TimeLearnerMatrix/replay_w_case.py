#!/usr/bin/env python3
"""Replay one archived W01-W04 condition with the current C++ trainer.

This file only prepares an isolated workdir, invokes NeuroModelerConsole via
posttune_verify, and records provenance. Learning remains in the C++ trainer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
STRUCT_ROOT = HERE.parent
REPO_ROOT = HERE.parents[4]
SCRIPT_ROOT = STRUCT_ROOT / "scripts"
DEFAULT_OUTPUT_ROOT = STRUCT_ROOT / "_repro" / "runs"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def git_head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="W01-W04 case ID from results.json")
    parser.add_argument("--console", type=Path, default=REPO_ROOT / "Bin/Platform/Win/NeuroModelerConsole.exe")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--max-polls", type=int, default=401)
    parser.add_argument("--autosave-model-s", type=int, default=1)
    parser.add_argument(
        "--keep-train-statistic-logs",
        action="store_true",
        help="keep expensive per-step UStatisticDoubleMatrix output files",
    )
    parser.add_argument("--stall-autosave-n", type=int, default=10)
    parser.add_argument("--slog-abort-gib", type=float, default=8.0)
    args = parser.parse_args()

    wave = args.case[:3]
    if wave not in {"W01", "W02", "W03", "W04"}:
        parser.error("case must be a W01-W04 ID")
    wave_root = HERE / wave
    result_file = wave_root / "results.json"
    source = wave_root / "inputs" / args.case
    if not result_file.is_file() or not source.is_dir():
        parser.error(f"archived inputs/results not found for {args.case}")

    archived_cases = json.loads(result_file.read_text(encoding="utf-8"))["cases"]
    row = next((case for case in archived_cases if case["case"] == args.case), None)
    if row is None:
        parser.error(f"case ID is not listed in {result_file}")

    sys.path.insert(0, str(SCRIPT_ROOT))
    import posttune_verify as pv  # type: ignore[import-not-found]

    pv.NMSDK_ROOT = REPO_ROOT
    pv.NM = args.console.resolve()
    pv.RUNS_ROOT = args.output_root.resolve()
    if not pv.NM.is_file():
        parser.error(f"Console not found: {pv.NM}")
    os.environ["NMSDK_CONSOLE"] = str(pv.NM)
    qt_bin = Path(r"C:\Qt\5.15.2\msvc2019_64\bin")
    os.environ["PATH"] = os.pathsep.join(
        str(path) for path in (pv.NM.parent, qt_bin, Path(os.environ.get("PATH", ".")))
    )

    factors = row["factors"]
    historical_result = row.get("result", {})
    trainer = str(factors["trainer"])
    kind = "branch" if trainer.endswith("Branch") else "asym"
    span_ms = int(factors["duration_ms"])
    train_t = float(factors["train_t"])
    config = pv._case(
        source,
        train_t=train_t,
        span_ms=span_ms,
        kind=kind,
        expect_tipr=str(historical_result.get("expect_tipr") or "flat"),
        skip_tipr_mid=True,
        expect_fires=historical_result.get("expect_fires"),
        gold=source,
    )
    config.update(
        {
            "normalization_mode": int(factors["normalization_mode"]),
            "presynaptic_inhibition": bool(factors["presynaptic_inhibition"]),
            "presynaptic_coefficient": float(factors["presynaptic_coefficient"]),
            "enable_posttrain_tuning": "0",
        }
    )
    pv.CASES[args.case] = config

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_started_utc = datetime.now(timezone.utc).isoformat()
    run_dir = args.output_root.resolve() / f"{args.case}_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    hashes_before = tree_hashes(source)
    commits_at_start = {
        "root": git_head(REPO_ROOT),
        "pulselib": git_head(REPO_ROOT / "Libraries/Nmsdk-PulseLib"),
        "bin": git_head(REPO_ROOT / "Bin"),
    }
    console_sha256_at_start = sha256(pv.NM)
    runner_sha256 = sha256(Path(__file__).resolve())
    pv.OUT = run_dir / "summary.md"
    result: dict[str, Any] = pv.run_case(
        args.case,
        run_dir=run_dir,
        train_t=train_t,
        max_polls=args.max_polls,
        no_prune=True,
        snap_every=10,
        autosave_model_s=args.autosave_model_s,
        stall_autosave_n=args.stall_autosave_n,
        slog_abort_gib=args.slog_abort_gib,
        disable_train_statistic_logs=not args.keep_train_statistic_logs,
    )
    hashes_after = tree_hashes(source)
    record = {
        "case": args.case,
        "wave": wave,
        "factors": factors,
        "historical_result": historical_result,
        "source_input_dir": str(source),
        "source_input_hashes_before": hashes_before,
        "source_input_hashes_after": hashes_after,
        "source_inputs_unchanged": hashes_before == hashes_after,
        "run_started_utc": run_started_utc,
        "commits_at_start": commits_at_start,
        "commits_at_completion": {
            "root": git_head(REPO_ROOT),
            "pulselib": git_head(REPO_ROOT / "Libraries/Nmsdk-PulseLib"),
            "bin": git_head(REPO_ROOT / "Bin"),
        },
        "runner_sha256": runner_sha256,
        "console": str(pv.NM),
        "console_sha256": console_sha256_at_start,
        "max_polls": args.max_polls,
        "autosave_model_seconds": args.autosave_model_s,
        "train_statistic_logs_disabled": not args.keep_train_statistic_logs,
        "stall_autosave_n": args.stall_autosave_n,
        "result": result,
    }
    (run_dir / "replay_summary.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "case": args.case,
                "train_status": result.get("train_status"),
                "need": result.get("after", {}).get("IsNeedToTrain"),
                "source_inputs_unchanged": record["source_inputs_unchanged"],
                "run_dir": str(run_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
