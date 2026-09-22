#!/usr/bin/env python3
"""PHASE9 P2: AsymRm silent mid (ltz_potential_max) + gate. No Train."""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

NM = Path("/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
ROOT = Path("/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain")
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
SILENT_THR = "1.0"
sys.path.insert(0, str(ROOT / "scripts"))
from repro_cold_lib import ensure_tag_after, get_tag, overlay_neuron, set_tag  # noqa: E402


def set_fixed_thr(path: Path, thr: str) -> None:
    t = path.read_text(encoding="utf-8")
    for tag in ("FixedLTZThreshold", "LTZThreshold"):
        t = set_tag(t, tag, thr, 1)
    t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
    t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
    path.write_text(t, encoding="utf-8")


def overlay_train_params(train: Path, test: Path) -> str:
    """Copy TipR / mid / lengths / PostTune enables from Train onto Test."""
    train_p = (train / "Parameters_00.xml").read_text(encoding="utf-8")
    tipr = get_tag(train_p, "TipSynapseResistance") or ""
    thr = get_tag(train_p, "FixedLTZThreshold") or SILENT_THR
    # Prefer C++ inference mid already written on Test.
    flag = test / "posttune_complete.flag"
    if flag.exists():
        for line in flag.read_text(encoding="utf-8").splitlines():
            if line.startswith("mid="):
                mid_s = line.split("=", 1)[1].split()[0]
                try:
                    if float(mid_s.replace(",", ".")) < 0.9:
                        thr = mid_s
                except ValueError:
                    pass
                break
    rmin = get_tag(train_p, "ResistanceMin") or "20000000"
    lens = get_tag(train_p, "DendriteLength") or ""
    mode = get_tag(train_p, "PostTrainTipResistanceMode") or "1"
    if (train / "Model_00.xml").exists() and (test / "Model_00.xml").exists():
        overlay_neuron(train / "Model_00.xml", test / "Model_00.xml")
    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = test / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if tipr:
            t = set_tag(t, "TipSynapseResistance", tipr, 1)
        if rmin:
            t = set_tag(t, "ResistanceMin", rmin, 1)
        if lens:
            t = set_tag(t, "DendriteLength", lens, 1)
        t = set_tag(t, "FixedLTZThreshold", thr, 1)
        t = set_tag(t, "LTZThreshold", thr, 1)
        t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
        t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
        t = set_tag(t, "IsNeedToTrain", "0", 1)
        t = set_tag(t, "EnablePostTrainTuning", "1", 1)
        # Learner StructureBuildMode=1 so tip names match DendriteLength (inference mid).
        t = set_tag(t, "StructureBuildMode", "1", 1)
        if get_tag(t, "EnablePostTrainMidThreshold") is None:
            t = ensure_tag_after(
                t, "EnablePostTrainTuning", "EnablePostTrainMidThreshold", "1",
                attrs=' Type="b" PType="257" IoType="17"',
            )
        else:
            t = set_tag(t, "EnablePostTrainMidThreshold", "1", 1)
        if get_tag(t, "PostTrainTipResistanceMode") is None:
            t = ensure_tag_after(
                t, "EnablePostTrainMidThreshold", "PostTrainTipResistanceMode", mode,
                attrs=' Type="i" PType="257" IoType="17"',
            )
        else:
            t = set_tag(t, "PostTrainTipResistanceMode", mode, 1)
        if get_tag(t, "PostTrainSilentThreshold") is None:
            t = ensure_tag_after(
                t, "PostTrainTipResistanceMode", "PostTrainSilentThreshold", "1",
                attrs=' Type="d" PType="257" IoType="17"',
            )
        else:
            t = set_tag(t, "PostTrainSilentThreshold", "1", 1)
        # Physics-based iteration gap on Test (inference mid free-run).
        if get_tag(t, "AutoScaleIterationGap") is None:
            t = ensure_tag_after(
                t, "IterationGap", "AutoScaleIterationGap", "1",
                attrs=' Type="b" PType="257" IoType="17"',
            )
        else:
            t = set_tag(t, "AutoScaleIterationGap", "1", 1)
        p.write_text(t, encoding="utf-8")
    return thr


def hard_deadline_s(tsec: float, span_ms: int | None = None) -> float:
    """Wall-clock hard stop for NM runs (span-aware)."""
    if span_ms is None:
        if tsec >= 80:
            span_ms = 480
        elif tsec >= 40:
            span_ms = 100
        elif tsec >= 20:
            span_ms = 50
        else:
            span_ms = 25
    mult = {25: 20, 50: 20, 100: 30, 480: 45}.get(span_ms, 30)
    floor = {25: 900, 50: 1200, 100: 1800, 480: 3600}.get(span_ms, 1800)
    return max(float(tsec) * mult, float(floor))


def run_nm(ini: Path, tsec: float, log: Path, *, span_ms: int | None = None) -> int:
    """Run NM; SIGTERM when SelectivityLog has ≥8 rows (avoids hang after CSV)."""
    import time
    import shutil

    # Drop prior StatisticLog to avoid balloon hang.
    slog = ini.parent / "StatisticLog"
    if slog.is_dir():
        shutil.rmtree(slog, ignore_errors=True)

    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tsec), "-x"]
    csv_path = ini.parent / "SelectivityLog" / "results.csv"
    with log.open("w") as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    hard_deadline = time.time() + hard_deadline_s(tsec, span_ms)
    while proc.poll() is None:
        if time.time() > hard_deadline:
            print(f"SIGTERM NM (hard deadline) pid={proc.pid}")
            proc.terminate()
            break
        if csv_path.exists():
            try:
                n = sum(1 for _ in csv_path.open(encoding="utf-8")) - 1
            except OSError:
                n = 0
            try:
                et = int(
                    subprocess.check_output(
                        ["ps", "-o", "etimes=", "-p", str(proc.pid)], text=True
                    ).strip()
                    or "0"
                )
            except subprocess.CalledProcessError:
                et = 0
            # span50/100: wait until 8 rows; allow long wall before early stop
            if n >= 8 and et > max(int(tsec), 180):
                print(f"SIGTERM NM pid={proc.pid} n={n} et={et}")
                proc.terminate()
                break
        time.sleep(2)
    try:
        return proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=30)


def col_from_csv(csv_path: Path, col: str) -> list[float]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    out = []
    for r in rows:
        v = r.get(col) or "0"
        try:
            out.append(float(v))
        except ValueError:
            out.append(0.0)
    return out


def mid_thr(vals: list[float]) -> tuple[float, float]:
    tgt = vals[0]
    below = [s for s in vals[1:] if s < tgt]
    foil = max(below) if below else max(vals[1:] or [0.0])
    gap = tgt - foil
    mid = 0.5 * (tgt + foil) if below else tgt * 0.99
    return mid, gap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_root", type=Path)
    ap.add_argument("--test-t", type=float, default=40.0)
    ap.add_argument("--silent-thr", default=SILENT_THR)
    ap.add_argument(
        "--metric",
        default="ltz_potential_max",
        choices=("ltz_potential_max", "soma_amp_sum"),
    )
    ap.add_argument(
        "--skip-tipr-mid",
        action="store_true",
        help="Skip silent mid; keep Train TipR/FixedLTZ (C++ PostTune); gate only",
    )
    ap.add_argument(
        "--span-ms",
        type=int,
        default=None,
        help="Pattern span for NM hard-deadline (25|50|100|480)",
    )
    args = ap.parse_args()
    root = args.exp_root.resolve()
    train, test = root / "Train", root / "Test"
    csv_path = test / "SelectivityLog" / "results.csv"
    span_ms = args.span_ms

    if args.skip_tipr_mid:
        thr = overlay_train_params(train, test)
        try:
            mid_v = float((thr or "1").replace(",", "."))
        except ValueError:
            mid_v = 1.0
        if mid_v >= 0.9:
            print(
                f"skip-tipr-mid: thr={thr} (silent) — C++ inference mid then gate"
            )
            if csv_path.exists():
                csv_path.unlink()
            flag = test / "posttune_complete.flag"
            if flag.exists():
                flag.unlink()
            # Ensure learner StructureBuildMode=1 for tip name resolution.
            for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
                if p.exists():
                    t = p.read_text(encoding="utf-8")
                    t = set_tag(t, "StructureBuildMode", "1", 1)
                    p.write_text(t, encoding="utf-8")
            mlog = test / "run_infer_mid.log"
            cmd_mid = [str(NM), "-c", str(test / "Project.ini"), "-s", "-t", "40", "-x"]
            import time as _time
            import shutil as _shutil

            slog = test / "StatisticLog"
            if slog.is_dir():
                _shutil.rmtree(slog, ignore_errors=True)

            proc = subprocess.Popen(
                cmd_mid, stdout=mlog.open("w"), stderr=subprocess.STDOUT
            )
            mid_s2 = None
            # Matrix free-run mid ~7–15 min wall; allow ~30 min
            for _ in range(360):
                _time.sleep(5)
                if flag.exists():
                    for line in flag.read_text(encoding="utf-8").splitlines():
                        if line.startswith("mid="):
                            mid_s2 = line.split("=", 1)[1].split()[0]
                            break
                    _time.sleep(2)
                    proc.terminate()
                    try:
                        proc.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    break
                if proc.poll() is not None:
                    break
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
            if not mid_s2:
                raise SystemExit("C++ inference mid did not write posttune_complete.flag")
            try:
                mid_f = float(mid_s2.replace(",", "."))
            except ValueError:
                mid_f = 1.0
            if mid_f >= 0.9:
                raise SystemExit(f"inference mid still silent: {mid_s2}")
            for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
                if p.exists():
                    set_fixed_thr(p, mid_s2)
            print(f"inference mid={mid_s2}; gate pass")
            if csv_path.exists():
                csv_path.unlink()
            if slog.is_dir():
                _shutil.rmtree(slog, ignore_errors=True)
            glog = test / "run_gate.log"
            rc = run_nm(test / "Project.ini", args.test_t, glog, span_ms=span_ms)
            print("gate rc", rc)
            if not csv_path.exists():
                raise SystemExit("no gate results.csv")
            subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_path)])
            print("thr", mid_s2)
            return
        print(f"skip silent mid; thr={thr}")
        glog = test / "run_gate.log"
        rc = run_nm(test / "Project.ini", args.test_t, glog, span_ms=span_ms)
        print("gate rc", rc)
        if not csv_path.exists():
            raise SystemExit("no gate results.csv")
        subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_path)])
        print("thr", thr)
        return

    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        if p.exists():
            set_fixed_thr(p, args.silent_thr)

    slog = test / "run_silent_probe.log"
    rc = run_nm(test / "Project.ini", args.test_t, slog, span_ms=span_ms)
    print("silent rc", rc)
    if not csv_path.exists():
        raise SystemExit("no silent results.csv")
    archived = test / "SelectivityLog" / "results_silent_thr1.csv"
    shutil.copy2(csv_path, archived)
    vals = col_from_csv(archived, args.metric)
    print(args.metric, vals)
    if len(vals) < 8 or max(vals) <= 0:
        # fallback soma if ltz all zero
        if args.metric == "ltz_potential_max":
            vals = col_from_csv(archived, "soma_amp_sum")
            print("fallback soma_amp_sum", vals)
            if len(vals) < 8 or max(vals) <= 0:
                raise SystemExit("silent FAIL")
        else:
            raise SystemExit("silent FAIL")
    mid, gap = mid_thr(vals[:8])
    print(f"mid={mid} gap={gap}")
    if gap <= 0:
        print("FAIL gap<=0", file=sys.stderr)
        sys.exit(3)
    mid_s = f"{mid:.12g}"
    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        if p.exists():
            set_fixed_thr(p, mid_s)

    glog = test / "run_gate.log"
    rc = run_nm(test / "Project.ini", args.test_t, glog, span_ms=span_ms)
    print("gate rc", rc)
    subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_path)])
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if rows:
        r0 = rows[0]
        t_rel = float(r0.get("neuron_t_rel") or -1)
        isis = [float(r0.get(f"isi{i}") or 0) for i in range(3)]
        pend = sum(isis)
        print(
            f"last-pulse t_rel={t_rel} pattern_end={pend} "
            f"ok={t_rel >= 0.8 * pend if t_rel >= 0 and pend else False}"
        )
    print("thr", mid_s)


if __name__ == "__main__":
    main()
