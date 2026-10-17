#!/usr/bin/env python3
"""Clone dendrite-length classifier structures into a fixed LTZone threshold pool."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from prepare_burst_exclusion_replays import FIXED_REPLAY_SECONDS, clone_existing


HERE = Path(__file__).resolve().parent
REPRO = HERE.parent
CLEAN_SOURCE_ROOT = REPRO / "BurstReplayVerified_20260928"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=CLEAN_SOURCE_ROOT,
                        help="Directory with the six short/medium/long On/Off structures")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    args = parser.parse_args()

    threshold_label = f"{int(round(args.threshold * 10000)):05d}"
    source_dirs = sorted(args.source_root.glob("*D*_Threshold*_20260928"))
    source_dirs = [path for path in source_dirs if "short_" in path.name.lower()
                   or "medium_" in path.name.lower() or "long_" in path.name.lower()]
    if len(source_dirs) != 6:
        raise ValueError(f"Expected six short/medium/long On/Off structures under {args.source_root}, got {len(source_dirs)}")

    created = []
    for source in source_dirs:
        match = re.fullmatch(
            r"(?:NSpikeClassifier_Class2_(short|medium|long)|NSpikeDendriteLength_(Short|Medium|Long))_D(\d+)_(On|Off)_Threshold\d+_20260928",
            source.name,
        )
        if not match:
            raise ValueError(f"Unexpected dendrite variant name: {source.name}")
        length_label = (match.group(1) or match.group(2)).lower()
        dendrite_length, mode = match.group(3), match.group(4)
        name = (
            f"NSpikeDendriteLength_{length_label.title()}_D{dendrite_length}_"
            f"{mode}_Threshold{threshold_label}_20260928"
        )
        destination = args.output_root / name
        created.append(clone_existing(source, destination, args.threshold, FIXED_REPLAY_SECONDS))

    print("\n".join(str(path) for path in created))


if __name__ == "__main__":
    main()
