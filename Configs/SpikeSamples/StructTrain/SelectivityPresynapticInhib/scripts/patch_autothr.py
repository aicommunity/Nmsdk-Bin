#!/usr/bin/env python3
"""Enable AutoCalibrateFixedLTZThreshold on NeuronTimeLearner Parameters."""
import re
import sys
from pathlib import Path

TAGS = {
    "AutoCalibrateFixedLTZThreshold": "1",
    "CalibrateLTZThresholdMode": "0",
    "CalibrateLTZThresholdFraction": "0.85",
    "CalibrateLTZThresholdMin": "0.0115",
    "CalibrateLTZThresholdMax": "0.05",
}


def upsert_tag(text: str, name: str, value: str) -> str:
    pattern = rf'<{name} Type="[^"]*" PType="257" IoType="17">[^<]*</{name}>'
    replacement = f'<{name} Type="{"b" if name.startswith("Auto") else "d" if "Fraction" in name or "Min" in name or "Max" in name and "Calibrated" not in name else "i" if name.endswith("Mode") else "d"}" PType="257" IoType="17">{value}</{name}>'
    if name == "AutoCalibrateFixedLTZThreshold":
        replacement = f'<{name} Type="b" PType="257" IoType="17">{value}</{name}>'
    elif name == "CalibrateLTZThresholdMode":
        replacement = f'<{name} Type="i" PType="257" IoType="17">{value}</{name}>'
    else:
        replacement = f'<{name} Type="d" PType="257" IoType="17">{value}</{name}>'

    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    anchor = '<UseFixedLTZThreshold Type="b" PType="257" IoType="17">'
    if anchor not in text:
        raise SystemExit(f"anchor UseFixedLTZThreshold not found")
    return text.replace(anchor, replacement + "\n\t\t\t\t\t" + anchor, 1)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for name, value in TAGS.items():
        text = upsert_tag(text, name, value)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch(Path(sys.argv[1]))
