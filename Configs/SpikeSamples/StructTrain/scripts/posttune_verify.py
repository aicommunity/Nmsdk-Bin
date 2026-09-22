#!/usr/bin/env python3
"""PostTune verification: soft-cold → train → snapshot (no tiprmin) → gate → compare gold."""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from repro_cold_lib import (  # noqa: E402
    NM,
    assert_disk_for_train,
    free_gib,
    get_tag,
    set_tag,
    soft_cold_reset_train,
    tipr_looks_posttuned,
)

PHASE8 = ROOT / "SelectivityBranch" / "scripts" / "phase8_tiprmin_gate.py"
PHASE9 = ROOT / "SelectivityAsymRm" / "scripts" / "phase9_preinh_bc_gate.py"
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
OUT = ROOT / "_repro" / "POSTTUNE_VERIFY_RESULT.md"

CASES = {
    "br25_on": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9_posttune",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9",
        "train_t": 320.0,
        "span_ms": 25,
        "kind": "branch",
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
    },
    "br25_off": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9_posttune_off",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9",
        "train_t": 320.0,
        "span_ms": 25,
        "kind": "branch",
        "expect_tipr": "legacy",
        "skip_tipr_mid": False,
    },
    "asym25": {
        "root": ROOT / "SelectivityAsymRm" / "EXP_span25ms_packA_gen_posttune",
        "gold": ROOT / "SelectivityAsymRm" / "EXP_span25ms_packA_gen",
        "train_t": 160.0,
        "span_ms": 25,
        "kind": "asym",
        "expect_tipr": "flat",
        "skip_tipr_mid": True,
    },
    "br100_keep": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9_posttune_keep",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9",
        "train_t": 640.0,
        "span_ms": 100,
        "kind": "branch",
        "expect_tipr": "keep",
        "skip_tipr_mid": True,
    },
    "br100_search": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9_posttune_search",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9",
        "train_t": 2400.0,
        "span_ms": 100,
        "kind": "branch",
        "expect_tipr": "search",
        "skip_tipr_mid": True,
        "expect_fires": "10000000",
    },
    "asym50": {
        "root": ROOT / "SelectivityAsymRm" / "EXP_span50ms_packA_gen_posttune",
        "gold": ROOT / "SelectivityAsymRm" / "EXP_span50ms_packA_gen",
        "train_t": 320.0,
        "span_ms": 50,
        "kind": "asym",
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
    },
    "phase6_480": {
        "root": ROOT / "SelectivityPhaseA" / "Phase6" / "EXP_480_gen_posttune",
        "gold": ROOT / "SelectivityPhaseA" / "Phase6" / "EXP_480_gen_tiprmin",
        "train_t": 900.0,
        "span_ms": 480,
        "kind": "phase6",
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
        "expect_fires": "10000010",
    },
}


def snap_params(params: Path) -> dict[str, str]:
    t = params.read_text(encoding="utf-8") if params.exists() else ""
    keys = (
        "TipSynapseResistance",
        "FixedLTZThreshold",
        "ResistanceMin",
        "IsNeedToTrain",
        "EnablePostTrainTuning",
        "PostTrainTipResistanceMode",
        "PostTrainTuneComplete",
        "TrainingPhase",
        "DendriteLength",
    )
    return {k: (get_tag(t, k) or "") for k in keys}


def _latest_stat_dir(train: Path) -> Path | None:
    slog = train / "StatisticLog"
    if not slog.is_dir():
        return None
    dirs = [p for p in slog.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def _last_trace_vector(stat_dir: Path, name: str) -> list[str] | None:
    path = stat_dir / f"NeuronTimeLearnerBranch.{name}.txt"
    if not path.exists():
        path = stat_dir / f"NeuronTimeLearner.{name}.txt"
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if not lines:
        return None
    # format: index time \t v0 \t v1 \t ...
    parts = lines[-1].replace(",", ".").split()
    if len(parts) < 3:
        return None
    return parts[2:]


def flush_posttune_artifacts(train: Path) -> None:
    """NM -S often does not flush Parameters on SIGTERM; rebuild Train XML from flag+traces."""
    flag = train / "posttune_complete.flag"
    mid = None
    tipr_s = None
    if flag.exists():
        for line in flag.read_text(encoding="utf-8").splitlines():
            if line.startswith("mid="):
                mid = line.split("=", 1)[1].split()[0]
            elif line.startswith("tipr="):
                tipr_s = line.split("=", 1)[1].strip()
    live = train / "posttune_tipr_live.txt"
    if live.exists() and not tipr_s:
        for line in live.read_text(encoding="utf-8").splitlines():
            if line.startswith("tipr="):
                tipr_s = line.split("=", 1)[1].strip()
    stat_dir = _latest_stat_dir(train)
    tipr = _last_trace_vector(stat_dir, "TipSynapseResistanceTrace") if stat_dir else None
    lens = _last_trace_vector(stat_dir, "DendriteLengthTrace") if stat_dir else None
    if live.exists() and not lens:
        for line in live.read_text(encoding="utf-8").splitlines():
            if line.startswith("L="):
                lens = line.split("=", 1)[1].split()
                break
    if not tipr_s and tipr:
        tipr_s = " ".join(tipr[:4])
    lens_s = " ".join(str(int(float(x))) for x in lens[:4]) if lens else None
    if not tipr_s and not mid and not lens_s:
        print("flush_posttune_artifacts: nothing to flush")
        return
    print(f"flush_posttune_artifacts mid={mid} TipR={tipr_s} L={lens_s}")
    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = train / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if tipr_s:
            t = set_tag(t, "TipSynapseResistance", tipr_s, 1)
            t = set_tag(t, "ResistanceMin", "20000000", 1)
        if lens_s:
            t = set_tag(t, "DendriteLength", lens_s, 1)
        if mid:
            t = set_tag(t, "FixedLTZThreshold", mid, 1)
            t = set_tag(t, "LTZThreshold", mid, 1)
            t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
            t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
        # Only clear Need when PostTune wrote a completion flag (or mid).
        if flag.exists() or mid:
            t = set_tag(t, "IsNeedToTrain", "0", 1)
        p.write_text(t, encoding="utf-8")


def wait_need0(train: Path, tlim: float, log: Path, *, max_polls: int = 401) -> str:
    ini = train / "Project.ini"
    assert_disk_for_train()
    # Drop prior StatisticLog so a stalled Need=1 run cannot grow to tens of GB.
    slog = train / "StatisticLog"
    if slog.is_dir():
        shutil.rmtree(slog, ignore_errors=True)
    flag = train / "posttune_complete.flag"
    if flag.exists():
        flag.unlink()
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    print(f"TRAIN {train.parent.name} -t {tlim} Avail={free_gib():.0f}G polls={max_polls}")
    proc = subprocess.Popen(cmd, cwd=str(train), stdout=log.open("w"), stderr=subprocess.STDOUT)
    need0 = False
    for i in range(1, max_polls + 1):
        time.sleep(30)
        if proc.poll() is not None:
            break
        need = get_tag((train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain")
        flag_hit = flag.exists()
        # Guard: abort if StatisticLog balloons (prior hang rootcause ~17GB).
        slog_bytes = 0
        if slog.is_dir():
            for p in slog.rglob("*"):
                if p.is_file():
                    try:
                        slog_bytes += p.stat().st_size
                    except OSError:
                        pass
        slog_gib = slog_bytes / (1 << 30)
        print(
            f"  poll#{i} Need={need} flag={int(flag_hit)} "
            f"slog={slog_gib:.2f}G et~{i * 30}s"
        )
        if slog_gib > 2.0:
            # Snapshot TipR/L traces before prune (Search can outlive StatisticLog).
            stat_dir = _latest_stat_dir(train)
            tipr = _last_trace_vector(stat_dir, "TipSynapseResistanceTrace") if stat_dir else None
            lens = _last_trace_vector(stat_dir, "DendriteLengthTrace") if stat_dir else None
            live = train / "posttune_tipr_live.txt"
            parts = []
            if tipr:
                parts.append("tipr=" + " ".join(tipr[:4]))
            if lens:
                parts.append("L=" + " ".join(str(int(float(x))) for x in lens[:4]))
            if parts:
                live.write_text("\n".join(parts) + "\n", encoding="utf-8")
                print(f"  SNAP {live.name}: {parts[0][:60]}")
            print(f"  PRUNE StatisticLog {slog_gib:.2f}G — keep Train running")
            shutil.rmtree(slog, ignore_errors=True)
            continue
        if slog_gib > 12.0:
            print(f"  ABORT StatisticLog>{slog_gib:.1f}G after prune failed — terminate NM")
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
            break
        if need == "0" or flag_hit:
            need0 = True
            # allow finalize + optional -S; then terminate
            time.sleep(20)
            proc.terminate()
            try:
                proc.wait(timeout=90)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
            break
    else:
        proc.terminate()
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
    flush_posttune_artifacts(train)
    need = get_tag((train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain")
    if need == "0" or flag.exists():
        return "done"
    return "incomplete" if need0 else "exited"


def parse_flag_meta(flag: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not flag.exists():
        return out
    for line in flag.read_text(encoding="utf-8").splitlines():
        for tok in line.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                out[k] = v
    return out


def count_events_mode4(side: Path) -> int:
    elog = side / "EventsLog"
    if not elog.is_dir():
        return 0
    n = 0
    for p in elog.rglob("*"):
        if not p.is_file():
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        n += len(re.findall(r"phase\s*->\s*PostTune\s+mode=4", txt))
        n += len(re.findall(r"PostTune mode=4", txt))
    return n


def tipr_vs_keep(tipr: str, keep_tipr: str, search_reverted: bool) -> str:
    a = " ".join((tipr or "").replace(",", " ").split()[:4])
    b = " ".join((keep_tipr or "").replace(",", " ").split()[:4])
    if not a or not b:
        return "unknown"
    if a == b:
        return "same_reverted" if search_reverted else "same_FAIL"
    return "diff"


def mid_source_of(flag_meta: dict[str, str], thr: str) -> str:
    try:
        mid_f = float((flag_meta.get("mid") or thr or "1").replace(",", "."))
    except ValueError:
        mid_f = 1.0
    if flag_meta.get("inference") == "1" and mid_f < 0.9:
        return "cpp"
    if mid_f < 0.9 and flag_meta.get("mid"):
        return "cpp_train"
    return "missing"


def fires_from_csv(csv_path: Path) -> tuple[str, str]:
    if not csv_path.exists():
        return "", ""
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if not rows:
        return "", ""
    fires = "".join("1" if (r.get("neuron_fired") or "0") not in ("0", "0.0", "") else "0" for r in rows[:8])
    # prefer acc from metrics script
    try:
        out = subprocess.check_output(
            [sys.executable, str(METRICS), str(csv_path)], text=True, stderr=subprocess.STDOUT
        )
        m = re.search(r"acc_legacy[=:]?\s*([0-9.]+)", out) or re.search(r"acc[=:]?\s*([0-9/]+)", out)
        acc = m.group(1) if m else str(sum(int(c) for c in fires[:1]) and "")
        # metrics prints summary line — keep last non-empty
        for line in reversed(out.strip().splitlines()):
            if "acc" in line.lower() or "ok_audit" in line:
                return fires, line.strip()
        return fires, acc
    except subprocess.CalledProcessError as e:
        return fires, e.output[-200:] if e.output else "metrics_fail"


def run_gate(case: dict) -> tuple[str, str]:
    root: Path = case["root"]
    test = root / "Test"
    span = int(case.get("span_ms", 25))
    if case["kind"] == "branch":
        cmd = [
            sys.executable,
            str(PHASE8),
            str(root),
            "--span-ms",
            str(span),
            "--pack",
            "A",
            "--test-t",
            "40",
        ]
        if case["skip_tipr_mid"]:
            cmd.append("--skip-tipr-mid")
        else:
            cmd.append("--force-python-hygiene")
    else:
        # asym + phase6: phase9 LTZ mid path
        test_t = "40" if span < 100 else ("80" if span < 480 else "80")
        cmd = [
            sys.executable,
            str(PHASE9),
            str(root),
            "--test-t",
            test_t,
            "--span-ms",
            str(span),
            "--metric",
            "ltz_potential_max",
        ]
        if case["skip_tipr_mid"]:
            cmd.append("--skip-tipr-mid")
    log = test / "run_posttune_gate.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    print("GATE", " ".join(cmd))
    rc = subprocess.call(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    print("gate rc", rc)
    return fires_from_csv(test / "SelectivityLog" / "results.csv")


def tipr_class(tipr: str, expect: str = "") -> str:
    if expect in ("keep", "search", "legacy"):
        if tipr_looks_posttuned(tipr):
            nums = [float(x) for x in tipr.replace(",", " ").split()[:4]]
            return "flat" if abs(nums[0] - 8.6e7) < 1e5 else "canon"
        return expect if expect != "legacy" else "other"
    if tipr_looks_posttuned(tipr):
        nums = [float(x) for x in tipr.replace(",", " ").split()[:4]]
        if abs(nums[0] - 8.6e7) < 1e5:
            return "flat"
        return "canon"
    return "other"


def run_case(name: str, *, skip_train: bool = False) -> dict:
    case = CASES[name]
    root: Path = case["root"]
    gold: Path = case["gold"]
    train = root / "Train"
    print(f"\n=== CASE {name} root={root.name} ===")
    if name == "br100_search" and skip_train:
        raise SystemExit(
            "br100_search: --skip-train forbidden — SearchSynthetic requires Train mode=4"
        )
    if not skip_train:
        soft_cold_reset_train(train)
        # Always ensure PostTune tags survive soft_cold (insert if missing).
        from repro_cold_lib import ensure_tag_after

        mode = {
            "br25_on": "1",
            "br25_off": "0",
            "asym25": "2",
            "br100_keep": "3",
            "br100_search": "4",
            "asym50": "1",
            "phase6_480": "1",
        }.get(name, "1")
        enable = "0" if name == "br25_off" else "1"
        for rel in ("Parameters_00.xml", "Model_00.xml"):
            p = train / rel
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8")
            t = ensure_tag_after(t, "IsNeedToTrain", "EnablePostTrainTuning", enable)
            t = set_tag(t, "EnablePostTrainTuning", enable, 1)
            # Physics-based gap: ignore XML IterationGap=1.5 floor.
            t = ensure_tag_after(
                t, "IterationGap", "AutoScaleIterationGap", "1",
                attrs=' Type="b" PType="257" IoType="17"',
            )
            t = set_tag(t, "AutoScaleIterationGap", "1", 1)
            if enable == "1":
                t = ensure_tag_after(
                    t, "EnablePostTrainTuning", "EnablePostTrainMidThreshold", "1",
                    attrs=' Type="b" PType="257" IoType="17"',
                )
                t = set_tag(t, "EnablePostTrainMidThreshold", "1", 1)
                t = ensure_tag_after(
                    t, "EnablePostTrainMidThreshold", "PostTrainTipResistanceMode", mode,
                    attrs=' Type="i" PType="257" IoType="17"',
                )
                t = set_tag(t, "PostTrainTipResistanceMode", mode, 1)
                t = ensure_tag_after(
                    t, "PostTrainTipResistanceMode", "PostTrainSilentThreshold", "1",
                    attrs=' Type="d" PType="257" IoType="17"',
                )
                t = set_tag(t, "PostTrainSilentThreshold", "1", 1)
                if mode == "4":
                    t = ensure_tag_after(
                        t, "PostTrainSilentThreshold", "PostTrainTipSearchIters", "12",
                        attrs=' Type="i" PType="257" IoType="17"',
                    )
                    t = set_tag(t, "PostTrainTipSearchIters", "12", 1)
            p.write_text(t, encoding="utf-8")
            print(
                f"  PostTune tags {rel}: enable={enable} mode="
                f"{get_tag(p.read_text(encoding='utf-8'), 'PostTrainTipResistanceMode')} "
                f"auto_gap="
                f"{get_tag(p.read_text(encoding='utf-8'), 'AutoScaleIterationGap')}"
            )
        # SearchSynthetic: AutoScale gapEff≈0.3 → ~8h wall budget still ample.
        polls = 800 if name == "br100_search" else 401
        status = wait_need0(
            train, case["train_t"], train / "run_posttune_verify.log", max_polls=polls
        )
    else:
        status = "skip_train"
    after = snap_params(train / "Parameters_00.xml")
    # Prefer Test mid from flag when Train left silent thr.
    test_flag = root / "Test" / "posttune_complete.flag"
    train_flag = train / "posttune_complete.flag"
    flag_meta = parse_flag_meta(test_flag)
    if not flag_meta.get("mid"):
        flag_meta = {**parse_flag_meta(train_flag), **flag_meta}
    if test_flag.exists():
        for line in test_flag.read_text(encoding="utf-8").splitlines():
            if line.startswith("mid="):
                after["FixedLTZThreshold"] = line.split("=", 1)[1].split()[0]
                break
    gold_test = snap_params(gold / "Test" / "Parameters_00.xml")
    fires, metrics_line = run_gate(case)
    # After gate, refresh mid from Test params / flag
    flag_meta = {**flag_meta, **parse_flag_meta(test_flag)}
    if test_flag.exists():
        for line in test_flag.read_text(encoding="utf-8").splitlines():
            if line.startswith("mid="):
                after["FixedLTZThreshold"] = line.split("=", 1)[1].split()[0]
                break
    tp = snap_params(root / "Test" / "Parameters_00.xml")
    if tp.get("FixedLTZThreshold") and float(tp["FixedLTZThreshold"].replace(",", ".") or "1") < 0.9:
        after["FixedLTZThreshold"] = tp["FixedLTZThreshold"]

    mid_src = mid_source_of(flag_meta, after.get("FixedLTZThreshold", ""))
    search_reverted = flag_meta.get("search_reverted") == "1"
    # Also accept EventsLog marker if flag lacks the token (older builds).
    mode4_n = count_events_mode4(train) + count_events_mode4(root / "Test")
    tipr_keep = ""
    tipr_vs = ""
    if name == "br100_search":
        keep_root = ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9_posttune_keep"
        tipr_keep = snap_params(keep_root / "Train" / "Parameters_00.xml").get(
            "TipSynapseResistance", ""
        ) or snap_params(keep_root / "Test" / "Parameters_00.xml").get(
            "TipSynapseResistance", ""
        )
        tipr_vs = tipr_vs_keep(
            after.get("TipSynapseResistance", ""), tipr_keep, search_reverted
        )
        if mode4_n < 1 and status != "skip_train":
            # Soft assert via status annotation — EventsLog may be off.
            print(f"  WARN mode4 EventsLog count={mode4_n}")
        if tipr_vs == "same_FAIL":
            status = "search_same_as_keep_FAIL"
        elif tipr_vs == "same_reverted":
            status = "done_search_reverted"
        elif tipr_vs == "diff":
            status = "done_search_diff"
        if mid_src != "cpp":
            status = f"{status}_no_cpp_mid"

    # Cleanup huge logs after case.
    for side in (train, root / "Test"):
        for dname in ("StatisticLog", "EventsLog"):
            d = side / dname
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)

    return {
        "case": name,
        "train_status": status,
        "after": after,
        "gold_thr": gold_test.get("FixedLTZThreshold", ""),
        "gold_tipr": gold_test.get("TipSynapseResistance", ""),
        "tipr_class": tipr_class(after.get("TipSynapseResistance", ""), case.get("expect_tipr", "")),
        "fires": fires,
        "metrics": metrics_line,
        "expect_tipr": case["expect_tipr"],
        "expect_fires": case.get("expect_fires", "10000000"),
        "mid_source": mid_src,
        "tipr_vs_keep": tipr_vs,
        "search_reverted": int(search_reverted),
        "mode4_events": mode4_n,
    }


def append_result(rows: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PostTune verify result",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Console: `{NM}`",
        "",
        "| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_keep | metrics |",
        "|------|-------|------|------------|------|----------|----------|-------|------------|--------------|---------|",
    ]
    for r in rows:
        a = r["after"]
        lines.append(
            "| {case} | {st} | {need} | {tc} | `{tipr}` | {thr} | {gthr} | `{fires}` | {ms} | {tv} | {met} |".format(
                case=r["case"],
                st=r["train_status"],
                need=a.get("IsNeedToTrain", ""),
                tc=r["tipr_class"],
                tipr=(a.get("TipSynapseResistance") or "")[:48],
                thr=a.get("FixedLTZThreshold", ""),
                gthr=r["gold_thr"],
                fires=r["fires"],
                ms=r.get("mid_source", ""),
                tv=r.get("tipr_vs_keep", "") or "—",
                met=(r["metrics"] or "")[:80].replace("|", "/"),
            )
        )
        # Fail loudly if gold-mid fallback sneaks back in.
        if "gold_mid" in str(r.get("train_status", "")):
            lines.append("")
            lines.append(f"**FAIL**: `{r['case']}` used gold_mid fallback — not allowed.")
        if r["case"] in ("asym50", "phase6_480", "br100_search") and r.get("mid_source") != "cpp":
            lines.append("")
            lines.append(f"**FAIL**: `{r['case']}` mid_source={r.get('mid_source')} (need cpp).")
        if r["case"] == "br100_search" and r.get("tipr_vs_keep") == "same_FAIL":
            lines.append("")
            lines.append("**FAIL**: br100_search TipR == keep without search_reverted.")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE", OUT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=list(CASES) + ["all"], default="all")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()
    names = list(CASES) if args.case == "all" else [args.case]
    rows = [run_case(n, skip_train=args.skip_train) for n in names]
    append_result(rows)


if __name__ == "__main__":
    main()
