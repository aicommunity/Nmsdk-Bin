#!/usr/bin/env python3
"""Build SoftCold FULL49 SNAP markdown from RCS + latest run provenance/tipr."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RCS = ROOT / "_repro" / "SOFTCOLD_HEAD_rcs.txt"
RUNS = ROOT / "_repro" / "runs"
OUT = Path(
    "/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/"
    "SOFTCOLD_FULL49_SNAP.md"
)

# Fallbacks only when audit/provenance lack bounds (legacy bundles).
DEFAULT_RMIN = 1.0e4
DEFAULT_RMAX = 1.0e10


def parse_rcs() -> list[tuple[str, int, str]]:
    rows = []
    for line in RCS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        rows.append((parts[0], int(parts[1]), parts[2] if len(parts) > 2 else ""))
    return rows


def latest_run(case: str) -> Path | None:
    """Prefer finalized bundle (tipr_final) over live *_work."""
    cands = [p for p in RUNS.glob(f"{case}_*") if p.is_dir()]
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in cands:
        if p.name.endswith("_work"):
            continue
        if (p / "Train" / "tipr_final.txt").exists():
            return p
    for p in cands:
        if (p / "Train" / "Parameters_00.xml").exists() or (p / "provenance.json").exists():
            return p
    return None


def _float_field(fields: dict[str, str], *keys: str) -> float | None:
    for k in keys:
        if k not in fields:
            continue
        try:
            v = float(fields[k])
            if v > 0.0:
                return v
        except ValueError:
            continue
    return None


def bounds_from_run(run: Path | None) -> tuple[float, float]:
    """Derive TipR bucket bounds from C++ audit / provenance (Rs/Rm derived)."""
    rmin, rmax = DEFAULT_RMIN, DEFAULT_RMAX
    if run is None:
        return rmin, rmax
    prov = run / "provenance.json"
    if prov.exists():
        try:
            data = json.loads(prov.read_text(encoding="utf-8"))
            for key, slot in (("rmin", "min"), ("resistance_min", "min"),
                              ("rmax", "max"), ("resistance_max", "max")):
                if key in data:
                    try:
                        v = float(data[key])
                        if v > 0:
                            if slot == "min":
                                rmin = v
                            else:
                                rmax = v
                    except (TypeError, ValueError):
                        pass
        except json.JSONDecodeError:
            pass
    audit = run / "Train" / "TimeLearnerTrainingAudit.log"
    if not audit.exists():
        audit = run / "Train" / "StatisticLog" / "TimeLearnerTrainingAudit.log"
    if audit.exists():
        try:
            text = audit.read_text(encoding="utf-8", errors="replace")
            # Prefer last reset line, else any iteration with rmin/rmax
            for line in reversed(text.splitlines()):
                if "rmin=" not in line and "rmax=" not in line:
                    continue
                fields = dict(
                    item.split("=", 1) for item in line.strip().split(";") if "=" in item
                )
                rm = _float_field(fields, "rmin", "resistance_min")
                rx = _float_field(fields, "rmax", "resistance_max")
                if rm is not None:
                    rmin = rm
                if rx is not None:
                    rmax = rx
                if "kind=reset" in line or (rm is not None and rx is not None):
                    break
        except OSError:
            pass
    return rmin, rmax


def tipr_bucket(
    case: str,
    tipr: str,
    failure_class: str,
    rc: int,
    *,
    rmin: float,
    rmax: float,
) -> str:
    if rc == 0:
        return "PASS"
    if case in ("br100_keep", "br100_search"):
        return "G"
    if case == "br25_on":
        return "N"
    if "cpp_training_failure" in failure_class or failure_class in (
        "resistance_max",
        "train_failed_rmax",
    ):
        return "D"
    nums = []
    for tok in tipr.replace(",", " ").replace("e07", "e7").split():
        try:
            nums.append(float(tok))
        except ValueError:
            pass
    active = nums[:3] if nums else []
    if case.endswith("_nextseg") and active and all(abs(x - 8.6e7) / 8.6e7 < 0.08 for x in active):
        return "A"
    if not active:
        return "D_unclassified"
    mx = max(active)
    mn = min(active)
    if rmax > 0 and mx >= 0.9 * rmax:
        return "D"
    if rmin > 0 and all(abs(x - rmin) / max(rmin, 1.0) < 0.08 for x in active):
        return "E"
    if all(abs(x - 8.6e7) / 8.6e7 < 0.08 for x in active):
        return "A"
    if case.startswith("br480") or case == "br25_preinh":
        return "B"
    if rmin > 0 and rmax > 0 and mn > rmin * 1.2 and mx < 0.5 * rmax:
        return "B"
    if rmin > 0 and rmax > 0 and mx > rmin * 3 and mx < 0.9 * rmax:
        return "B"
    return "other"


def main() -> None:
    console = "?"
    pulselib = "?"
    parallel = "?"
    for arg in sys.argv[1:]:
        if arg.startswith("--console="):
            console = arg.split("=", 1)[1]
        elif arg.startswith("--pulselib="):
            pulselib = arg.split("=", 1)[1]
        elif arg.startswith("--parallel="):
            parallel = arg.split("=", 1)[1]
    rows = parse_rcs()
    lines = [
        "# SoftCold FULL49 SNAP (Rs/Rm · W3 off)",
        "",
        f"Срез: Console `{console}` · PulseLib `{pulselib}` · PARALLEL={parallel} · "
        "RCS [`SOFTCOLD_HEAD_rcs.txt`](../../../Bin/Configs/SpikeSamples/StructTrain/_repro/SOFTCOLD_HEAD_rcs.txt). "
        "W3 (`EnableRmaxLengthEscape`) **off**; TipR buckets use per-run derived rmin/rmax.",
        "",
        "| case | rc | tipr_class | failure_class | Need | TipR | L | rmin | rmax | bucket |",
        "|------|----|------------|---------------|------|------|---|------|------|--------|",
    ]
    counts: dict[str, int] = {}
    for case, rc, _utc in rows:
        run = latest_run(case)
        tipr = need = L = tipr_class = failure_class = "?"
        rmin, rmax = bounds_from_run(run)
        if run:
            prov = run / "provenance.json"
            if prov.exists():
                try:
                    data = json.loads(prov.read_text(encoding="utf-8"))
                    tipr_class = str(data.get("tipr_class") or "?")
                    failure_class = str(data.get("failure_class") or "?")
                    ts = str(data.get("train_status") or "")
                    if "cpp_training_failure" in ts and failure_class == "?":
                        failure_class = ts
                except json.JSONDecodeError:
                    pass
            tipr_path = run / "Train" / "tipr_final.txt"
            if tipr_path.exists():
                tipr = " ".join(tipr_path.read_text(encoding="utf-8").split()[:4])
            live = run / "Train" / "posttune_tipr_live.txt"
            if live.exists():
                text = live.read_text(encoding="utf-8")
                m = re.search(r"tipr=([^\n]+)", text)
                if m and tipr == "?":
                    tipr = " ".join(m.group(1).split()[:4])
                m = re.search(r"\bneed=(\S+)", text)
                if m:
                    need = m.group(1)
                m = re.search(r"\bL=([^\n]+)", text)
                if m:
                    L = " ".join(m.group(1).split()[:4])
            params = run / "Train" / "Parameters_00.xml"
            if params.exists():
                pt = params.read_text(encoding="utf-8", errors="replace")
                if need == "?":
                    m = re.search(r"<IsNeedToTrain>([^<]+)", pt)
                    if m:
                        need = m.group(1).strip()
                if tipr == "?":
                    m = re.search(r"<TipSynapseResistance>([^<]+)", pt)
                    if m:
                        tipr = " ".join(m.group(1).replace(",", " ").split()[:4])
                if L == "?":
                    m = re.search(r"<DendriteLength>([^<]+)", pt)
                    if m:
                        L = " ".join(m.group(1).replace(",", " ").split()[:4])
        bucket = tipr_bucket(
            case, tipr, failure_class, rc, rmin=rmin, rmax=rmax
        )
        counts[bucket] = counts.get(bucket, 0) + 1
        tipr_s = tipr.replace("|", " ")
        L_s = L.replace("|", " ")
        lines.append(
            f"| `{case}` | {rc} | {tipr_class} | {failure_class} | {need} | "
            f"`{tipr_s}` | `{L_s}` | {rmin:g} | {rmax:g} | **{bucket}** |"
        )
    lines.extend(["", "## Counts", ""])
    for k in sorted(counts):
        lines.append(f"- **{k}**: {counts[k]}")
    lines.append("")
    lines.append(
        f"PASS+FAIL check: {sum(1 for _, rc, _ in rows if rc == 0)} PASS / "
        f"{sum(1 for _, rc, _ in rows if rc != 0)} FAIL / {len(rows)} total."
    )
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} rows={len(rows)} counts={counts}")


if __name__ == "__main__":
    main()
