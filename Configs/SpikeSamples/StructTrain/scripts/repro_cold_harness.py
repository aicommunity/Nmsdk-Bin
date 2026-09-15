#!/usr/bin/env python3
"""Orchestrator: prepare / run / compare identical-cold repro harness."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from repro_cold_lib import (
    FAMILIES,
    REPRO_ROOT,
    ROOT,
    NM,
    Family,
    assert_disk_for_train,
    clone_root,
    free_gib,
    prepare_family,
    post_train_hygiene,
    snapshot_gate,
    verdict_family,
)

PACK = ROOT / "scripts" / "pack_statistic_logs.py"
PHASE9 = ROOT / "SelectivityAsymRm" / "scripts" / "phase9_preinh_bc_gate.py"
PHASE8 = ROOT / "SelectivityBranch" / "scripts" / "phase8_tiprmin_gate.py"
METRICS = ROOT / "scripts" / "selectivity_metrics.py"


def _find_slog(train: Path) -> Path | None:
    slog = train / "StatisticLog"
    if not slog.is_dir():
        return None
    cands = sorted(slog.glob("20*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def run_train(family: Family, root: Path, *, dry_run: bool = False) -> None:
    train = root / "Train"
    ini = train / "Project.ini"
    tlim = family.train_t
    print(f"TRAIN {root.name} -t {tlim} Avail={free_gib():.0f}G")
    if dry_run:
        return
    assert_disk_for_train()
    log = train / "run_repro_cold.log"
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    proc = subprocess.Popen(
        cmd, cwd=str(train), stdout=log.open("w"), stderr=subprocess.STDOUT
    )
    slog_dir = None
    for i in range(1, 200):
        time.sleep(30)
        if proc.poll() is not None:
            print(f"NM exited rc={proc.returncode} poll={i}")
            break
        if slog_dir is None:
            slog_dir = _find_slog(train)
        model_t = 0.0
        L = "?"
        if slog_dir:
            traces = sorted(slog_dir.glob("*DendriteLengthTrace.txt"))
            if traces:
                try:
                    last = traces[0].read_text(encoding="utf-8", errors="replace").strip().splitlines()[
                        -1
                    ]
                    parts = last.split()
                    if len(parts) >= 6:
                        model_t = float(parts[1])
                        L = " ".join(parts[2:6])
                except (OSError, ValueError, IndexError):
                    pass
        if i % 4 == 0:
            print(f"  poll={i} model_t={model_t:.2f} L={L} avail={free_gib():.0f}G")
        if free_gib() < 50:
            print("HARD STOP disk")
            proc.terminate()
            break
        if model_t >= tlim - 2:
            # wait for Parameters DendriteLength != 1 1 1 1
            for j in range(40):
                time.sleep(10)
                from repro_cold_lib import get_tag

                raw = (train / "Parameters_00.xml").read_text(encoding="utf-8")
                Ld = get_tag(raw, "DendriteLength") or ""
                print(f"  save_wait L={Ld}")
                if Ld.replace(",", " ").split() != ["1", "1", "1", "1"]:
                    time.sleep(5)
                    proc.terminate()
                    try:
                        proc.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    print("saved+SIGTERM")
                    return
                if proc.poll() is not None:
                    return
            proc.terminate()
            break
    else:
        proc.terminate()
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()


def pack_root(root: Path, *, dry_run: bool = False) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    arch = ROOT / "archives" / f"statisticlog_repro_{stamp}"
    print(f"PACK {root} -> {arch}")
    if dry_run:
        return arch
    arch.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            sys.executable,
            str(PACK),
            "--root",
            str(root),
            "--arch-dir",
            str(arch),
            "--min-bytes",
            "209715200",
        ]
    )
    return arch


def run_gate(family: Family, root: Path, *, dry_run: bool = False) -> None:
    print(f"GATE {root} metric={family.metric}")
    if dry_run:
        return
    post_train_hygiene(root, family)
    if family.kind == "fastspan":
        cmd = [
            sys.executable,
            str(PHASE9),
            str(root),
            "--test-t",
            "40",
            "--metric",
            family.metric,
        ]
    else:
        cmd = [
            sys.executable,
            str(PHASE8),
            str(root),
            "--span-ms",
            str(family.span_ms),
            "--pack",
            "A",
            "--skip-prepare",
            "--test-t",
            "40",
        ]
    log = root / "Test" / "run_repro_gate.log"
    proc = subprocess.Popen(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    csv_path = root / "Test" / "SelectivityLog" / "results.csv"
    for _ in range(90):
        time.sleep(8)
        if proc.poll() is not None:
            break
        for pid_s in Path("/proc").iterdir():
            if not pid_s.name.isdigit():
                continue
            try:
                cmdl = (pid_s / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            except OSError:
                continue
            if "NeuroModelerConsole" not in cmdl:
                continue
            if str(root / "Test") not in cmdl:
                continue
            if csv_path.exists():
                n = sum(1 for _ in csv_path.open()) - 1
                try:
                    et = int((pid_s / "stat").read_text().split()[21])  # not etimes
                except (OSError, IndexError, ValueError):
                    et = 0
                # use ps
                try:
                    et = int(
                        subprocess.check_output(
                            ["ps", "-o", "etimes=", "-p", pid_s.name], text=True
                        ).strip()
                        or "0"
                    )
                except subprocess.CalledProcessError:
                    et = 0
                if n >= 8 and et > 100:
                    print(f"  SIGTERM NM pid={pid_s.name} n={n} et={et}")
                    subprocess.call(["kill", "-TERM", pid_s.name])
    try:
        proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
    subprocess.call([sys.executable, str(METRICS), "-v", str(csv_path)])


def cmd_prepare(args: argparse.Namespace) -> None:
    families = list(FAMILIES.values()) if args.all else [FAMILIES[args.family]]
    for fam in families:
        prepare_family(fam, force=args.force)


def cmd_run(args: argparse.Namespace) -> None:
    jobs: list[tuple[Family, int]] = []
    if args.all:
        for fam in FAMILIES.values():
            for r in (1, 2):
                jobs.append((fam, r))
    else:
        fam = FAMILIES[args.family]
        reps = (1, 2) if args.rep is None else (args.rep,)
        for r in reps:
            jobs.append((fam, r))
    for fam, rep in jobs:
        root = clone_root(fam, rep)
        if not root.exists():
            prepare_family(fam, reps=(rep,), force=False)
        run_train(fam, root, dry_run=args.dry_run)
        pack_root(root, dry_run=args.dry_run)
        run_gate(fam, root, dry_run=args.dry_run)
        snap = snapshot_gate(root)
        print(f"SNAP r{rep} {fam.key}: {snap}")


def cmd_compare(args: argparse.Namespace) -> None:
    lines = [
        "# REPRO_COLD_RESULT",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "Identical cold Train harness (clean tip-1 Model, TipR cold→@Rmin, mid gate).",
        "",
        "| family | role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse |",
        "|--------|------|---|------|-----|-------|-----|------|----------|------------|",
    ]
    verdicts: list[str] = []
    for key, fam in FAMILIES.items():
        gold = snapshot_gate(fam.gold)
        r1p = clone_root(fam, 1)
        r2p = clone_root(fam, 2)
        r1 = snapshot_gate(r1p) if r1p.exists() else {}
        r2 = snapshot_gate(r2p) if r2p.exists() else {}
        for role, snap in (("gold", gold), ("r1", r1), ("r2", r2)):
            lines.append(
                "| {fam} | {role} | `{L}` | `{TipR}` | {thr} | `{fires}` | {acc} | {mode} | {ok} | {lp} |".format(
                    fam=key,
                    role=role,
                    L=snap.get("L", ""),
                    TipR=snap.get("TipR", "")[:48],
                    thr=snap.get("thr", ""),
                    fires=snap.get("fires", ""),
                    acc=snap.get("acc", ""),
                    mode=snap.get("mode", ""),
                    ok=snap.get("ok_audit", ""),
                    lp=snap.get("last_pulse_ok", ""),
                )
            )
        if r1 and r2:
            v = verdict_family(gold, r1, r2)
            verdicts.append(f"- **{key}**: `{v}`")
        else:
            verdicts.append(f"- **{key}**: incomplete (missing r1/r2)")
    lines.extend(["", "## Verdicts", ""] + verdicts + [""])
    lines.extend(
        [
            "## Criteria",
            "",
            "- `REPRO_OK` — both reps: ok_audit=1, fires==gold, L==gold, last_pulse_ok",
            "- `REPRO_SOFT` — both PASS-like (acc≥7) but L/thr drift",
            "- `REPRO_FAIL` — ok_audit=0 or fires≠gold",
            "- `NONDET` — r1 vs r2 disagree on fires or L",
            "",
        ]
    )
    out = REPRO_ROOT / "REPRO_COLD_RESULT.md"
    REPRO_ROOT.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prepare", help="clone gold + canonical cold")
    p_prep.add_argument("--family", choices=FAMILIES.keys())
    p_prep.add_argument("--all", action="store_true")
    p_prep.add_argument("--force", action="store_true", help="rm existing clones")
    p_prep.add_argument("--dry-run", action="store_true")
    p_prep.set_defaults(func=cmd_prepare)

    p_run = sub.add_parser("run", help="train + pack + gate")
    p_run.add_argument("--family", choices=FAMILIES.keys())
    p_run.add_argument("--rep", type=int, choices=(1, 2))
    p_run.add_argument("--all", action="store_true")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_cmp = sub.add_parser("compare", help="write REPRO_COLD_RESULT.md")
    p_cmp.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    if args.cmd in ("prepare", "run"):
        if not args.all and not getattr(args, "family", None):
            ap.error("need --family or --all")
    args.func(args)


if __name__ == "__main__":
    main()
