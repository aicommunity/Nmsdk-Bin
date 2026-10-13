"""Shared no-clobber primitives for TimeLearner matrix launches."""
from __future__ import annotations

import hashlib
import csv
import json
import os
import socket
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class CpuLoadSampler:
    """Best-effort instantaneous CPU utilization using OS counters, no dependencies."""

    def __init__(self) -> None:
        self.previous: tuple[int, int] | None = None

    def sample(self) -> float | None:
        if os.name == "nt":
            command = [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter \"Name='_Total'\").PercentProcessorTime",
            ]
            try:
                value = subprocess.check_output(command, text=True, timeout=4).strip()
                return float(value) if value else None
            except (OSError, subprocess.SubprocessError, ValueError):
                return None
        try:
            line = Path("/proc/stat").read_text(encoding="ascii").splitlines()[0]
            fields = [int(value) for value in line.split()[1:]]
            total = sum(fields)
            idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
        except (OSError, IndexError, ValueError):
            return None
        current = (total, idle)
        previous = self.previous
        self.previous = current
        if previous is None:
            time.sleep(0.2)
            return self.sample()
        total_delta = total - previous[0]
        idle_delta = idle - previous[1]
        if total_delta <= 0:
            return None
        return max(0.0, min(100.0, 100.0 * (total_delta - idle_delta) / total_delta))


def logical_cpu_count() -> int:
    return max(1, os.cpu_count() or 1)


def linux_console_pids(proc_root: Path = Path("/proc")) -> set[int]:
    """Return Linux Console PIDs using the untruncated executable/cmdline."""
    found = set()
    try:
        for entry in proc_root.iterdir():
            if entry.name.isdigit():
                try:
                    # Linux TASK_COMM_LEN truncates names to 15 characters, so
                    # /proc/<pid>/comm cannot identify NeuroModelerConsole.
                    comm = (entry / "comm").read_text(encoding="ascii").strip()
                    argv0 = (entry / "cmdline").read_bytes().split(b"\0", 1)[0].decode(
                        "utf-8", errors="replace"
                    )
                    try:
                        executable = os.readlink(entry / "exe")
                    except OSError:
                        executable = ""
                    names = {
                        comm,
                        argv0.replace("\\", "/").rsplit("/", 1)[-1],
                        executable.replace("\\", "/").rsplit("/", 1)[-1],
                    }
                    if names.intersection({"NeuroModelerConsole", "NeuroModelerConsole.exe"}):
                        found.add(int(entry.name))
                except OSError:
                    continue
    except OSError:
        return set()
    return found


def active_console_pids() -> set[int]:
    """Return PIDs for NeuroModelerConsole processes on the current host."""
    if os.name == "nt":
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq NeuroModelerConsole.exe", "/FO", "CSV", "/NH"],
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return set()
        found: set[int] = set()
        for row in csv.reader(output.splitlines()):
            if len(row) >= 2 and row[0].strip('"') == "NeuroModelerConsole.exe":
                try:
                    found.add(int(row[1].strip('"')))
                except ValueError:
                    continue
        return found
    return linux_console_pids()


def active_console_count() -> int:
    return len(active_console_pids())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, value: Any, *, replace: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # link() is an atomic create-if-absent operation on the same volume.
            # It avoids the exists()/replace() race that could clobber another writer.
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def exclusive_file_lock(
    path: Path, *, purpose: str, wait_timeout_s: float = 0.0
) -> Iterator[Path]:
    """Create a host-local lock atomically; never remove another owner's lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "purpose": purpose,
        },
        sort_keys=True,
    ).encode("utf-8")
    deadline = time.monotonic() + max(0.0, wait_timeout_s)
    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            break
        except FileExistsError as exc:
            if time.monotonic() >= deadline:
                try:
                    owner = path.read_text(encoding="utf-8").strip()
                except OSError:
                    owner = "unreadable lock owner"
                raise RuntimeError(f"another matrix launch owns {path}: {owner}") from exc
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        yield path
    finally:
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
            if current.get("pid") == os.getpid() and current.get("host") == socket.gethostname():
                path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            # A lock is safety state. If its ownership cannot be verified, preserve it.
            pass


def reserve_run_root(runs_base: Path, run_id: str) -> Path:
    """Reserve a new run namespace; callers must use resume mode for existing IDs."""
    runs_base.mkdir(parents=True, exist_ok=True)
    run_root = runs_base / run_id
    run_root.mkdir(exist_ok=False)
    return run_root


def verify_run_manifest(manifest: dict[str, Any], expected: dict[str, Any], run_id: str) -> None:
    """Require byte-independent semantic identity before resuming a run."""
    if manifest.get("run_id") != run_id:
        raise RuntimeError(f"run manifest ID mismatch for {run_id}")
    if manifest.get("run_fingerprint") != expected.get("run_fingerprint"):
        raise RuntimeError(
            "resume refused: code, Console, inputs, selected cases, or run options differ "
            f"from the original run {run_id}"
        )


def allocate_case_attempt(case_root: Path) -> tuple[str, Path]:
    """Allocate a fresh, never-reused case attempt directory."""
    case_root.mkdir(parents=True, exist_ok=True)
    attempt = 1
    while True:
        attempt_id = f"attempt-{attempt:04d}"
        attempt_dir = case_root / attempt_id
        try:
            attempt_dir.mkdir(exist_ok=False)
            return attempt_id, attempt_dir
        except FileExistsError:
            attempt += 1
