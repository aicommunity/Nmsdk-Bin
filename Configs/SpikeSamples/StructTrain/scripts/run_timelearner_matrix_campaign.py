#!/usr/bin/env python3
"""Dual-host TimeLearner matrix campaign: run all assigned waves; analyze later.

Continues after training_stop / evaluation_error / quality_fail.
Stops only on infrastructure / incomplete results (unless --retry-infra).

Roles:
  local  — full queue (updater+commit) for LOCAL_WAVES; also ingests .17 waves
  remote — --no-commit only (use on .17); local must ingest

Environment:
  TIMELEARNER_MATRIX_SSH — default user@10.245.1.17 (local ingest)
  SSHPASS — for sshpass when ingesting
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BIN_ROOT = BASE.parents[2]
ROOT = BIN_ROOT.parent
SCRIPTS = BASE / "scripts"
QUEUE = SCRIPTS / "run_timelearner_matrix_queue.py"
UPDATER = SCRIPTS / "update_timelearner_matrix_report.py"
RUNS_BASE = BASE / "_repro" / "TimeLearnerMatrixRuns"
LOCK = BASE / "_repro" / ".matrix_commit.lock"
ARCHIVE_17 = "/media/user/Data/NmsdkStructTrainArchive/matrix_runs"
LOG_DIR = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "evidence" / "metrics"

# Plan split (~2:3). W01 already completed on .17.
WAVES_17 = [
    "W04", "W06", "W07", "W46", "W47", "W10", "W12", "W13", "W15", "W17", "W19",
    "W45", "W21", "W23", "W25", "W26", "W28", "W30", "W32", "W34", "W35", "W36",
    "W38", "W40", "W41", "W42", "W43", "W44",
]
WAVES_LOCAL = [
    "W02", "W03", "W05", "W08", "W09", "W11", "W14", "W16", "W18", "W20", "W22",
    "W24", "W27", "W29", "W31", "W33", "W37", "W39",
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    log("+ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check, env=env)


def acquire_lock(timeout_s: int = 7200) -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout_s
    while True:
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, f"pid={os.getpid()} utc={utc_stamp()}\n".encode())
            os.close(fd)
            return
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"commit lock busy: {LOCK}")
            time.sleep(5)


def release_lock() -> None:
    try:
        LOCK.unlink(missing_ok=True)
    except TypeError:
        if LOCK.exists():
            LOCK.unlink()


def make_run_id(prefix: str) -> str:
    return f"{prefix}-{utc_stamp()}-{os.getpid()}"


def wave_done_locally(wave: str) -> bool:
    p = BASE / "TimeLearnerMatrix" / wave / "results.json"
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(data.get("run_complete")) and bool(data.get("cases"))


def run_local_wave(wave: str, jobs: int) -> int:
    if wave_done_locally(wave):
        log(f"SKIP {wave}: results.json already run_complete")
        return 0
    run_id = make_run_id("run-local")
    env = os.environ.copy()
    env["TIMELEARNER_MATRIX_RUN_ID"] = run_id
    log(f"LOCAL TRAIN {wave} RUN_ID={run_id}")
    acquire_lock()
    try:
        # ensure clean staged before queue
        run(["git", "diff", "--cached", "--quiet"], cwd=BIN_ROOT, check=False)
        run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=False)
        cp = run(
            [sys.executable, "-u", str(QUEUE), "--run-id", run_id, "--waves", wave, "--jobs", str(jobs)],
            cwd=BASE,
            check=False,
            env=env,
        )
    finally:
        release_lock()
    # 0 = clean; 1 = training/eval issues but committed; 2 = infra
    if cp.returncode == 2:
        log(f"INFRA FAIL local {wave} rc=2 RUN_ID={run_id}")
        return 2
    if cp.returncode not in (0, 1):
        # queue returns runner rc or 1 after commit on train issues
        st = RUNS_BASE / run_id / "queue_status.json"
        if st.is_file():
            status = json.loads(st.read_text(encoding="utf-8")).get("status", "")
            if "committed" in status or "checkpoint" in status:
                log(f"CONTINUE after local {wave} rc={cp.returncode} status={status}")
                _push_after_commit()
                return 0
        log(f"UNEXPECTED local {wave} rc={cp.returncode}")
        return cp.returncode
    _push_after_commit()
    log(f"OK local {wave} (rc={cp.returncode}) — continue campaign")
    return 0


def _push_after_commit() -> None:
    run(["git", "-C", str(BIN_ROOT), "push", "origin", "HEAD"], check=False)
    run(["git", "-C", str(ROOT), "push", "origin", "HEAD"], check=False)


def ssh_base() -> list[str]:
    host = os.environ.get("TIMELEARNER_MATRIX_SSH", "user@10.245.1.17")
    if os.environ.get("SSHPASS"):
        return ["sshpass", "-e", "ssh", "-o", "StrictHostKeyChecking=accept-new", host]
    return ["ssh", "-o", "StrictHostKeyChecking=accept-new", host]


def rsync_base() -> list[str]:
    host = os.environ.get("TIMELEARNER_MATRIX_SSH", "user@10.245.1.17")
    if os.environ.get("SSHPASS"):
        return ["sshpass", "-e", "rsync", "-a", "-e", "ssh -o StrictHostKeyChecking=accept-new"]
    return ["rsync", "-a"]


def remote_run_wave(wave: str, jobs: int) -> tuple[int, str]:
    """Start wave on .17 in foreground over SSH (long). Returns (rc, run_id)."""
    run_id = make_run_id("run-17")
    remote_cmd = (
        "set -e; cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain; "
        f"export TIMELEARNER_MATRIX_RUN_ID={run_id}; "
        "git -C /home/user/Nmsdk/Bin diff --cached --quiet || git -C /home/user/Nmsdk/Bin reset HEAD; "
        "git -C /home/user/Nmsdk diff --cached --quiet || git -C /home/user/Nmsdk reset HEAD; "
        f"python3 -u scripts/run_timelearner_matrix_queue.py --run-id {run_id} "
        f"--waves {wave} --jobs {jobs} --no-commit; "
        f"echo QUEUE_RC=$?; echo RUN_ID={run_id}; "
        f"test -f _repro/TimeLearnerMatrixRuns/{run_id}/queue_status.json"
    )
    log(f"REMOTE TRAIN {wave} RUN_ID={run_id}")
    cp = run(ssh_base() + [remote_cmd], check=False)
    return cp.returncode, run_id


def ingest_remote_wave(wave: str, run_id: str) -> int:
    host = os.environ.get("TIMELEARNER_MATRIX_SSH", "user@10.245.1.17")
    src = f"{host}:/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/{run_id}/"
    dst = RUNS_BASE / run_id
    dst.mkdir(parents=True, exist_ok=True)
    log(f"RSYNC {run_id} → local")
    run(rsync_base() + [src, str(dst) + "/"], check=True)
    env = os.environ.copy()
    env["TIMELEARNER_MATRIX_RUN_ID"] = run_id
    acquire_lock()
    try:
        run([sys.executable, str(UPDATER), wave], cwd=BASE, env=env)
        # mirror queue git_add_commit
        run(["git", "add", "Configs/SpikeSamples/StructTrain/EXPERIMENTS.md",
             "Configs/SpikeSamples/StructTrain/SUCCESSFUL_EXPERIMENTS.md",
             f"Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/{wave}/results.json"],
            cwd=BIN_ROOT)
        msg = f"research(TimeLearner): record {wave} results (host=17)"
        run(["git", "commit", "-m", msg], cwd=BIN_ROOT, check=False)
        run(["git", "add", "Bin",
             "Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/TIMELEARNER_MATRIX_WAVES_20261010.md",
             "Docs/Audit/TimeLearner-2026-09-26-review/plans/TimeLearner-full-matrix-waves-20261010.ru.md",
             "Docs/Audit/TimeLearner-2026-09-26-review/TIMELEARNER_FULL_MATRIX_AND_HISTORY_2026-10-10.ru.md"],
            cwd=ROOT, check=False)
        run(["git", "commit", "-m", f"research(TimeLearner): pin {wave} report (host=17)"], cwd=ROOT, check=False)
    finally:
        release_lock()
    _push_after_commit()
    # archive on .17 Data + purge remote active run
    arch = (
        f"mkdir -p {ARCHIVE_17} && "
        f"rsync -a /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/{run_id}/ "
        f"{ARCHIVE_17}/{run_id}/ && "
        f"rm -rf /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/{run_id} && "
        "git -C /home/user/Nmsdk/Bin checkout -- Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/*/inputs 2>/dev/null || true; "
        "git -C /home/user/Nmsdk pull --ff-only origin codex/timelearner-audit-followup-20261010 || true; "
        "git -C /home/user/Nmsdk/Bin pull --ff-only origin codex/timelearner-audit-followup-20261010 || true"
    )
    run(ssh_base() + [arch], check=False)
    log(f"INGESTED {wave} {run_id}")
    return 0


def run_remote_role(waves: list[str], jobs: int) -> int:
    """On .17: run wave list with --no-commit only."""
    for wave in waves:
        if wave_done_locally(wave):
            # results may exist after pull from origin
            log(f"SKIP {wave}: results already present")
            continue
        run_id = make_run_id("run-17")
        env = os.environ.copy()
        env["TIMELEARNER_MATRIX_RUN_ID"] = run_id
        cp = run(
            [sys.executable, "-u", str(QUEUE), "--run-id", run_id, "--waves", wave,
             "--jobs", str(jobs), "--no-commit"],
            cwd=BASE,
            check=False,
            env=env,
        )
        (RUNS_BASE / run_id / "CAMPAIGN_WAVE_DONE").write_text(
            f"wave={wave}\nrc={cp.returncode}\n", encoding="utf-8"
        )
        if cp.returncode == 2:
            log(f"INFRA FAIL remote {wave}; stop campaign role")
            return 2
        log(f"REMOTE WAVE DONE {wave} rc={cp.returncode} RUN_ID={run_id} — await local ingest")
        # wait until local removes this run dir after ingest (or marker)
        marker = RUNS_BASE / run_id / "INGESTED"
        for _ in range(3600):  # up to ~30h at 30s
            if not (RUNS_BASE / run_id).exists() or marker.exists():
                break
            time.sleep(30)
        else:
            log(f"TIMEOUT waiting ingest for {run_id}")
            return 3
    log("REMOTE ROLE: all waves finished train")
    return 0


def run_local_role(jobs: int, remote_waves: list[str], local_waves: list[str]) -> int:
    """Interleave: prefer starting remote wave, then local, serializing ingest/commit."""
    ri, li = 0, 0
    remote_active: tuple[str, str] | None = None  # wave, run_id
    state_path = LOG_DIR / "matrix_campaign_state.json"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    def save_state(**kw):
        data = {
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "ri": ri,
            "li": li,
            "remote_active": list(remote_active) if remote_active else None,
            **kw,
        }
        state_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # Skip completed
    while ri < len(remote_waves) and wave_done_locally(remote_waves[ri]):
        log(f"SKIP remote-list {remote_waves[ri]} (already have results)")
        ri += 1
    while li < len(local_waves) and wave_done_locally(local_waves[li]):
        log(f"SKIP local-list {local_waves[li]} (already have results)")
        li += 1

    while ri < len(remote_waves) or li < len(local_waves):
        save_state(phase="loop")
        # Start remote wave if none active
        if remote_active is None and ri < len(remote_waves):
            wave = remote_waves[ri]
            # launch remote in background via nohup on .17
            run_id = make_run_id("run-17")
            remote_cmd = (
                "cd /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain && "
                f"export TIMELEARNER_MATRIX_RUN_ID={run_id} && "
                f"nohup python3 -u scripts/run_timelearner_matrix_queue.py "
                f"--run-id {run_id} --waves {wave} --jobs {jobs} --no-commit "
                f"> _repro/TimeLearnerMatrixRuns/{run_id}.campaign.log 2>&1 & "
                f"echo $! > _repro/TimeLearnerMatrixRuns/{run_id}.pid && "
                f"echo {run_id}"
            )
            run(ssh_base() + [
                f"mkdir -p /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns && {remote_cmd}"
            ])
            remote_active = (wave, run_id)
            log(f"STARTED remote {wave} {run_id}")
            save_state(phase="remote_started")

        # If local has capacity and no commit in progress, run one local wave while remote trains
        if li < len(local_waves) and remote_active is not None:
            wave = local_waves[li]
            rc = run_local_wave(wave, jobs)
            if rc == 2:
                return 2
            li += 1
            save_state(phase="local_done")
        elif li < len(local_waves) and remote_active is None and ri >= len(remote_waves):
            wave = local_waves[li]
            rc = run_local_wave(wave, jobs)
            if rc == 2:
                return 2
            li += 1
            save_state(phase="local_done")

        # Poll remote completion
        if remote_active is not None:
            wave, run_id = remote_active
            exit_remote = (
                f"D=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns; "
                f"if [ -f $D/{run_id}/queue.exit ] || [ -f $D/{run_id}/queue_status.json ]; then "
                f"  if [ -f $D/{run_id}/queue.exit ]; then cat $D/{run_id}/queue.exit; "
                f"  else python3 -c \"import json;print(json.load(open('$D/{run_id}/queue_status.json')).get('status',''))\"; fi; "
                f"else echo RUNNING; fi"
            )
            # wait loop with optional more local waves if previous local finished quickly
            while True:
                out = subprocess.check_output(ssh_base() + [exit_remote], text=True).strip()
                if out != "RUNNING" and "queue_completed" in out or out.isdigit() or out.startswith("paused") or out.startswith("completed") or out.startswith("queue_"):
                    # queue.exit may be numeric
                    log(f"REMOTE FINISHED {wave} signal={out!r}")
                    break
                if out != "RUNNING":
                    # queue.exit content is often just a number
                    try:
                        int(out.splitlines()[-1])
                        log(f"REMOTE FINISHED {wave} exit={out!r}")
                        break
                    except ValueError:
                        pass
                # between polls, if local waves remain, run another
                if li < len(local_waves):
                    rc = run_local_wave(local_waves[li], jobs)
                    if rc == 2:
                        return 2
                    li += 1
                    save_state(phase="local_done_while_remote")
                    continue
                time.sleep(60)

            # check incomplete
            check = (
                f"python3 -c \"import json;from pathlib import Path;"
                f"p=Path('/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/_repro/TimeLearnerMatrixRuns/{run_id}/queue_status.json');"
                f"d=json.loads(p.read_text()) if p.exists() else {{}};"
                f"print(d.get('status',''))\""
            )
            status = subprocess.check_output(ssh_base() + [check], text=True).strip()
            if "incomplete" in status or "infrastructure" in status:
                log(f"INFRA on remote {wave}: {status}")
                return 2
            ingest_remote_wave(wave, run_id)
            remote_active = None
            ri += 1
            save_state(phase="remote_ingested")

    log("LOCAL ROLE: full matrix lists complete")
    save_state(phase="campaign_complete")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", choices=["local", "remote"], required=True)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--waves", nargs="*", help="override wave list for this role")
    args = ap.parse_args()
    if args.jobs < 1 or args.jobs > 8:
        raise SystemExit("--jobs must be 1..8")
    if args.role == "remote":
        waves = args.waves or WAVES_17
        return run_remote_role(waves, args.jobs)
    # local master drives both lists
    remote_waves = WAVES_17 if not args.waves else []
    local_waves = args.waves or WAVES_LOCAL
    if args.waves:
        # explicit waves only on local host
        return run_local_role(args.jobs, remote_waves=[], local_waves=args.waves)
    return run_local_role(args.jobs, remote_waves=WAVES_17, local_waves=WAVES_LOCAL)


if __name__ == "__main__":
    raise SystemExit(main())
