#!/usr/bin/env python3
"""PHASE10 T1.1: TipR Done/partial/rmin retry + soma silent mid on br480 clone."""
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
DEFAULT_TIPR_SRC = (
    ROOT / "TimeNeuronTimeLearnerBranch_PreInh250" / "Train" / "Parameters_00.xml"
)
TIPRMIN = "20000000 20000000 20000000 86000000"
RMIN = "20000000"
SILENT_THR = "1.0"


def set_tag(text: str, tag: str, value: str) -> str:
    return re.sub(
        rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
        lambda m: m.group(1) + value + m.group(2),
        text,
    )


def get_tag(text: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).strip() if m else None


def normalize_tipr(raw: str) -> str:
    # locale commas → dots inside each of 4 numbers
    parts = raw.replace(",", ".").split()
    if len(parts) != 4:
        raise SystemExit(f"TipR expected 4 values, got {parts!r} from {raw!r}")
    return " ".join(parts)


def patch_tip_exc_r(text: str, tips: list[int], tipr_vals: list[str]) -> str:
    for i, L in enumerate(tips):
        r = tipr_vals[i] if i < len(tipr_vals) else tipr_vals[-1]
        # for rmin mode tips 0..2 = 2e7, tip3 = 8.6e7 — already in tipr_vals
        pat = re.compile(
            rf'(<Dendrite1_{L} Class="[^"]+">.*?<ExcSynapse1 Class="[^"]+">'
            rf'.*?<Resistance Type="d"[^>]*>)[^<]*(</Resistance>)',
            re.S,
        )
        text, n = pat.subn(lambda m, _r=r: m.group(1) + _r + m.group(2), text, count=1)
        if not n:
            print(f"WARN: no ExcSynapse Resistance for Dendrite1_{L}", file=sys.stderr)
    return text


def set_fixed_thr(path: Path, thr: str) -> None:
    t = path.read_text(encoding="utf-8")
    for tag in ("FixedLTZThreshold", "LTZThreshold"):
        t = set_tag(t, tag, thr)
    t = set_tag(t, "UseFixedLTZThreshold", "1")
    t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0")
    path.write_text(t, encoding="utf-8")


def run_nm(ini: Path, tsec: float, log: Path) -> int:
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tsec), "-x"]
    with log.open("w") as f:
        return subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)


def soma_from_csv(csv_path: Path) -> list[float]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    out = []
    for r in rows:
        try:
            out.append(float(r.get("soma_amp_sum") or 0))
        except ValueError:
            out.append(0.0)
    return out


def mid_thr(somas: list[float]) -> tuple[float, float]:
    tgt = somas[0]
    below = [s for s in somas[1:] if s < tgt]
    foil = max(below) if below else max(somas[1:] or [0.0])
    gap = tgt - foil
    mid = 0.5 * (tgt + foil) if below else tgt * 0.99
    return mid, gap


def resolve_tipr(mode: str, tipr_src: Path) -> str:
    if mode == "rmin":
        return TIPRMIN
    raw = get_tag(tipr_src.read_text(encoding="utf-8"), "TipSynapseResistance")
    if not raw:
        raise SystemExit(f"no TipSynapseResistance in {tipr_src}")
    done = normalize_tipr(raw)
    if mode == "done":
        return done
    if mode == "partial":
        parts = done.split()
        return f"20000000 20000000 20000000 {parts[3]}"
    raise SystemExit(f"unknown tipr-mode {mode}")


def apply_tipr(root: Path, tipr: str, tips: list[int]) -> None:
    vals = tipr.split()
    for phase in ("Train", "Test"):
        for rel in ("Parameters_00.xml", "Model_00.xml"):
            p = root / phase / rel
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8")
            t = set_tag(t, "TipSynapseResistance", tipr)
            t = set_tag(t, "ResistanceMin", RMIN)
            if rel.endswith("Model_00.xml"):
                t = patch_tip_exc_r(t, tips, vals)
            p.write_text(t, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_root", type=Path)
    ap.add_argument("--tipr-mode", choices=("rmin", "done", "partial"), required=True)
    ap.add_argument("--tipr-src", type=Path, default=DEFAULT_TIPR_SRC)
    ap.add_argument("--test-t", type=float, default=40.0)
    ap.add_argument("--tips", default="97 50 25 1", help="DendriteLength tips for Exc R")
    args = ap.parse_args()

    root = args.exp_root.resolve()
    test = root / "Test"
    tips = [int(x) for x in args.tips.split()]
    tipr = resolve_tipr(args.tipr_mode, args.tipr_src.resolve())
    print("tipr-mode", args.tipr_mode, "TipR", tipr)
    apply_tipr(root, tipr, tips)

    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        set_fixed_thr(p, SILENT_THR)

    csv_path = test / "SelectivityLog" / "results.csv"
    rc = run_nm(test / "Project.ini", args.test_t, test / "run_silent_probe.log")
    print("silent rc", rc)
    if not csv_path.exists():
        raise SystemExit("no silent results.csv")
    archived = test / "SelectivityLog" / "results_silent_thr1.csv"
    shutil.copy2(csv_path, archived)
    somas = soma_from_csv(archived)
    print("somas", somas)
    mid, gap = mid_thr(somas[:8] if len(somas) >= 8 else somas)
    print("mid", mid, "gap", gap)
    if gap <= 0:
        print("FAIL_GAP")
        raise SystemExit(2)

    mid_s = f"{mid:.12g}"
    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        set_fixed_thr(p, mid_s)
    rc = run_nm(test / "Project.ini", args.test_t, test / "run_gate.log")
    print("gate rc", rc)
    subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_path)])
    print("thr", mid_s)


if __name__ == "__main__":
    main()
