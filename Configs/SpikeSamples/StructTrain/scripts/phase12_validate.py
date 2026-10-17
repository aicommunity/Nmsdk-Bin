#!/usr/bin/env python3
"""PHASE12 Wave1–4 orchestrator: Branch + FastSpan/AsymRm/LtzCal/Phase6."""
from __future__ import annotations

import argparse
import csv
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

import phase12_wave3 as w3

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


@dataclass(frozen=True)
class CloneSpec:
    exp_id: str
    gold: Path
    span_ms: int
    pack: Literal["B", "C"]
    parent_id: str
    tipr_recipe: TipRRecipe
    skip_reason: str = ""
    gold_acc: str = "8/8"
    gold_thr: str = ""


def _clone(
    exp_id: str,
    span_ms: int,
    pack: Literal["B", "C"],
    parent_id: str,
    tipr_recipe: TipRRecipe,
    *,
    skip_reason: str = "",
    gold_thr: str = "",
) -> CloneSpec:
    return CloneSpec(
        exp_id=exp_id,
        gold=BRANCH / exp_id,
        span_ms=span_ms,
        pack=pack,
        parent_id=parent_id,
        tipr_recipe=tipr_recipe,
        skip_reason=skip_reason,
        gold_thr=gold_thr,
    )


def _build_wave2_clones() -> dict[str, CloneSpec]:
    rows: list[CloneSpec] = []
    # Plan order: all gen B/C by span, then preinh, then nextseg (skip nextseg@100 gate)
    for variant, tipr_for_100 in (
        ("gen", "done_tipr"),
        ("preinh", "tiprmin"),
        ("nextseginh", "tiprmin"),
    ):
        for span in (25, 50, 100):
            tipr: TipRRecipe = tipr_for_100 if (variant == "gen" and span == 100) else "tiprmin"
            for pack in ("B", "C"):
                eid = f"EXP_br_span{span}_pack{pack}_{variant}_C1e9"
                parent = f"EXP_br_span{span}_packA_{variant}_C1e9"
                skip = ""
                if variant == "nextseginh" and span == 100:
                    skip = "parent FAIL EXP_br_span100_packA_nextseginh_C1e9"
                rows.append(
                    _clone(eid, span, pack, parent, tipr, skip_reason=skip)  # type: ignore[arg-type]
                )
    return {c.exp_id: c for c in rows}


WAVE2_CLONES: dict[str, CloneSpec] = _build_wave2_clones()
WAVE2_CLONE_ORDER = list(WAVE2_CLONES.keys())

WAVE2_BR480: dict[str, ExpSpec] = {
    s.exp_id: s
    for s in (
        ExpSpec(
            exp_id="EXP_br480_tiprmin",
            gold=BRANCH / "EXP_br480_tiprmin",
            clone_name="Branch480_tiprmin",
            span_ms=480,
            train_t=600.0,
            neuron="NSPNeuronGen",
            next_seg=False,
            tipr_recipe="tiprmin",
            gold_L="85 46 25 1",
            gold_thr="0.05149",
        ),
        ExpSpec(
            exp_id="EXP_br480_nextseginh_tiprmin",
            gold=BRANCH / "EXP_br480_nextseginh_tiprmin",
            clone_name="Branch480_nextseginh_tiprmin",
            span_ms=480,
            train_t=600.0,
            neuron="NSPNeuronGen",
            next_seg=True,
            tipr_recipe="tiprmin",
            gold_L="89 46 25 1",
            gold_thr="0.036298",
        ),
        ExpSpec(
            exp_id="EXP_br480_preinh250_tiprmin",
            gold=BRANCH / "EXP_br480_preinh250_tiprmin",
            clone_name="Branch480_preinh250_tiprmin",
            span_ms=480,
            train_t=600.0,
            neuron="NSPNeuronGenPreinh2_5",
            next_seg=False,
            tipr_recipe="tiprmin",
            gold_L="97 50 25 1",
            gold_thr="0.111136",
        ),
    )
}
WAVE2_BR480_ORDER = list(WAVE2_BR480.keys())

INVEST_W2 = REPRO_ROOT / "_invest" / "w2_clone_bak"


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
                shutil.rmtree(dst, ignore_errors=True)
                if dst.exists():
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


def run_train(
    spec: ExpSpec,
    root: Path,
    *,
    dry_run: bool = False,
    max_extensions: int = 2,
) -> str:
    """Train until Need=0. If NM exits at -t with Need=1, extend up to max_extensions extra -t windows."""
    status = "incomplete_done"
    extensions = 0
    while True:
        status = _run_train_once(spec, root, dry_run=dry_run)
        if status == "done" or dry_run:
            return status
        if status in ("disk",):
            return status
        # exited_need1 / incomplete_done → extend wall
        need = read_need(root / "Train" / "Parameters_00.xml")
        if need == "0":
            return "done"
        if extensions >= max_extensions:
            return status
        extensions += 1
        print(f"TRAIN extend#{extensions}/{max_extensions} after status={status} Need={need}")


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


def _update_manifest_status(
    exp_id: str,
    status: str,
    notes: str = "",
    commit: str = "",
    path_substr: str = "",
) -> None:
    if not MANIFEST.exists():
        print(f"WARN no manifest {MANIFEST}")
        return
    text = MANIFEST.read_text(encoding="utf-8")
    status_alts = (
        "DEFERRED_PARENT_FAIL|DEFERRED|VALIDATED_CLONE|VALIDATED|FAIL_ROOTCAUSE|"
        "ARTIFACT_KEEP|FAIL|BLOCKED_FS|ARTIFACT|OUT"
    )
    if path_substr:
        pat = re.compile(
            rf"^(\| {re.escape(exp_id)} \|[^\n]*{re.escape(path_substr)}[^\n]*\| )"
            rf"({status_alts})"
            rf"( \|)",
            re.M,
        )
    else:
        pat = re.compile(
            rf"^(\| {re.escape(exp_id)} \|[^\n]*\| )"
            rf"({status_alts})"
            rf"( \|)",
            re.M,
        )
    new_text, n = pat.subn(rf"\g<1>{status}\3", text, count=1)
    if n != 1:
        print(f"WARN manifest status replace n={n} for {exp_id} path_substr={path_substr!r}")
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    log_line = f"| {utc} | {exp_id} | {status} | | | | {notes} |\n"
    for section, marker in (
        ("## Wave 6 run log", "|-----|--------|---------|---|-----|-------|-------|\n"),
        ("## Wave 5 run log", "|-----|--------|---------|---|-----|-------|-------|\n"),
        ("## Wave 3 run log", "|-----|--------|---------|---|-----|-------|-------|\n"),
        ("## Wave 2 run log", "|-----|--------|---------|---|-----|-------|-------|\n"),
        ("## Wave 1 run log", "|-----|--------|---------|---|-----|-------|-------|\n"),
    ):
        if section in new_text and marker in new_text.split(section, 1)[-1][:800]:
            idx = new_text.find(section)
            mpos = new_text.find(marker, idx)
            if mpos >= 0:
                ins = mpos + len(marker)
                new_text = new_text[:ins] + log_line + new_text[ins:]
                break
    else:
        if "## Wave 1 run log" in new_text:
            marker = "|-----|--------|---------|---|-----|-------|-------|\n"
            new_text = new_text.replace("| | | | | | | |\n", log_line, 1)
            if log_line not in new_text and marker in new_text:
                new_text = new_text.replace(marker, marker + log_line, 1)
    MANIFEST.write_text(new_text, encoding="utf-8")
    print(f"manifest {exp_id} -> {status}")


def _manifest_parent_validated(parent_id: str) -> bool:
    if not MANIFEST.exists():
        return False
    text = MANIFEST.read_text(encoding="utf-8")
    m = re.search(
        rf"^\| {re.escape(parent_id)} \|[^\n]*\| (VALIDATED|VALIDATED_CLONE) \|",
        text,
        re.M,
    )
    return m is not None


def _metrics_from_csv(csv_path: Path) -> dict[str, str]:
    if not csv_path.exists():
        return {}
    proc = subprocess.run(
        [sys.executable, str(METRICS), "-v", str(csv_path)],
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    print(out)
    d: dict[str, str] = {}
    for key in ("ok_audit", "acc", "mode", "fires", "last_pulse_ok"):
        m = re.search(rf"{key}\s*[=:]\s*(\S+)", out)
        if m:
            d[key] = m.group(1).rstrip(",")
    # also parse from CSV directly for acc
    try:
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        fires = "".join("1" if float(r.get("fired") or r.get("n_spikes") or 0) > 0 else "0" for r in rows[:8])
        if "fires" not in d and fires:
            d["fires"] = fires
        # selectivity_metrics prints structured; fallback acc count
        if "acc" not in d and rows:
            # leave empty — gate script already ran metrics
            pass
    except OSError:
        pass
    return d


def _read_thr(root: Path) -> str:
    p = root / "Test" / "Parameters_00.xml"
    if not p.exists():
        return ""
    return get_tag(p.read_text(encoding="utf-8"), "FixedLTZThreshold") or ""


def clone_gate(spec: CloneSpec, *, dry_run: bool = False) -> dict[str, str]:
    if spec.skip_reason:
        _update_manifest_status(
            spec.exp_id,
            "DEFERRED_PARENT_FAIL",
            notes=spec.skip_reason,
            path_substr="SelectivityBranch",
        )
        return {"status": "DEFERRED_PARENT_FAIL", "notes": spec.skip_reason}
    if not spec.gold.exists():
        raise SystemExit(f"missing gold {spec.gold}")
    if not _manifest_parent_validated(spec.parent_id):
        raise SystemExit(f"parent {spec.parent_id} not VALIDATED — refuse clone-gate {spec.exp_id}")

    bak = INVEST_W2 / spec.exp_id
    test = spec.gold / "Test"
    csv_p = test / "SelectivityLog" / "results.csv"
    if not dry_run:
        bak.mkdir(parents=True, exist_ok=True)
        for rel in (
            "SelectivityLog/results.csv",
            "Parameters_00.xml",
            "Model_00.xml",
        ):
            src = test / rel
            if src.exists():
                dst = bak / Path(rel).name
                if rel.startswith("SelectivityLog"):
                    dst = bak / "results.csv"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        print(f"bak -> {bak}")

    cmd = [
        sys.executable,
        str(PHASE8),
        str(spec.gold),
        "--span-ms",
        str(spec.span_ms),
        "--pack",
        spec.pack,
        "--skip-prepare",
        "--matrix-only",
        "--test-t",
        "80" if spec.span_ms >= 100 else "40",
    ]
    if spec.tipr_recipe == "done_tipr":
        cmd.append("--keep-tipr")
        cmd.append("--allow-done-tipr-fallback")
    print("CLONE_GATE", " ".join(cmd))
    if dry_run:
        return {"status": "dry"}
    log = test / "run_phase12_clone_gate.log"
    rc = subprocess.call(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    print(f"clone-gate rc={rc} log={log}")
    if not csv_p.exists():
        # restore bak
        _restore_clone_bak(spec, bak)
        _update_manifest_status(
            spec.exp_id, "FAIL", notes="no results.csv after gate", path_substr="SelectivityBranch"
        )
        raise SystemExit(f"clone-gate FAIL no csv {spec.exp_id}")
    subprocess.call([sys.executable, str(METRICS), "-v", str(csv_p)])
    snap = snapshot_gate(spec.gold)
    try:
        acc = int(snap.get("acc") or 0)
    except ValueError:
        acc = 0
    ok = snap.get("ok_audit") == "1" and acc >= 7
    thr = snap.get("thr") or _read_thr(spec.gold)
    notes = f"matrix-only pack{spec.pack}; thr={thr}; acc={acc}; ok_audit={snap.get('ok_audit')}"
    if not ok:
        _restore_clone_bak(spec, bak)
        _update_manifest_status(spec.exp_id, "FAIL", notes=notes, path_substr="SelectivityBranch")
        raise SystemExit(f"clone-gate FAIL {spec.exp_id} {notes}")
    _update_manifest_status(
        spec.exp_id, "VALIDATED_CLONE", notes=notes, path_substr="SelectivityBranch"
    )
    return {"status": "VALIDATED_CLONE", **snap, "notes": notes}


def _restore_clone_bak(spec: CloneSpec, bak: Path) -> None:
    test = spec.gold / "Test"
    for name, dst in (
        ("results.csv", test / "SelectivityLog" / "results.csv"),
        ("Parameters_00.xml", test / "Parameters_00.xml"),
        ("Model_00.xml", test / "Model_00.xml"),
    ):
        src = bak / name
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"restored {dst}")


def promote_clone(spec: CloneSpec, *, dry_run: bool = False) -> None:
    """Clone gate already wrote Test; promote_clone only re-stamps if needed."""
    if spec.skip_reason:
        _update_manifest_status(
            spec.exp_id,
            "DEFERRED_PARENT_FAIL",
            notes=spec.skip_reason,
            path_substr="SelectivityBranch",
        )
        return
    snap = snapshot_gate(spec.gold)
    acc = int(snap.get("acc") or 0)
    if snap.get("ok_audit") != "1" or acc < 7:
        raise SystemExit(f"refuse promote-clone {spec.exp_id} snap={snap}")
    notes = (
        f"matrix-only pack{spec.pack}; thr={snap.get('thr')}; "
        f"acc={acc}; fires=`{snap.get('fires')}`"
    )
    if dry_run:
        print(f"dry promote-clone {notes}")
        return
    _update_manifest_status(
        spec.exp_id, "VALIDATED_CLONE", notes=notes, path_substr="SelectivityBranch"
    )


def bin_commit_paths(paths: list[Path], message: str) -> None:
    bin_root = Path("/home/user/Nmsdk/Bin")
    rels = []
    for p in paths:
        p = p.resolve()
        try:
            rels.append(str(p.relative_to(bin_root)))
        except ValueError:
            rels.append(str(p))
    subprocess.call(["git", "add", "--"] + rels, cwd=bin_root)
    # also -u for deletions inside exp dirs
    st = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=bin_root)
    if st.returncode == 0:
        print(f"no staged changes for: {message}")
        return
    subprocess.check_call(["git", "commit", "-m", message], cwd=bin_root)
    print(f"committed: {message}")


def cmd_list_wave2(args: argparse.Namespace) -> None:
    print("=== WAVE2_CLONES ===")
    for eid in WAVE2_CLONE_ORDER:
        c = WAVE2_CLONES[eid]
        skip = f" SKIP={c.skip_reason}" if c.skip_reason else ""
        print(
            f"{eid}\tspan={c.span_ms}\tpack={c.pack}\tparent={c.parent_id}\t"
            f"recipe={c.tipr_recipe}{skip}"
        )
    print("=== WAVE2_BR480 ===")
    for eid in WAVE2_BR480_ORDER:
        s = WAVE2_BR480[eid]
        print(
            f"{eid}\tL={s.gold_L}\tthr={s.gold_thr}\tneuron={s.neuron}\t"
            f"NextSeg={int(s.next_seg)}\ttrain_t={s.train_t}"
        )


def cmd_clone_gate(args: argparse.Namespace) -> None:
    spec = WAVE2_CLONES[args.exp]
    clone_gate(spec, dry_run=args.dry_run)
    if not args.dry_run and not args.no_commit and not spec.skip_reason:
        bin_commit_paths(
            [
                MANIFEST,
                spec.gold / "Test",
            ],
            f"phase12 W2a: VALIDATED_CLONE {spec.exp_id}",
        )


def cmd_run_clones_wave2(args: argparse.Namespace) -> None:
    started = False if args.from_exp else True
    for eid in WAVE2_CLONE_ORDER:
        if not started:
            if eid == args.from_exp:
                started = True
            else:
                continue
        print(f"\n===== CLONE {eid} =====")
        spec = WAVE2_CLONES[eid]
        try:
            clone_gate(spec, dry_run=args.dry_run)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise
            continue
        if (
            not args.dry_run
            and not args.no_commit
            and not spec.skip_reason
        ):
            bin_commit_paths(
                [MANIFEST, spec.gold / "Test"],
                f"phase12 W2a: VALIDATED_CLONE {eid}",
            )


def cmd_promote_clone(args: argparse.Namespace) -> None:
    promote_clone(WAVE2_CLONES[args.exp], dry_run=args.dry_run)


def cmd_run_br480(args: argparse.Namespace) -> None:
    spec = WAVE2_BR480[args.exp]
    ns = argparse.Namespace(
        exp=args.exp,
        replicas=args.replicas,
        dry_run=args.dry_run,
        force_prepare=args.force_prepare,
    )
    # reuse cmd_run path via temporary WAVE1 lookup — call internals
    reps = tuple(range(1, args.replicas + 1))
    for rep in reps:
        root = clone_root(spec, rep)
        if not root.exists() or args.force_prepare:
            prepare_exp(
                spec,
                reps=(rep,),
                force=bool(args.force_prepare or not root.exists()),
            )
        status = run_train(spec, root, dry_run=args.dry_run)
        print(f"TRAIN_STATUS={status} r{rep}")
        if status not in ("done", "dry"):
            _update_manifest_status(
                spec.exp_id, "FAIL", notes=f"train {status} r{rep}", path_substr="SelectivityBranch"
            )
            raise SystemExit(f"train failed: {status}")
        pack_root(root, dry_run=args.dry_run)
        run_gate(spec, root, dry_run=args.dry_run)
        print(f"SNAP r{rep}: {snapshot_gate(root)}")
    v = write_compare(spec)
    if v in ("REPRO_OK_EXACT", "REPRO_OK_QUALITY", "REPRO_OK", "REPRO_SOFT"):
        print(f"PASS candidate verdict={v}")
        if not args.dry_run and not args.no_promote:
            promote_pass(spec, dry_run=False)
            if not args.no_commit:
                bin_commit_paths(
                    [MANIFEST, spec.gold],
                    f"phase12 W2b: VALIDATED {spec.exp_id}",
                )
    else:
        _update_manifest_status(
            spec.exp_id, "FAIL", notes=f"verdict={v}", path_substr="SelectivityBranch"
        )
        raise SystemExit(f"compare FAIL {v}")


def cmd_run_br480_all(args: argparse.Namespace) -> None:
    for eid in WAVE2_BR480_ORDER:
        print(f"\n===== BR480 {eid} =====")
        ns = argparse.Namespace(
            exp=eid,
            replicas=args.replicas,
            dry_run=args.dry_run,
            force_prepare=args.force_prepare,
            no_promote=args.no_promote,
            no_commit=args.no_commit,
        )
        try:
            cmd_run_br480(ns)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise


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
    # disambiguate same exp_id across families (AsymRm vs LtzCal)
    path_hint = ""
    try:
        path_hint = str(spec.gold.relative_to(ROOT)).split("/")[0]
    except ValueError:
        path_hint = spec.gold.parent.name
    _update_manifest_status(spec.exp_id, "VALIDATED", notes=notes, path_substr=path_hint)
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

    p = sub.add_parser("list-wave2")
    p.set_defaults(func=cmd_list_wave2)

    p = sub.add_parser("clone-gate")
    p.add_argument("--exp", required=True, choices=WAVE2_CLONE_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(func=cmd_clone_gate)

    p = sub.add_parser("run-clones-wave2")
    p.add_argument("--from", dest="from_exp", default=None, choices=WAVE2_CLONE_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.set_defaults(func=cmd_run_clones_wave2)

    p = sub.add_parser("promote-clone")
    p.add_argument("--exp", required=True, choices=WAVE2_CLONE_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_promote_clone)

    p = sub.add_parser("run-br480")
    p.add_argument("--exp", required=True, choices=WAVE2_BR480_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(func=cmd_run_br480)

    p = sub.add_parser("run-br480-all")
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.set_defaults(func=cmd_run_br480_all)

    w3.register_wave3_cli(sub)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
