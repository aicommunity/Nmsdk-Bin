#!/usr/bin/env python3
"""Thin wrapper → StructTrain/scripts/selectivity_metrics.py (legacy line + --verbose)."""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from selectivity_metrics import main

if __name__ == "__main__":
    main()
