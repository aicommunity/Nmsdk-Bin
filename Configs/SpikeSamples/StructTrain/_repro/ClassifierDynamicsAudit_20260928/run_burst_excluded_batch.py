#!/usr/bin/env python3
"""Run at most three Release console replays and monitor LTZone bursts live."""

from __future__ import annotations

import argparse
import csv
import math
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
PROJECT_ROOT = HERE.parent / "BurstReplayVerified_Rerun"
CONSOLE = REPO / "Bin" / "Platform" / "Win" / "NeuroModelerConsole.exe"
POST_SAVE_ACCESS_VIOLATION = 0xC0000005


def period_seconds(project_dir: Path) -> float:
    root = ET.parse(project_dir / "Parameters_00.xml").getroot()
    model = root.find("./Model")
    if model is None:
        raise ValueError(f"Missing model parameters: {project_dir}")
    classifier = next((node for node in model.iter()
                       if node.get("Class") in {"NSpikeClassifier", "NClassifier"}), None)
    if classifier is None:
        raise ValueError(f"No NSpikeClassifier/NClassifier in {project_dir}")
    params = classifier.find("./Parameters")
    if params is None:
        raise ValueError(f"Classifier has no Parameters in {project_dir}")
    frequency = float(params.findtext("SpikesFrequency", "0"))
    time_step_text = params.findtext("TimeStep", "0")
    if float(time_step_text) <= 0:
        project_text = (project_dir / "Project.ini").read_text(encoding="utf-8-sig")
        timestep_match = re.search(r"<GlobalTimeStep>([^<]+)</GlobalTimeStep>", project_text)
        time_step_text = timestep_match.group(1) if timestep_match else "0"
    time_step = float(time_step_text)
    if frequency <= 0 or time_step <= 0:
        raise ValueError(f"Invalid response window settings: frequency={frequency}, timestep={time_step}")
    return 1.0 / frequency - 1.0 / time_step


class TraceMonitor:
    def __init__(self, trace_path: Path, period: float):
        self.path = trace_path
        self.period = period
        self.offset = 0
        self.header: list[str] | None = None
        self.aliases: list[str] = []
        self.previous: dict[str, float] = {}
        self.edges: dict[str, dict[int, int]] = {}
        self.last_reported_window = -1
        self.latest_time = 0.0

    def poll(self) -> list[tuple[int, dict[str, int]]]:
        if not self.path.exists():
            return []
        reports = []
        with self.path.open("r", encoding="utf-8-sig", newline="") as stream:
            stream.seek(self.offset)
            if self.header is None:
                raw = stream.readline()
                if not raw.endswith("\n"):
                    return []
                self.offset = stream.tell()
                self.header = next(csv.reader([raw]))
                self.aliases = [column.partition(" [")[0] for column in self.header]
                # Match the recorder's spike-output aliases only. Names such as
                # `class1_ltz_potential` are analog voltages, not spike trains.
                self.edges = {
                    alias: {}
                    for alias in self.aliases[1:]
                    if alias.lower().endswith("_ltz")
                }
            while True:
                raw = stream.readline()
                if not raw or not raw.endswith("\n"):
                    break
                self.offset = stream.tell()
                fields = next(csv.reader([raw]))
                if len(fields) != len(self.aliases):
                    continue
                values = {alias: float(value) for alias, value in zip(self.aliases, fields)}
                now = values["model_time"]
                self.latest_time = now
                for alias in self.edges:
                    value = values[alias]
                    if self.previous.get(alias, 0.0) < 0.5 <= value:
                        window = max(0, int(math.ceil((now - 1e-10) / self.period)) - 1)
                        self.edges[alias][window] = self.edges[alias].get(window, 0) + 1
                    self.previous[alias] = value
                complete = int(math.floor((now + 1e-9) / self.period)) - 1
                while self.last_reported_window < complete:
                    self.last_reported_window += 1
                    counts = {alias: values_for_window.get(self.last_reported_window, 0)
                              for alias, values_for_window in self.edges.items()}
                    reports.append((self.last_reported_window + 1, counts))
        return reports


def run_batch(projects: list[tuple[Path, float, str]], max_wall_seconds: float) -> list[int | None]:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    active = {}
    results: dict[str, int | None] = {}
    now = time.monotonic()
    for project_dir, seconds, name in projects:
        project_dir = project_dir.resolve()
        if not (project_dir / "Project.ini").is_file():
            raise FileNotFoundError(project_dir / "Project.ini")
        period = period_seconds(project_dir)
        trace_path = project_dir / "signals.csv"
        stdout_file = (project_dir / "console.stdout.txt").open("w", encoding="utf-8")
        stderr_file = (project_dir / "console.stderr.txt").open("w", encoding="utf-8")
        process = subprocess.Popen(
            [str(CONSOLE), "-c", "Project.ini", "-s", "-t", f"{seconds:g}", "-x", "-S"],
            cwd=project_dir,
            stdout=stdout_file,
            stderr=stderr_file,
            creationflags=creationflags,
        )
        active[name] = {
            "process": process,
            "monitor": TraceMonitor(trace_path, period),
            "start": now,
            "last_heartbeat": now,
            "stdout": stdout_file,
            "stderr": stderr_file,
            "project": project_dir,
        }
        print(f"START {project_dir.name}: period={period:.6f}s, target={seconds:g}s, pid={process.pid}", flush=True)

    while active:
        now = time.monotonic()
        for name, item in list(active.items()):
            process = item["process"]
            monitor = item["monitor"]
            for window_number, counts in monitor.poll():
                maximum = max(counts.values(), default=0)
                detail = ",".join(f"{key}={value}" for key, value in counts.items())
                marker = " BURST" if maximum > 1 else ""
                print(f"WINDOW {name} #{window_number}: max_edges={maximum}{marker} {detail}", flush=True)
            elapsed = now - item["start"]
            if now - item["last_heartbeat"] >= 10:
                print(f"LIVE {name}: model_time~{monitor.latest_time:.3f}s, wall={elapsed:.1f}s", flush=True)
                item["last_heartbeat"] = now
            if process.poll() is None and elapsed > max_wall_seconds:
                process.kill()
                process.wait()
                results[name] = None
                print(f"TIMEOUT {name} after {elapsed:.1f}s", flush=True)
            elif process.poll() is not None:
                # Drain complete rows written just before console exit.
                for window_number, counts in monitor.poll():
                    maximum = max(counts.values(), default=0)
                    detail = ",".join(f"{key}={value}" for key, value in counts.items())
                    marker = " BURST" if maximum > 1 else ""
                    print(f"WINDOW {name} #{window_number}: max_edges={maximum}{marker} {detail}", flush=True)
                results[name] = process.returncode
                print(
                    f"DONE {name}: exit={process.returncode}, completed_windows={monitor.last_reported_window + 1}, "
                    f"trace={monitor.path.exists()}",
                    flush=True,
                )
            if name in results:
                item["stdout"].close()
                item["stderr"].close()
                del active[name]
        if active:
            time.sleep(0.5)
    return [results[name] for _, _, name in projects]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("projects", nargs="+", help="Project directory names under the replay root")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT,
                        help="Directory containing the named config clones")
    parser.add_argument("--seconds", type=float, default=None,
                        help="Override model seconds for every project; normally use each Project.ini setting")
    parser.add_argument("--max-wall-seconds", type=float, default=900)
    parser.add_argument("--batch-size", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 3:
        raise ValueError("batch-size must be between 1 and 3 console applications")
    if not CONSOLE.is_file():
        raise FileNotFoundError(CONSOLE)

    # This launcher owns only the listed processes and caps each wave at three.
    overall = 0
    all_results: dict[str, int | None] = {}
    for index in range(0, len(args.projects), args.batch_size):
        batch = args.projects[index:index + args.batch_size]
        print(f"BATCH {index // args.batch_size + 1}: {', '.join(batch)}", flush=True)
        batch_projects = []
        for name in batch:
            project = args.project_root / name
            project_text = (project / "Project.ini").read_text(encoding="utf-8-sig")
            match = re.search(r"<MaxCalculationModelTime>([^<]+)</MaxCalculationModelTime>", project_text)
            if match is None:
                raise ValueError(f"MaxCalculationModelTime is missing in {project / 'Project.ini'}")
            configured = float(match.group(1))
            seconds = args.seconds or configured
            batch_projects.append((project, seconds, name))
        codes = run_batch(batch_projects, args.max_wall_seconds)
        for (_, _, name), return_code in zip(batch_projects, codes):
            all_results[name] = return_code
            if return_code is None:
                overall = 2
            elif return_code not in (0, 1, -1073741819, POST_SAVE_ACCESS_VIOLATION):
                overall = 1
    print("RESULTS " + ", ".join(f"{name}={code}" for name, code in all_results.items()), flush=True)
    return overall


if __name__ == "__main__":
    sys.exit(main())
