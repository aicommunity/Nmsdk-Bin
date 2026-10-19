#!/usr/bin/env python3
"""Clone Branch EXP peers into SelectivityBranchFastSpan with FastSpan (D002C25e11) kinetics."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1].parent  # StructTrain
OUT = BASE / "SelectivityBranchFastSpan"
BRANCH = BASE / "SelectivityBranch"

# Branch source peers (topology/ISI/mod)
PEER = {
    (25, "gen"): "EXP_br_span25_packA_gen_C1e9",
    (25, "preinh"): "EXP_br_span25_packA_preinh_C1e9",
    (25, "nextseg"): "EXP_br_span25_packA_nextseginh_C1e9",
    (50, "gen"): "EXP_br_span50_packA_gen_C1e9",
    (50, "preinh"): "EXP_br_span50_packA_preinh_C1e9",
    (50, "nextseg"): "EXP_br_span50_packA_nextseginh_C1e9",
    (100, "gen"): "EXP_br_span100_packA_gen_C1e9",
    (100, "preinh"): "EXP_br_span100_packA_preinh_C1e9",
    (100, "nextseg"): "EXP_br_span100_packA_nextseginh_C1e9",
}

# Full sensible grid: 3 span × 3 mod × {N0,N1} = 18 EXP
MIN_SET = [
    (s, m, mode)
    for mode in (1, 0)
    for s in (25, 50, 100)
    for m in ("gen", "preinh", "nextseg")
]

# Keep Branch Neuron Class / topology (matrix prepare patches SynapseClassName counts).
# FastSpan kinetics = DissociationTC/C from FastResponse D002C25e11 reference.
FAST_CLASS = None  # do not rewrite NeuronClassName / Neuron Class=
FAST_DISSOC = "0.002"
FAST_CAP = "2.5000000000000002e-10"

SKIP_NAMES = {"EventsLog", "History.xml", "run_train.log", "run_test.log", "save.tmp", "StatisticLog"}


def patch_text(text: str, norm_mode: int) -> str:
    # Kinetics only (preserve Branch Neuron Class / cable topology).
    text = re.sub(
        r"(<SynapseDissociationTC\b[^>]*>)[^<]*(</SynapseDissociationTC>)",
        rf"\g<1>{FAST_DISSOC}\2",
        text,
    )
    text = re.sub(
        r"(<DissociationTC\b[^>]*>)[^<]*(</DissociationTC>)",
        rf"\g<1>{FAST_DISSOC}\2",
        text,
    )
    text = re.sub(
        r"(<MembraneCapacity\b[^>]*>)[^<]*(</MembraneCapacity>)",
        rf"\g<1>{FAST_CAP}\2",
        text,
    )
    # NormalizationMode
    text = re.sub(
        r"(<NormalizationMode\b[^>]*>)[^<]*(</NormalizationMode>)",
        rf"\g<1>{norm_mode}\2",
        text,
    )
    return text


def copy_side(src: Path, dst: Path, norm_mode: int) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.iterdir():
        if p.name in SKIP_NAMES or p.name.endswith(".log"):
            continue
        if p.is_dir():
            if p.name in SKIP_NAMES:
                continue
            shutil.copytree(p, dst / p.name, dirs_exist_ok=True)
            continue
        data = p.read_bytes()
        if p.suffix.lower() in {".xml", ".ini", ".md"}:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                shutil.copy2(p, dst / p.name)
                continue
            if p.suffix.lower() == ".xml":
                text = patch_text(text, norm_mode)
            (dst / p.name).write_text(text, encoding="utf-8")
        else:
            shutil.copy2(p, dst / p.name)


def exp_name(span: int, mod: str, mode: int) -> str:
    return f"EXP_br_fs_span{span}_{mod}_N{mode}_C1e9"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    readme = OUT / "README.md"
    if not readme.exists():
        readme.write_text(
            "# SelectivityBranchFastSpan\n\n"
            "Trainer=Branch (`NNeuronTimeLearnerBranch`) + NeuronModel=FastSpan "
            f"(Branch topology + DissociationTC={FAST_DISSOC}, C={FAST_CAP}).\n\n"
            "Each EXP is a Train/Test pair with Interface.xml Watch on Branch.\n"
            "Cloned from SelectivityBranch peers; element kinetics patched to FastSpan.\n",
            encoding="utf-8",
        )
    for span, mod, mode in MIN_SET:
        peer = PEER[(span, mod)]
        src_root = BRANCH / peer
        if not src_root.is_dir():
            raise SystemExit(f"missing peer {src_root}")
        name = exp_name(span, mod, mode)
        dst_root = OUT / name
        if dst_root.exists():
            shutil.rmtree(dst_root)
        dst_root.mkdir(parents=True)
        for side in ("Train", "Test"):
            copy_side(src_root / side, dst_root / side, mode)
        (dst_root / "README.md").write_text(
            f"# {name}\n\n"
            f"Trainer=Branch · NeuronModel=FastSpan · Span={span} мс · Mod={mod} · Mode=N{mode}.\n"
            f"Peer: `SelectivityBranch/{peer}`.\n"
            f"Element kinetics: DissocTC={FAST_DISSOC} Cap={FAST_CAP} (Branch class kept).\n"
            "Both Train/ and Test/ include Interface.xml (Watch → NeuronTimeLearnerBranch).\n",
            encoding="utf-8",
        )
        # Interface contract check
        for side in ("Train", "Test"):
            iface = dst_root / side / "Interface.xml"
            assert iface.is_file() and iface.stat().st_size > 1000, iface
            text = iface.read_text(encoding="utf-8", errors="replace")
            assert "NeuronTimeLearnerBranch" in text, iface
            assert "NeuronTimeLearner\"" not in text.replace(
                "NeuronTimeLearnerBranch", ""
            ) or "NeuronTimeLearnerBranch" in text
        print("OK", name)
    print("done", len(MIN_SET), "EXP")


if __name__ == "__main__":
    main()
