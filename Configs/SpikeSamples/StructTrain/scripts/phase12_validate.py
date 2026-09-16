#!/usr/bin/env python3
"""PHASE12 Wave1 orchestrator: soft-cold ×2 Branch packA roots + stamp/promote."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from repro_cold_lib import (
    NM,
    REPRO_ROOT,
    ROOT,
    TIPR_COLD,
    TIPR_RMIN,
    L_COLD,
    Family,
    apply_tiprmin,
    assert_disk_for_train,
    assert_train_cold_flags,
    cold_reset_train,
    free_gib,
    get_tag,
    patch_tip_exc_r,
    read_lengths,
    read_need,
    rsync_clone,
    snapshot_gate,
    tip_indices,
    verdict_family,
)

PACK = ROOT / "scripts" / "pack_statistic_logs.py"
PHASE8 = ROOT / "SelectivityBranch" / "scripts" / "phase8_tiprmin_gate.py"
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
MANIFEST = ROOT / "PHASE12_VALIDATION.md"
BRANCH = ROOT / "SelectivityBranch"

TipRRecipe = Literal["tiprmin", "done_tipr"]


@dataclass(frozen=True)
class ExpSpec:
    exp_id: str
    gold: Path
    clone_name: str
    span_ms: int
    train_t: float
    neuron: str
    next_seg: bool
    tipr_recipe: TipRRecipe
    metric: str = "soma_amp_sum"
    kind: str = "branch"
    gold_L: str = ""
    gold_thr: str = ""


def _spec(
    exp_id: str,
    span_ms: int,
    neuron: str,
    next_seg: bool,
    tipr_recipe: TipRRecipe,
    gold_L: str,
    gold_thr: str,
    train_t: float = 320.0,
) -> ExpSpec:
    return ExpSpec(
        exp_id=exp_id,
        gold=BRANCH / exp_id,
        clone_name=exp_id.replace("EXP_br_", "Branch_"),
        span_ms=span_ms,
        train_t=train_t,
        neuron=neuron,
        next_seg=next_seg,
        tipr_recipe=tipr_recipe,
        gold_L=gold_L,
        gold_thr=gold_thr,
    )


GEN = "NSPNeuronGenAsymRmD001C1e9"
PRE = "NSPNeuronGenPreinh2_5AsymRmD001C1e9"

WAVE1_EXPS: dict[str, ExpSpec] = {
    s.exp_id: s
    for s in (
        _spec("EXP_br_span25_packA_gen_C1e9", 25, GEN, False, "tiprmin", "13 11 7 1", "0.07179975"),
        _spec("EXP_br_span50_packA_gen_C1e9", 50, GEN, False, "tiprmin", "13 11 6 1", "0.06440315"),
        _spec(
            "EXP_br_span100_packA_gen_C1e9",
            100,
            GEN,
            False,
            "done_tipr",
            "25 21 11 1",
            "0.007181835",
        ),
        _spec(
            "EXP_br_span25_packA_preinh_C1e9",
            25,
            PRE,
            False,
            "tiprmin",
            "7 6 4 1",
            "0.05171075",
        ),
        _spec(
            "EXP_br_span50_packA_preinh_C1e9",
            50,
            PRE,
            False,
            "tiprmin",
            "13 11 6 1",
            "0.03008405",
        ),
        _spec(
            "EXP_br_span100_packA_preinh_C1e9",
            100,
            PRE,
            False,
            "tiprmin",
            "22 18 11 1",
            "0.0203054",
        ),
        _spec(
            "EXP_br_span25_packA_nextseginh_C1e9",
            25,
            GEN,
            True,
            "tiprmin",
            "13 11 7 1",
            "0.07179975",
        ),
        _spec(
            "EXP_br_span50_packA_nextseginh_C1e9",
            50,
            GEN,
            True,
            "tiprmin",
            "14 9 6 1",
            "0.0456422",
        ),
        _spec(
            "EXP_br_span100_packA_nextseginh_C1e9",
            100,
            GEN,
            True,
            "tiprmin",
            "21 17 11 1",
            "0.014432775",
        ),
    )
}

WAVE1_ORDER = list(WAVE1_EXPS.keys())


def clone_root(spec: ExpSpec, rep: int) -> Path:
    return REPRO_ROOT / spec.clone_name / f"r{rep}"


def as_family(spec: ExpSpec) -> Family:
    return Family(
        key=spec.exp_id,
        gold=spec.gold,
        clone_name=spec.clone_name,
        train_t=spec.train_t,
        metric=spec.metric,
        kind=spec.kind,
        span_ms=spec.span_ms,
    )


def _terminate(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)


def _find_slog(train: Path) -> Path | None:
    slog = train / "StatisticLog"
    if not slog.is_dir():
        return None
    cands = sorted(slog.glob("20*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def assert_next_seg(train: Path, want: bool) -> None:
    t = (train / "Parameters_00.xml").read_text(encoding="utf-8")
    got = get_tag(t, "EnableNextSegmentInhibition")
    if want and got != "1":
        raise SystemExit(f"NextSeg expected 1, got {got} in {train}")
    if not want and got not in (None, "0", "?"):
        # missing tag is OK for gen/preinh
        if got == "1":
            raise SystemExit(f"NextSeg unexpectedly 1 in {train}")


def assert_neuron(train: Path, neuron: str) -> None:
    t = (train / "Parameters_00.xml").read_text(encoding="utf-8")
    got = get_tag(t, "NeuronClassName")
    if got != neuron:
        raise SystemExit(f"NeuronClassName={got} want {neuron}")


def assert_reset_injected(train: Path) -> None:
    t = (train / "Parameters_00.xml").read_text(encoding="utf-8")
    if get_tag(t, "ResetToUntrainedState") != "1":
        raise SystemExit(f"ResetToUntrainedState missing/!=1 in {train}")


def prepare_exp(spec: ExpSpec, reps: tuple[int, ...] = (1, 2), *, force: bool = False) -> list[Path]:
    REPRO_ROOT.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for rep in reps:
        dst = clone_root(spec, rep)
        if dst.exists():
            if force:
                shutil.rmtree(dst)
            else:
                print(f"skip existing {dst}")
                out.append(dst)
                continue
        pname = f"{spec.clone_name}_r{rep}_soft"
        print(f"clone {spec.gold.name} -> {dst}")
        rsync_clone(spec.gold, dst, pname)
        cold_reset_train(dst / "Train", mode="soft")
        # cold Test params (Need=0, L/TipR cold markers)
        tp = dst / "Test" / "Parameters_00.xml"
        if tp.exists():
            from repro_cold_lib import set_tag

            t = tp.read_text(encoding="utf-8")
            t = set_tag(t, "IsNeedToTrain", "0", 1)
            t = set_tag(t, "DendriteLength", L_COLD, 1)
            t = set_tag(t, "TipSynapseResistance", TIPR_COLD, 1)
            tp.write_text(t, encoding="utf-8")
        assert_train_cold_flags(dst / "Train" / "Parameters_00.xml", mode="soft")
        assert_reset_injected(dst / "Train")
        assert_neuron(dst / "Train", spec.neuron)
        assert_next_seg(dst / "Train", spec.next_seg)
        tips = tip_indices((dst / "Train" / "Model_00.xml").read_text(encoding="utf-8"))
        print(f"  soft ok tips_max={max(tips) if tips else 0} NextSeg={int(spec.next_seg)}")
        out.append(dst)
    return out


def run_train(spec: ExpSpec, root: Path, *, dry_run: bool = False) -> str:
    """Train until Need=0. If NM exits at -t with Need=1, extend up to 2 extra -t windows."""
    status = "incomplete_done"
    extensions = 0
    while extensions < 3:
        status = _run_train_once(spec, root, dry_run=dry_run)
        if status == "done" or dry_run:
            return status
        if status in ("disk",):
            return status
        # exited_need1 / incomplete_done → extend wall
        need = read_need(root / "Train" / "Parameters_00.xml")
        if need == "0":
            return "done"
        extensions += 1
        print(f"TRAIN extend#{extensions} after status={status} Need={need}")
    return status


def _run_train_once(spec: ExpSpec, root: Path, *, dry_run: bool = False) -> str:
    train = root / "Train"
    ini = train / "Project.ini"
    tlim = spec.train_t
    print(f"TRAIN {root.name} -t {tlim} Avail={free_gib():.0f}G")
    if dry_run:
        return "dry"
    assert_disk_for_train()
    log = train / "run_phase12_cold.log"
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    proc = subprocess.Popen(cmd, cwd=str(train), stdout=log.open("a"), stderr=subprocess.STDOUT)
    slog_dir = None
    need0_seen = False
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
                        print(f"Need=0 after NM exit poll={i} wait={j}")
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
            print(f"  poll={i} model_t={model_t:.2f} L={Ld} Need={need} avail={free_gib():.0f}G")
        if free_gib() < 50:
            print("HARD STOP disk")
            _terminate(proc)
            return "disk"
        if need == "0":
            need0_seen = True
            time.sleep(8)
            print("Need=0 saved+SIGTERM")
            _terminate(proc)
            return "done"
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


def pack_root(root: Path, *, dry_run: bool = False) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    arch = ROOT / "archives" / f"statisticlog_phase12_{stamp}"
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


def post_hygiene(spec: ExpSpec, root: Path) -> None:
    """TipR@Rmin + tip Exc on Train; done_tipr skips TipR force."""
    train = root / "Train"
    tips = read_lengths(train / "Parameters_00.xml")
    if spec.tipr_recipe == "tiprmin":
        apply_tiprmin([train / "Parameters_00.xml", train / "Model_00.xml"])
        mp = train / "Model_00.xml"
        mt = patch_tip_exc_r(
            mp.read_text(encoding="utf-8").replace(",", "."), tips, branch=True
        )
        mp.write_text(mt, encoding="utf-8")
    else:
        print("  done_tipr: skip TipR@Rmin force on Train")


def run_gate(spec: ExpSpec, root: Path, *, dry_run: bool = False) -> None:
    print(f"GATE {root} recipe={spec.tipr_recipe}")
    if dry_run:
        return
    post_hygiene(spec, root)
    cmd = [
        sys.executable,
        str(PHASE8),
        str(root),
        "--span-ms",
        str(spec.span_ms),
        "--pack",
        "A",
        "--test-t",
        "40",
    ]
    if spec.tipr_recipe == "done_tipr":
        # Keep Train Done TipR through prepare (do not force TipR@Rmin)
        cmd.append("--keep-tipr")
        cmd.append("--allow-done-tipr-fallback")
    log = root / "Test" / "run_phase12_gate.log"
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


def verdict_phase12(gold: dict[str, str], r1: dict[str, str], r2: dict[str, str]) -> str:
    """Wave1: EXACT preferred; QUALITY if r1≡r2 + ok_audit + last_pulse + Need=0 + acc≥7."""
    base = verdict_family(gold, r1, r2)
    if base in ("REPRO_OK_EXACT", "REPRO_OK_QUALITY", "REPRO_OK", "REPRO_SOFT"):
        return base
    if not r1 or not r2:
        return "incomplete"

    def L(d: dict[str, str]) -> str:
        return " ".join(d.get("L", "").split())

    if r1.get("fires") != r2.get("fires") or L(r1) != L(r2):
        return "NONDET"
    for snap in (r1, r2):
        if snap.get("Need") != "0":
            return "REPRO_FAIL"
        if snap.get("ok_audit") != "1":
            return "REPRO_FAIL"
        if snap.get("last_pulse_ok") != "1":
            return "REPRO_FAIL"
        try:
            if int(snap.get("acc") or 0) < 7:
                return "REPRO_FAIL"
        except ValueError:
            return "REPRO_FAIL"
    if L(r1) == L(gold) and r1.get("fires") == gold.get("fires"):
        return "REPRO_OK_EXACT"
    return "REPRO_OK_QUALITY"


def write_compare(spec: ExpSpec) -> str:
    gold = snapshot_gate(spec.gold)
    r1p, r2p = clone_root(spec, 1), clone_root(spec, 2)
    r1 = snapshot_gate(r1p) if r1p.exists() else {}
    r2 = snapshot_gate(r2p) if r2p.exists() else {}
    lines = [
        f"# PHASE12 compare {spec.exp_id}",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "| role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse | Need |",
        "|------|---|------|-----|-------|-----|------|----------|------------|------|",
    ]
    for role, snap in (("gold", gold), ("r1", r1), ("r2", r2)):
        lines.append(
            "| {role} | `{L}` | `{TipR}` | {thr} | `{fires}` | {acc} | {mode} | {ok} | {lp} | {need} |".format(
                role=role,
                L=snap.get("L", ""),
                TipR=(snap.get("TipR", "") or "")[:48],
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
        v = verdict_phase12(gold, r1, r2)
    else:
        v = "incomplete"
    lines += ["", f"**verdict:** `{v}`", ""]
    out = REPRO_ROOT / spec.clone_name / "COMPARE.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"COMPARE -> {out} verdict={v}")
    return v


def _update_manifest_status(exp_id: str, status: str, notes: str = "", commit: str = "") -> None:
    if not MANIFEST.exists():
        print(f"WARN no manifest {MANIFEST}")
        return
    text = MANIFEST.read_text(encoding="utf-8")
    # Match table row starting with | exp_id |
    pat = re.compile(
        rf"^(\| {re.escape(exp_id)} \|[^\n]*\| )(DEFERRED|VALIDATED|VALIDATED_CLONE|FAIL|BLOCKED_FS|ARTIFACT|OUT)( \|)",
        re.M,
    )
    new_text, n = pat.subn(rf"\g<1>{status}\3", text, count=1)
    if n != 1:
        print(f"WARN manifest status replace n={n} for {exp_id}")
    # append run log row
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    log_line = f"| {utc} | {exp_id} | {status} | | | | {notes} |\n"
    if "## Wave 1 run log" in new_text:
        # insert after header separator of run log table
        marker = "|-----|--------|---------|---|-----|-------|-------|\n"
        if marker in new_text:
            # replace empty placeholder row if present
            new_text = new_text.replace("| | | | | | | |\n", log_line, 1)
            if log_line not in new_text:
                new_text = new_text.replace(marker, marker + log_line, 1)
        if commit and f"| {exp_id} |" in new_text:
            # try set last_commit column (last before newline) — best-effort leave notes
            pass
    MANIFEST.write_text(new_text, encoding="utf-8")
    print(f"manifest {exp_id} -> {status}")


def promote_pass(spec: ExpSpec, *, dry_run: bool = False) -> None:
    gold = snapshot_gate(spec.gold)
    r1 = snapshot_gate(clone_root(spec, 1))
    r2 = snapshot_gate(clone_root(spec, 2))
    v = verdict_phase12(gold, r1, r2)
    if v not in ("REPRO_OK_EXACT", "REPRO_OK_QUALITY", "REPRO_OK", "REPRO_SOFT"):
        raise SystemExit(f"refuse promote verdict={v}")
    for snap in (r1, r2):
        if snap.get("Need") != "0":
            raise SystemExit(f"Need!={snap.get('Need')}")
        if snap.get("ok_audit") != "1":
            raise SystemExit("ok_audit!=1")
        if snap.get("last_pulse_ok") != "1":
            raise SystemExit("last_pulse!=1")
        if int(snap.get("acc") or 0) < 7:
            raise SystemExit(f"acc={snap.get('acc')} < 7")
    if " ".join(r1.get("L", "").split()) != " ".join(r2.get("L", "").split()):
        raise SystemExit("r1 L != r2 L")
    if r1.get("fires") != r2.get("fires"):
        raise SystemExit("r1 fires != r2 fires")
    src = clone_root(spec, 2)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = spec.gold.parent / f"{spec.exp_id}.bak_phase12_{stamp}"
    print(f"PROMOTE {src} -> {spec.gold} bak={bak}")
    if dry_run:
        return
    if bak.exists():
        raise SystemExit(f"bak exists {bak}")
    shutil.copytree(
        spec.gold,
        bak,
        ignore=shutil.ignore_patterns(
            "StatisticLog", "EventsLog", "SelectivityLog", "*.log", "History.xml"
        ),
    )
    for side in ("Train", "Test"):
        for name in (
            "Parameters_00.xml",
            "Model_00.xml",
            "Project.ini",
            "Interface.xml",
        ):
            s = src / side / name
            d = spec.gold / side / name
            if s.exists():
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)
    csv_s = src / "Test" / "SelectivityLog" / "results.csv"
    if csv_s.exists():
        dst_csv = spec.gold / "Test" / "SelectivityLog" / "results.csv"
        dst_csv.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(csv_s, dst_csv)
    notes = f"verdict={v} L=`{r2.get('L')}` thr={r2.get('thr')} fires=`{r2.get('fires')}`"
    _update_manifest_status(spec.exp_id, "VALIDATED", notes=notes)
    print(f"PROMOTE done {notes}")


def stamp_from_repro(spec: ExpSpec) -> str:
    """Mark VALIDATED if existing _repro r1/r2 match gold exactly (no retrain)."""
    r1p, r2p = clone_root(spec, 1), clone_root(spec, 2)
    if not r1p.exists() or not r2p.exists():
        raise SystemExit(f"missing repro clones under {REPRO_ROOT / spec.clone_name}")
    gold = snapshot_gate(spec.gold)
    r1 = snapshot_gate(r1p)
    r2 = snapshot_gate(r2p)
    v = verdict_family(gold, r1, r2)
    print(f"stamp-from-repro {spec.exp_id}: {v}")
    write_compare(spec)
    if v != "REPRO_OK_EXACT":
        raise SystemExit(f"refuse stamp: need REPRO_OK_EXACT got {v}")
    for snap in (r1, r2):
        if snap.get("Need") != "0" or snap.get("ok_audit") != "1":
            raise SystemExit("Need/ok_audit fail")
        if snap.get("last_pulse_ok") != "1":
            raise SystemExit("last_pulse fail")
    notes = f"stamp-from-repro {v} L=`{r1.get('L')}` thr={r1.get('thr')}"
    _update_manifest_status(spec.exp_id, "VALIDATED", notes=notes)
    return v


def cmd_list(args: argparse.Namespace) -> None:
    wave = args.wave
    for eid in WAVE1_ORDER:
        s = WAVE1_EXPS[eid]
        if wave is not None and wave != 1:
            continue
        print(
            f"{eid}\tspan={s.span_ms}\trecipe={s.tipr_recipe}\tNextSeg={int(s.next_seg)}\t"
            f"L={s.gold_L}\tthr={s.gold_thr}\tclone={s.clone_name}"
        )


def cmd_prepare(args: argparse.Namespace) -> None:
    spec = WAVE1_EXPS[args.exp]
    reps = (1, 2) if args.replicas is None else tuple(range(1, args.replicas + 1))
    prepare_exp(spec, reps=reps, force=args.force)


def cmd_run(args: argparse.Namespace) -> None:
    spec = WAVE1_EXPS[args.exp]
    reps = tuple(range(1, args.replicas + 1))
    for rep in reps:
        root = clone_root(spec, rep)
        if not root.exists() or args.force_prepare:
            prepare_exp(spec, reps=(rep,), force=bool(args.force_prepare or not root.exists()))
        status = run_train(spec, root, dry_run=args.dry_run)
        print(f"TRAIN_STATUS={status} r{rep}")
        if status not in ("done", "dry"):
            _update_manifest_status(spec.exp_id, "FAIL", notes=f"train {status} r{rep}")
            raise SystemExit(f"train failed: {status}")
        pack_root(root, dry_run=args.dry_run)
        run_gate(spec, root, dry_run=args.dry_run)
        snap = snapshot_gate(root)
        print(f"SNAP r{rep}: {snap}")
    v = write_compare(spec)
    if v in ("REPRO_OK_EXACT", "REPRO_OK_QUALITY", "REPRO_OK", "REPRO_SOFT"):
        print(f"PASS candidate verdict={v} — run promote to write gold")
    else:
        _update_manifest_status(spec.exp_id, "FAIL", notes=f"verdict={v}")
        raise SystemExit(f"compare FAIL {v}")


def cmd_compare(args: argparse.Namespace) -> None:
    write_compare(WAVE1_EXPS[args.exp])


def cmd_promote(args: argparse.Namespace) -> None:
    promote_pass(WAVE1_EXPS[args.exp], dry_run=args.dry_run)


def cmd_stamp(args: argparse.Namespace) -> None:
    stamp_from_repro(WAVE1_EXPS[args.exp])


def cmd_run_all(args: argparse.Namespace) -> None:
    """Wave1 order: stamp span25 gen if possible, else run; then remaining."""
    order = WAVE1_ORDER if not args.exp else [args.exp]
    for eid in order:
        spec = WAVE1_EXPS[eid]
        print(f"\n===== {eid} =====")
        if eid == "EXP_br_span25_packA_gen_C1e9" and not args.force_train:
            try:
                stamp_from_repro(spec)
                print("stamped VALIDATED — skip train")
                continue
            except SystemExit as e:
                print(f"stamp skipped: {e}")
        ns = argparse.Namespace(
            exp=eid,
            replicas=args.replicas,
            dry_run=args.dry_run,
            force_prepare=args.force_prepare,
        )
        cmd_run(ns)
        if not args.dry_run and not args.no_promote:
            promote_pass(spec, dry_run=False)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list")
    p.add_argument("--wave", type=int, default=1)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("prepare")
    p.add_argument("--exp", required=True, choices=WAVE1_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("run")
    p.add_argument("--exp", required=True, choices=WAVE1_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("compare")
    p.add_argument("--exp", required=True, choices=WAVE1_ORDER)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("promote")
    p.add_argument("--exp", required=True, choices=WAVE1_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_promote)

    p = sub.add_parser("stamp-from-repro")
    p.add_argument("--exp", required=True, choices=WAVE1_ORDER)
    p.set_defaults(func=cmd_stamp)

    p = sub.add_parser("run-all-wave1")
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--force-train", action="store_true", help="skip stamp-from-repro")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--exp", choices=WAVE1_ORDER, help="single exp only")
    p.set_defaults(func=cmd_run_all)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
