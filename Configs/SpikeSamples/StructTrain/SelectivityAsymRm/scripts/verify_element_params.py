#!/usr/bin/env python3
"""Verify DissociationTC / Capacity / Rm / Rsyn / Secr / InhibitionCoeff in a Model_00.xml."""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def floats(tag: str, text: str) -> list[float]:
    return [float(m) for m in re.findall(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)]


def near(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= max(tol, abs(b) * 1e-9)


def channel_resistances(text: str, channel: str) -> list[float]:
    """Resistance values inside ExcChannel / InhChannel blocks (not FBResistance)."""
    vals: list[float] = []
    for m in re.finditer(
        rf"<{channel}\b[^>]*>.*?</{channel}>", text, flags=re.DOTALL
    ):
        block = m.group(0)
        for rm in re.finditer(r"<Resistance\b[^>]*>([^<]*)</Resistance>", block):
            # Skip FBResistance sibling already excluded by tag name
            vals.append(float(rm.group(1)))
    return vals


def synapse_resistances(text: str, prefix: str) -> list[float]:
    vals: list[float] = []
    for m in re.finditer(
        rf"<{prefix}\d*\b[^>]*>.*?</{prefix}\d*>", text, flags=re.DOTALL
    ):
        # Fallback: ExcSynapse1 style tags
        pass
    for m in re.finditer(
        rf"<(ExcSynapse\d+|InhSynapse\d+)\b[^>]*>.*?</\1>", text, flags=re.DOTALL
    ):
        name = m.group(1)
        if not name.startswith(prefix):
            continue
        block = m.group(0)
        for rm in re.finditer(r"<Resistance\b[^>]*>([^<]*)</Resistance>", block):
            vals.append(float(rm.group(1)))
    return vals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", type=Path)
    ap.add_argument("--expect-dissoc", type=float, required=True)
    ap.add_argument("--expect-cap", type=float, required=True)
    ap.add_argument("--expect-inh", type=float, default=None)
    ap.add_argument("--no-inh", action="store_true", help="require no InhibitionCoeff=2.5")
    ap.add_argument("--expect-class", type=str, default="")
    ap.add_argument("--min-count", type=int, default=4)
    ap.add_argument("--forbid-bio", action="store_true", default=True)
    ap.add_argument("--expect-exc-r", type=float, default=None)
    ap.add_argument("--expect-inh-r", type=float, default=None)
    ap.add_argument("--expect-exc-syn-r", type=float, default=None)
    ap.add_argument("--expect-inh-syn-r", type=float, default=None)
    ap.add_argument("--expect-secr", type=float, default=None)
    args = ap.parse_args()

    if not args.model.exists():
        print(f"FAIL missing {args.model}", file=sys.stderr)
        return 1

    text = args.model.read_text(encoding="utf-8", errors="replace")
    errs: list[str] = []

    if args.expect_class:
        classes = re.findall(r'<Neuron Class="([^"]+)"', text)
        if not classes or classes[0] != args.expect_class:
            errs.append(f"Neuron Class={classes[:1]} expected {args.expect_class}")

    dissocs = floats("DissociationTC", text)
    caps = floats("Capacity", text)
    if len(dissocs) < args.min_count:
        errs.append(f"DissociationTC count {len(dissocs)} < {args.min_count}")
    if len(caps) < args.min_count:
        errs.append(f"Capacity count {len(caps)} < {args.min_count}")

    bad_d = [v for v in dissocs if not near(v, args.expect_dissoc)]
    bad_c = [v for v in caps if not near(v, args.expect_cap)]
    if bad_d:
        errs.append(
            f"DissociationTC unexpected {Counter(round(x, 12) for x in bad_d)} "
            f"(want {args.expect_dissoc}; all={Counter(round(x, 12) for x in dissocs)})"
        )
    if bad_c:
        errs.append(
            f"Capacity unexpected {Counter(round(x, 12) for x in bad_c)} "
            f"(want {args.expect_cap}; all={Counter(round(x, 12) for x in caps)})"
        )

    if args.forbid_bio:
        if any(near(v, 0.005) for v in dissocs) and not near(args.expect_dissoc, 0.005):
            errs.append("found Bio DissociationTC=0.005")
        if any(near(v, 1e-9) for v in caps) and not near(args.expect_cap, 1e-9):
            errs.append("found Bio Capacity=1e-9")

    inhs = floats("InhibitionCoeff", text)
    if args.expect_inh is not None:
        if not any(near(v, args.expect_inh) for v in inhs):
            errs.append(f"missing InhibitionCoeff={args.expect_inh} (have {Counter(inhs)})")
    if args.no_inh:
        if any(near(v, 2.5) for v in inhs):
            errs.append(f"unexpected InhibitionCoeff=2.5 (have {Counter(inhs)})")

    if args.expect_secr is not None:
        secrs = floats("SecretionTC", text)
        if len(secrs) < args.min_count:
            errs.append(f"SecretionTC count {len(secrs)} < {args.min_count}")
        bad_s = [v for v in secrs if not near(v, args.expect_secr)]
        if bad_s:
            errs.append(
                f"SecretionTC unexpected {Counter(round(x, 12) for x in bad_s)} "
                f"(want {args.expect_secr})"
            )

    if args.expect_exc_r is not None:
        exc_r = channel_resistances(text, "ExcChannel")
        if not exc_r:
            errs.append("no ExcChannel Resistance found")
        else:
            bad = [v for v in exc_r if not near(v, args.expect_exc_r)]
            if bad:
                errs.append(
                    f"ExcChannel Resistance unexpected {Counter(round(x, 3) for x in bad)} "
                    f"(want {args.expect_exc_r})"
                )

    if args.expect_inh_r is not None:
        inh_r = channel_resistances(text, "InhChannel")
        if not inh_r:
            errs.append("no InhChannel Resistance found")
        else:
            bad = [v for v in inh_r if not near(v, args.expect_inh_r)]
            if bad:
                errs.append(
                    f"InhChannel Resistance unexpected {Counter(round(x, 3) for x in bad)} "
                    f"(want {args.expect_inh_r})"
                )

    if args.expect_exc_syn_r is not None:
        syn_r = synapse_resistances(text, "ExcSynapse")
        if not syn_r:
            errs.append("no ExcSynapse Resistance found")
        else:
            bad = [v for v in syn_r if not near(v, args.expect_exc_syn_r)]
            if bad:
                errs.append(
                    f"ExcSynapse Resistance unexpected {Counter(round(x, 3) for x in bad)} "
                    f"(want {args.expect_exc_syn_r})"
                )

    if args.expect_inh_syn_r is not None:
        syn_r = synapse_resistances(text, "InhSynapse")
        if not syn_r:
            errs.append("no InhSynapse Resistance found")
        else:
            bad = [v for v in syn_r if not near(v, args.expect_inh_syn_r)]
            if bad:
                errs.append(
                    f"InhSynapse Resistance unexpected {Counter(round(x, 3) for x in bad)} "
                    f"(want {args.expect_inh_syn_r})"
                )

    if errs:
        print(f"FAIL {args.model}:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    extras = []
    if args.expect_exc_r is not None:
        extras.append(f"ExcR={args.expect_exc_r}")
    if args.expect_inh_r is not None:
        extras.append(f"InhR={args.expect_inh_r}")
    if args.expect_secr is not None:
        extras.append(f"Secr={args.expect_secr}")
    print(
        f"OK {args.model.name}: Dissoc×{len(dissocs)}={args.expect_dissoc} "
        f"Cap×{len(caps)}={args.expect_cap}"
        + (f" Inh={args.expect_inh}" if args.expect_inh is not None else "")
        + ((" " + " ".join(extras)) if extras else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
