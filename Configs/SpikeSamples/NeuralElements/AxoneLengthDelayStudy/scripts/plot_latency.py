#!/usr/bin/env python3
"""Plot lag vs length for delay / chain / cad families."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def load_metrics(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x: str) -> float:
    return float(x)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    rows = [r for r in load_metrics(args.metrics) if r.get("ok") == "1"]

    # delay
    d = sorted(
        [r for r in rows if r.get("model") == "delay"],
        key=lambda r: fnum(r["length_value"]),
    )
    if d:
        xs = [fnum(r["length_value"]) * 1000.0 for r in d]
        ys = [fnum(r["lag_ms"]) for r in d]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(xs, ys, "o-", label="measured lag")
        ax.plot(xs, xs, "k--", alpha=0.5, label="y = DelayTime")
        ax.set_xlabel("DelayTime [ms]")
        ax.set_ylabel("first-spike lag [ms]")
        ax.set_title("NAxoneDelay: lag vs DelayTime")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.outdir / "delay_vs_DelayTime.png", dpi=120)
        plt.close(fig)

    # chain
    ch = sorted(
        [r for r in rows if r.get("model") == "chain"],
        key=lambda r: fnum(r["length_value"]),
    )
    if ch:
        xs = [fnum(r["length_value"]) for r in ch]
        ys = [fnum(r["lag_ms"]) for r in ch]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(xs, ys, "o-", label="measured lag")
        if len(xs) >= 2:
            # simple linear fit
            n = len(xs)
            mx = sum(xs) / n
            my = sum(ys) / n
            den = sum((x - mx) ** 2 for x in xs) or 1.0
            slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
            intercept = my - slope * mx
            fit_y = [slope * x + intercept for x in xs]
            ax.plot(xs, fit_y, "--", alpha=0.7, label=f"fit: {slope:.2f}*N+{intercept:.2f}")
        ax.set_xlabel("NumSegments")
        ax.set_ylabel("first-spike lag [ms]")
        ax.set_title("NAxoneChain: lag vs NumSegments")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.outdir / "delay_vs_NumSegments.png", dpi=120)
        plt.close(fig)

    # cad
    cad = sorted(
        [r for r in rows if r.get("model") == "cad"],
        key=lambda r: fnum(r["length_value"]),
    )
    if cad:
        xs = [fnum(r["length_value"]) for r in cad]
        ys = [fnum(r["lag_ms"]) for r in cad]
        buf = [(n - 1) * 2.0 for n in xs]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(xs, ys, "o-", label="measured lag")
        ax.plot(xs, buf, "s--", alpha=0.6, label="(N-1)*InternodeDelay 2ms")
        ax.set_xlabel("NumNodes")
        ax.set_ylabel("first-spike lag [ms]")
        ax.set_title("NAxoneChainAndDelay: lag vs NumNodes")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.outdir / "delay_vs_NumNodes.png", dpi=120)
        plt.close(fig)

    print(f"plots in {args.outdir}")


if __name__ == "__main__":
    main()
