#!/usr/bin/env python3
"""Orchestrator: prepare / run / compare / invest identical-cold repro harness."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from repro_cold_lib import (
    FAMILIES,
    INVEST_JOBS,
    INVEST_ROOT,
    REPRO_ROOT,
    ROOT,
    NM,
    ColdMode,
    Family,
    append_compare_row,
    assert_disk_for_train,
    clone_root,
    free_gib,
    get_tag,
    invest_root,
    prepare_family,
    prepare_invest,
    post_train_hygiene,
    enable_post_train_tuning_on,
    tipr_looks_posttuned,
    get_tag,
    read_need,
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


def _terminate(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)


def run_train(family: Family, root: Path, *, dry_run: bool = False) -> str:
    """Train until IsNeedToTrain=0 (or timeout). Returns status: done|incomplete_done|exited|disk."""
    train = root / "Train"
    ini = train / "Project.ini"
    tlim = family.train_t
    print(f"TRAIN {root.name} -t {tlim} Avail={free_gib():.0f}G")
    if dry_run:
        return "dry"
    assert_disk_for_train()
    log = train / "run_repro_cold.log"
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    proc = subprocess.Popen(
        cmd, cwd=str(train), stdout=log.open("w"), stderr=subprocess.STDOUT
    )
    slog_dir = None
    need0_seen = False
    # ~200 * 30s ≈ 100 min wall; Branch -t 320 may need longer — extend loop
    max_polls = 400
    for i in range(1, max_polls + 1):
        time.sleep(30)
        if proc.poll() is not None:
            need = read_need(train / "Parameters_00.xml")
            if need != "0":
                for j in range(18):
                    time.sleep(10)
                    need = read_need(train / "Parameters_00.xml")
                    if need == "0":
                        print(f"Need=0 after NM exit (delayed save) poll={i} wait={j}")
                        return "done"
            print(f"NM exited rc={proc.returncode} poll={i} Need={need}")
            return "done" if need == "0" else "exited_need1"
        if slog_dir is None:
            slog_dir = _find_slog(train)
        model_t = 0.0
        L = "?"
        if slog_dir:
            traces = sorted(slog_dir.glob("*DendriteLengthTrace.txt"))
            if traces:
                try:
                    last = (
                        traces[0]
                        .read_text(encoding="utf-8", errors="replace")
                        .strip()
                        .splitlines()[-1]
                    )
                    parts = last.split()
                    if len(parts) >= 6:
                        model_t = float(parts[1])
                        L = " ".join(parts[2:6])
                except (OSError, ValueError, IndexError):
                    pass
        raw = (train / "Parameters_00.xml").read_text(encoding="utf-8")
        need = get_tag(raw, "IsNeedToTrain") or "?"
        Ld = get_tag(raw, "DendriteLength") or L
        if i % 4 == 0:
            print(
                f"  poll={i} model_t={model_t:.2f} L={Ld} Need={need} avail={free_gib():.0f}G"
            )
        if free_gib() < 50:
            print("HARD STOP disk")
            _terminate(proc)
            return "disk"
        if need == "0":
            need0_seen = True
            # allow a short settle then SIGTERM (Qt hang after -S)
            time.sleep(8)
            print("Need=0 saved+SIGTERM")
            _terminate(proc)
            return "done"
        # past -t wall: wait for Need=0 with extended save polls (do NOT stop on L alone)
        if model_t >= tlim - 2:
            print(f"  past -t ({model_t:.2f}>={tlim}); waiting Need=0 …")
            for j in range(60):
                time.sleep(10)
                if proc.poll() is not None:
                    need = read_need(train / "Parameters_00.xml")
                    return "done" if need == "0" else "exited_need1"
                need = read_need(train / "Parameters_00.xml")
                Ld = get_tag(
                    (train / "Parameters_00.xml").read_text(encoding="utf-8"),
                    "DendriteLength",
                )
                if j % 3 == 0:
                    print(f"  save_wait Need={need} L={Ld}")
                if need == "0":
                    time.sleep(5)
                    print("Need=0 after -t +SIGTERM")
                    _terminate(proc)
                    return "done"
            print("WARN incomplete_done: Need still 1 after wait past -t")
            _terminate(proc)
            return "incomplete_done"
    print("WARN poll budget exhausted")
    _terminate(proc)
    return "incomplete_done" if not need0_seen else "done"


def pack_root(root: Path, *, dry_run: bool = False, prefix: str = "repro") -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    arch = ROOT / "archives" / f"statisticlog_{prefix}_{stamp}"
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


def run_gate(
    family: Family,
    root: Path,
    *,
    dry_run: bool = False,
    force_python_hygiene: bool = False,
) -> None:
    print(f"GATE {root} metric={family.metric}")
    if dry_run:
        return
    train_p = root / "Train" / "Parameters_00.xml"
    tp = train_p.read_text(encoding="utf-8") if train_p.exists() else ""
    tipr = get_tag(tp, "TipSynapseResistance")
    skip_tipr_mid = (
        not force_python_hygiene
        and enable_post_train_tuning_on(tp)
        and tipr_looks_posttuned(tipr)
    )
    post_train_hygiene(root, family, force_python_hygiene=force_python_hygiene)
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
        # Full prepare_test (includes patch_tip_exc_r) — no --skip-prepare
        cmd = [
            sys.executable,
            str(PHASE8),
            str(root),
            "--span-ms",
            str(family.span_ms),
            "--pack",
            "A",
            "--test-t",
            "40",
        ]
        if skip_tipr_mid:
            cmd.append("--skip-tipr-mid")
    log = root / "Test" / "run_repro_gate.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    csv_path = root / "Test" / "SelectivityLog" / "results.csv"
    for _ in range(120):
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
        proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
    if csv_path.exists():
        subprocess.call([sys.executable, str(METRICS), "-v", str(csv_path)])


def cmd_prepare(args: argparse.Namespace) -> None:
    mode: ColdMode = args.cold
    families = list(FAMILIES.values()) if args.all else [FAMILIES[args.family]]
    for fam in families:
        prepare_family(fam, force=args.force, mode=mode)


def cmd_run(args: argparse.Namespace) -> None:
    mode: ColdMode = args.cold
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
        root = Path(args.root) if args.root else clone_root(fam, rep)
        if not root.exists():
            if args.root:
                raise SystemExit(f"missing --root {root}")
            prepare_family(fam, reps=(rep,), force=False, mode=mode)
        status = run_train(fam, root, dry_run=args.dry_run)
        print(f"TRAIN_STATUS={status}")
        pack_root(root, dry_run=args.dry_run, prefix="repro")
        run_gate(
            fam,
            root,
            dry_run=args.dry_run,
            force_python_hygiene=getattr(args, "force_python_hygiene", False),
        )
        snap = snapshot_gate(root)
        print(f"SNAP r{rep} {fam.key} cold={mode}: {snap}")


def cmd_invest(args: argparse.Namespace) -> None:
    if getattr(args, "all", False):
        job_ids = ["A1", "A2", "B1", "B2"]
    else:
        job_ids = [args.job]
    for job_id in job_ids:
        fam_key, mode, _ = INVEST_JOBS[job_id]
        fam = FAMILIES[fam_key]
        root = invest_root(job_id)
        if args.prepare_only or not root.exists() or args.force:
            prepare_invest(job_id, force=bool(args.force or root.exists()))
        if args.prepare_only:
            continue
        status = run_train(fam, root, dry_run=args.dry_run)
        print(f"TRAIN_STATUS={status} job={job_id}")
        pack_root(root, dry_run=args.dry_run, prefix="invest")
        run_gate(
            fam,
            root,
            dry_run=args.dry_run,
            force_python_hygiene=getattr(args, "force_python_hygiene", False),
        )
        append_compare_row(job_id, fam, mode, root)
        snap = snapshot_gate(root)
        print(f"INVEST SNAP {job_id}: {snap}")
        print(f"COMPARE -> {INVEST_ROOT / 'COMPARE.md'}")


def cmd_compare(args: argparse.Namespace) -> None:
    lines = [
        "# REPRO_COLD_RESULT",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "Cold Train harness (soft-cold default; TipR cold→@Rmin; Need=0; mid gate).",
        "",
        "| family | role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse | Need |",
        "|--------|------|---|------|-----|-------|-----|------|----------|------------|------|",
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
                "| {fam} | {role} | `{L}` | `{TipR}` | {thr} | `{fires}` | {acc} | {mode} | {ok} | {lp} | {need} |".format(
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
                    need=snap.get("Need", ""),
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
            "- `REPRO_OK_QUALITY` — r1≡r2, ok_audit=1, acc≥8 (fires/L vs gold optional)",
            "- `REPRO_OK_EXACT` — QUALITY + fires==gold + L==gold",
            "- `REPRO_OK` / `REPRO_SOFT` — legacy exact/soft fires match",
            "- `REPRO_FAIL` — ok_audit=0 or (legacy) fires≠gold without QUALITY",
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

    p_prep = sub.add_parser("prepare", help="clone gold + cold reset")
    p_prep.add_argument("--family", choices=FAMILIES.keys())
    p_prep.add_argument("--all", action="store_true")
    p_prep.add_argument("--force", action="store_true")
    p_prep.add_argument("--cold", choices=("soft", "strip"), default="soft")
    p_prep.add_argument("--dry-run", action="store_true")
    p_prep.set_defaults(func=cmd_prepare)

    p_run = sub.add_parser("run", help="train + pack + gate")
    p_run.add_argument("--family", choices=FAMILIES.keys())
    p_run.add_argument("--rep", type=int, choices=(1, 2))
    p_run.add_argument("--all", action="store_true")
    p_run.add_argument("--cold", choices=("soft", "strip"), default="soft")
    p_run.add_argument("--root", type=str, help="explicit experiment root")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument(
        "--force-python-hygiene",
        action="store_true",
        help="Always apply Python tiprmin/mid even when C++ PostTune TipR is present",
    )
    p_run.set_defaults(func=cmd_run)

    p_inv = sub.add_parser("invest", help="A/B soft vs strip under _repro/_invest")
    p_inv.add_argument("--job", choices=list(INVEST_JOBS.keys()))
    p_inv.add_argument("--all", action="store_true", help="A1 A2 B1 B2")
    p_inv.add_argument("--force", action="store_true")
    p_inv.add_argument("--prepare-only", action="store_true")
    p_inv.add_argument("--dry-run", action="store_true")
    p_inv.add_argument(
        "--force-python-hygiene",
        action="store_true",
        help="Always apply Python tiprmin/mid even when C++ PostTune TipR is present",
    )
    p_inv.set_defaults(func=cmd_invest)

    p_cmp = sub.add_parser("compare", help="write REPRO_COLD_RESULT.md")
    p_cmp.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    if args.cmd == "prepare" and not args.all and not args.family:
        ap.error("need --family or --all")
    if args.cmd == "run" and not args.all and not args.family and not args.root:
        ap.error("need --family/--all or --root")
    if args.cmd == "invest" and not args.all and not args.job:
        ap.error("need --job or --all")
    args.func(args)


if __name__ == "__main__":
    main()
