#!/usr/bin/env python3
"""Extract first-spike lag: AxoneUnderTest.Output vs PGenerator.Output."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def load_series(path: Path) -> tuple[list[float], list[float]]:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return [], []
    times: list[float] = []
    vals: list[float] = []
    for i, ln in enumerate(text.splitlines()):
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        if re.search(r"[A-Za-z_]", ln) and i == 0:
            continue
        parts = [p for p in re.split(r"[,;\s]+", ln.strip()) if p]
        try:
            nums = [float(p.replace(",", ".")) for p in parts]
        except ValueError:
            continue
        if len(nums) == 1:
            times.append(float(i))
            vals.append(nums[0])
        else:
            times.append(nums[0])
            vals.append(nums[-1])
    return times, vals


def spike_starts(times: list[float], vals: list[float], thr: float = 0.5) -> list[float]:
    out: list[float] = []
    for i, v in enumerate(vals):
        if v > thr and (i == 0 or vals[i - 1] <= thr):
            out.append(times[i])
    return out


def find_trace(cell: Path, name: str) -> Path | None:
    slog = cell / "StatisticLog"
    if not slog.is_dir():
        return None
    direct = slog / name
    if direct.is_file():
        return direct
    cands = sorted(slog.rglob(name), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def analyze_cell(cell: Path) -> dict:
    row: dict = {"cell": cell.name, "ok": 0, "error": ""}
    gen_p = find_trace(cell, "PGenerator.Output.txt")
    ax_p = find_trace(cell, "AxoneUnderTest.Output.txt")
    if not gen_p:
        row["error"] = "missing_gen_trace"
        return row
    if not ax_p:
        row["error"] = "missing_axon_trace"
        return row
    gt, gv = load_series(gen_p)
    at, av = load_series(ax_p)
    gs = spike_starts(gt, gv)
    axs = spike_starts(at, av)
    row["n_spikes_gen"] = len(gs)
    row["n_spikes_axon"] = len(axs)
    if not gs:
        row["error"] = "no_spikes_gen"
        return row
    if not axs:
        row["error"] = "no_spikes_axon"
        return row
    lag = axs[0] - gs[0]
    row.update(
        {
            "t_gen0": gs[0],
            "t_axon0": axs[0],
            "lag_s": lag,
            "lag_ms": lag * 1000.0,
            "ok": 1,
            "error": "",
        }
    )
    return row


def load_grid(path: Path) -> dict[str, dict]:
    by_cell: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            by_cell[r["cell"]] = r
    return by_cell


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cell", nargs="?", type=Path)
    ap.add_argument("--batch", type=Path)
    ap.add_argument("--grid", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    fields = [
        "cell",
        "model",
        "class",
        "length_param",
        "length_value",
        "lag_s",
        "lag_ms",
        "t_gen0",
        "t_axon0",
        "n_spikes_gen",
        "n_spikes_axon",
        "ok",
        "error",
    ]

    if args.batch:
        grid = load_grid(args.grid) if args.grid else {}
        cells = sorted([p for p in args.batch.iterdir() if p.is_dir() and (p / "project.ini").is_file()])
        rows = []
        for c in cells:
            r = analyze_cell(c)
            g = grid.get(c.name, {})
            r["model"] = g.get("model", "")
            r["class"] = g.get("class", "")
            r["length_param"] = g.get("length_param", "")
            r["length_value"] = g.get("length_value", "")
            rows.append(r)
            print(f"{c.name}: ok={r.get('ok')} lag_ms={r.get('lag_ms', '')} err={r.get('error','')}")
        out = args.out or (args.batch.parent / "metrics.csv")
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"wrote {out} ({len(rows)} rows)")
        return

    if not args.cell:
        raise SystemExit("need cell or --batch")
    r = analyze_cell(args.cell)
    print(r)


if __name__ == "__main__":
    main()
