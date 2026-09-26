#!/usr/bin/env python3
"""GoldTest retest for NOT_RETESTED rows only (no Train, no soft-cold).

Reads a TSV manifest (kind\\tname\\tTest_rel), runs NeuroModelerConsole on each
Test/Project.ini, classifies SelectivityLog/results.csv, writes GOLD_RETEST CSV.

Env:
  NM, TIMEOUT_SEC (default floor), PARALLEL (default 3)
Span-aware TEST_SIM_T: 25→40, 50→80, 100→120, 480→120 (override with --test-sim-t >0).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NM = Path(os.environ.get("NM", "/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole"))
sys.path.insert(0, str(ROOT / "scripts"))
from selectivity_metrics import classify  # noqa: E402


def load_manifest(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        kind, name, test_rel = parts[0], parts[1], parts[2]
        if kind == "OUT" or not test_rel:
            continue
        rows.append((kind, name, test_rel))
    return rows


def infer_sim_t(test_rel: str, override: float) -> float:
    if override > 0:
        return override
    s = test_rel.lower()
    if "480" in s or "span400" in s or "span300" in s:
        return 120.0
    if "span200" in s or "span100" in s or "_span100" in s:
        return 120.0
    if "span50" in s or "_span50" in s:
        return 80.0
    if "span25" in s or "_span25" in s:
        return 40.0
    return 40.0


def infer_timeout(sim_t: float, floor: int) -> int:
    # wall clock: analyzer often needs >> model seconds on debug Console
    return max(floor, int(sim_t * 25), 900)


def _csv_nrows(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    try:
        with csv_path.open(encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)
    except OSError:
        return 0


def run_nm_gate(ini: Path, csv_path: Path, *, test_sim_t: float, timeout_sec: int) -> tuple[int, str]:
    """Run Console Test; SIGTERM/KILL when CSV has ≥8 rows."""
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(test_sim_t), "-x"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        return -1, str(e)
    hard = time.time() + timeout_sec
    err = ""
    while proc.poll() is None:
        if time.time() > hard:
            err = "timeout"
            proc.terminate()
            break
        n = _csv_nrows(csv_path)
        if n >= 8:
            time.sleep(2.0)
            if proc.poll() is None:
                err = "sigterm_csv8"
                proc.terminate()
            break
        time.sleep(2.0)
    try:
        rc = proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            rc = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            rc = -9
        err = err or "kill_after_term"
    return rc, err


def run_one(
    kind: str,
    name: str,
    test_rel: str,
    *,
    timeout_floor: int,
    test_sim_t_override: float,
    console_sha16: str,
) -> dict[str, str]:
    test = ROOT / test_rel
    ini = test / "Project.ini"
    csv_path = test / "SelectivityLog" / "results.csv"
    slog = test / "StatisticLog"
    if slog.is_dir():
        subprocess.call(["rm", "-rf", str(slog)])
    sim_t = infer_sim_t(test_rel, test_sim_t_override)
    timeout_sec = infer_timeout(sim_t, timeout_floor)
    started = time.time()
    rc = -1
    err = ""
    if not ini.exists():
        err = "missing_ini"
    else:
        if csv_path.exists():
            csv_path.unlink()
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        rc, err = run_nm_gate(
            ini, csv_path, test_sim_t=sim_t, timeout_sec=timeout_sec
        )

    metrics: dict = {}
    if csv_path.exists():
        try:
            with csv_path.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            metrics = classify(rows)
        except OSError as e:
            err = err or f"csv_read:{e}"

    acc = int(metrics.get("acc", 0) or 0)
    n = int(metrics.get("n", 0) or 0)
    target = int(metrics.get("target_hit", 0) or 0)
    mode = str(metrics.get("mode", metrics.get("mode_legacy", "")) or "")
    fires = str(metrics.get("fires", "") or "")
    ok_audit = int(metrics.get("ok_audit", 0) or 0)

    gate_ok = n >= 8 and err in ("", "sigterm_csv8")
    if not gate_ok or n == 0 or err in ("timeout", "missing_ini", "kill_after_term"):
        head = "FAIL"
    elif mode == "selective" and acc == 8 and fires == "10000000":
        head = "PASS"
    elif mode == "selective" and acc >= 7 and fires.startswith("1"):
        head = "PASS"
    elif n == 8 and target == 1 and acc >= 4 and mode in ("selective", "partial_FA"):
        head = "PASS"
    else:
        head = "FAIL"

    return {
        "kind": kind,
        "name": name,
        "test_rel": test_rel,
        "acc": f"{acc}/{n}" if n else "—",
        "target": "да" if target else ("нет" if n else "—"),
        "mode": mode or "—",
        "fires": fires or "—",
        "ok_audit": str(ok_audit),
        "head": head,
        "rc": str(rc),
        "err": err,
        "sim_t": str(sim_t),
        "elapsed_s": f"{time.time() - started:.1f}",
        "console_sha16": console_sha16,
        "utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    }


def parse_done_names(resume_log: Path) -> set[str]:
    done: set[str] = set()
    if not resume_log.exists():
        return done
    for line in resume_log.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[\d+/\d+\] (\S+) (PASS|FAIL) ", line)
        if m and m.group(2) == "PASS":
            done.add(m.group(1))
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "_repro" / "NOT_RETESTED_manifest_20260925.txt",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT
        / "_repro"
        / f"GOLD_RETEST_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv",
    )
    ap.add_argument("--parallel", type=int, default=int(os.environ.get("PARALLEL", "3")))
    ap.add_argument(
        "--timeout-sec",
        type=int,
        default=int(os.environ.get("TIMEOUT_SEC", "900")),
        help="floor; actual timeout is max(floor, sim_t*25)",
    )
    ap.add_argument(
        "--test-sim-t",
        type=float,
        default=0.0,
        help="0 = span-aware auto",
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--resume-log",
        type=Path,
        default=None,
        help="skip names already PASS in this log",
    )
    ap.add_argument("--only-fail-from-log", type=Path, default=None)
    args = ap.parse_args()

    if not NM.is_file():
        print(f"missing NM: {NM}", file=sys.stderr)
        return 2
    console_sha = hashlib.sha256(NM.read_bytes()).hexdigest()
    rows = load_manifest(args.manifest)
    if args.only_fail_from_log and args.only_fail_from_log.exists():
        fails: set[str] = set()
        for line in args.only_fail_from_log.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\[\d+/\d+\] (\S+) FAIL ", line)
            if m:
                fails.add(m.group(1))
            # also names not yet started: handled via resume
        # include unfinished = all - PASS from same log
        done_pass = parse_done_names(args.only_fail_from_log)
        started = set()
        for line in args.only_fail_from_log.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\[\d+/\d+\] (\S+) ", line)
            if m:
                started.add(m.group(1))
        need = fails | ({r[1] for r in rows} - done_pass)
        # Prefer: not-yet-PASS remainder of manifest
        rows = [r for r in rows if r[1] not in done_pass]
        print(f"resume: skip PASS={len(done_pass)}; remaining={len(rows)}")
    elif args.resume_log:
        done = parse_done_names(args.resume_log)
        rows = [r for r in rows if r[1] not in done]
        print(f"resume-log skip PASS={len(done)}; remaining={len(rows)}")
    if args.limit > 0:
        rows = rows[: args.limit]
    print(
        f"GoldTest batch: {len(rows)} tests PARALLEL={args.parallel} "
        f"sim_t={'auto' if args.test_sim_t <= 0 else args.test_sim_t} "
        f"timeout_floor={args.timeout_sec} Console={console_sha[:16]}"
    )

    results: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        futs = {
            ex.submit(
                run_one,
                kind,
                name,
                test_rel,
                timeout_floor=args.timeout_sec,
                test_sim_t_override=args.test_sim_t,
                console_sha16=console_sha[:16],
            ): name
            for kind, name, test_rel in rows
        }
        done_n = 0
        for fut in as_completed(futs):
            done_n += 1
            r = fut.result()
            results.append(r)
            print(
                f"[{done_n}/{len(rows)}] {r['name']} {r['head']} "
                f"Acc={r['acc']} fires={r['fires']} sim_t={r['sim_t']} "
                f"rc={r['rc']} {r['err']}",
                flush=True,
            )

    results.sort(key=lambda r: (r["kind"], r["test_rel"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "kind",
        "name",
        "test_rel",
        "acc",
        "target",
        "mode",
        "fires",
        "ok_audit",
        "head",
        "rc",
        "err",
        "sim_t",
        "elapsed_s",
        "console_sha16",
        "utc",
    ]
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, "") for k in fields})
    n_pass = sum(1 for r in results if r["head"] == "PASS")
    n_fail = sum(1 for r in results if r["head"] == "FAIL")
    print(f"Wrote {args.out} PASS={n_pass} FAIL={n_fail} total={len(results)}")
    print(f"console_sha256={console_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
