#!/usr/bin/env python3
"""Thin wrapper: delegate to StructTrain/scripts/selectivity_metrics.py."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2] / "scripts"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from selectivity_metrics import main  # noqa: E402

if __name__ == "__main__":
    main()
