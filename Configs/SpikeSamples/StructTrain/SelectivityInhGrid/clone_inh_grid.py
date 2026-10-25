#!/usr/bin/env python3
"""Clone Classic/Branch EXP grid for PSI × NextSeg × SegEI campaign.

Writes SelectivityInhGrid/EXP_* and INH_EXP_MANIFEST.json (consumed by posttune_verify).
Does not overwrite HIST templates under SelectivityAsymRm / SelectivityBranch.

PLAN 2026-10-25 §0 F1/F2:
  - Base neuron = HIST AsymRm (not SymInh).
  - PSI only via neuron class (Preinh2_5AsymRm…); never Model UsePresynaptic patches.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ST = ROOT.parent
CLASSIC_SRC = {
    25: ST / "SelectivityAsymRm" / "EXP_span25ms_packA_gen",
    50: ST / "SelectivityAsymRm" / "EXP_span50ms_packA_gen",
    100: ST / "SelectivityAsymRm" / "EXP_span100ms_packA_gen",
}
BRANCH_SRC = {
    25: ST / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9",
    50: ST / "SelectivityBranch" / "EXP_br_span50_packA_gen_C1e9",
    100: ST / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9",
}

MODS = {
    "gen": dict(psi=False, nextseg=False, segei=False),
    "preinh": dict(psi=True, nextseg=False, segei=False),
    "nextseg": dict(psi=False, nextseg=True, segei=False),
    "segei": dict(psi=False, nextseg=False, segei=True),
    "preinh_nextseg": dict(psi=True, nextseg=True, segei=False),
    "preinh_segei": dict(psi=True, nextseg=False, segei=True),
    "nextseg_segei": dict(psi=False, nextseg=True, segei=True),
    "all": dict(psi=True, nextseg=True, segei=True),
}

# F1: HIST AsymRm base. F2: PSI = dedicated Preinh neuron class (membrane NPMembraneBioPreinh*).
NEURON_BASE = "NSPNeuronGenAsymRmD001C1e9"
NEURON_PSI = "NSPNeuronGenPreinh2_5AsymRmD001C1e9"
SEG_D = 8
SEG_A = 1.0


def neuron_for(flags: dict) -> str:
    return NEURON_PSI if flags.get("psi") else NEURON_BASE


def _set_tag(text: str, name: str, value: str, typ: str) -> str:
    pat = rf"(<{name}\s+Type=\"{re.escape(typ)}\"[^>]*>)([^<]*)(</{name}>)"
    if re.search(pat, text):
        return re.sub(pat, rf"\g<1>{value}\g<3>", text, count=1)
    inj = (
        f'\t\t\t\t\t<{name} Type="{typ}" PType="257" IoType="17">{value}</{name}>\n'
    )
    if "<NeuronClassName " in text:
        return re.sub(
            r"(<NeuronClassName\s+Type=\"std::string\"[^>]*>[^<]*</NeuronClassName>\n)",
            rf"\1{inj}",
            text,
            count=1,
        )
    return text + inj


def _patch_parameters(
    path: Path, *, mode: int, flags: dict, neuron: str, classic: bool
) -> None:
    del classic  # reserved; Classic/Branch share Parameter flag set
    t = path.read_text(encoding="utf-8", errors="replace")
    t = _set_tag(t, "NeuronClassName", neuron, "std::string")
    t = _set_tag(t, "NormalizationMode", str(mode), "i")
    t = _set_tag(t, "EnableNextSegmentInhibition", "1" if flags["nextseg"] else "0", "b")
    t = _set_tag(t, "EnableSegExcInh", "1" if flags["segei"] else "0", "b")
    t = _set_tag(t, "SegExcInhDelta", str(SEG_D), "i")
    t = _set_tag(t, "SegExcInhAlpha", str(SEG_A), "d")
    # F2: do not write UsePresynapticInhibition / InhibitionCoeff here — BuildStructure
    # rebuilds synapses from NeuronClassName / MembraneClassName.
    path.write_text(t, encoding="utf-8")


def _patch_model_neuron_class(path: Path, neuron: str) -> None:
    """Only NeuronClassName — never PSI synapse flags (F2)."""
    if not path.is_file():
        return
    t = path.read_text(encoding="utf-8", errors="replace")
    t = re.sub(
        r"(<NeuronClassName\s+Type=\"std::string\"[^>]*>)([^<]*)(</NeuronClassName>)",
        rf"\g<1>{neuron}\g<3>",
        t,
    )
    path.write_text(t, encoding="utf-8")


def clone_one(src: Path, dst: Path, *, mode: int, flags: dict, classic: bool) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(
            "*.log",
            "EventsLog",
            "StatisticLog",
            "SelectivityLog",
            "posttune_mid_dbg.txt",
            "History.xml",
            "save.tmp",
            "*.bak*",
            "*_posttune*",
        ),
    )
    neuron = neuron_for(flags)
    for side in ("Train", "Test"):
        p = dst / side / "Parameters_00.xml"
        if p.is_file():
            _patch_parameters(
                p, mode=mode, flags=flags, neuron=neuron, classic=classic
            )
        m = dst / side / "Model_00.xml"
        _patch_model_neuron_class(m, neuron)


def main() -> None:
    rows = []
    for span, src in CLASSIC_SRC.items():
        if not src.is_dir():
            raise SystemExit(f"missing classic src {src}")
        for mod, flags in MODS.items():
            for mode_name, mode_i in (("N0", 0), ("N1", 1)):
                exp = f"EXP_classic_S{span}_{mod}_InhGrid_{mode_name}"
                dst = ROOT / exp
                clone_one(src, dst, mode=mode_i, flags=flags, classic=True)
                rows.append(
                    {
                        "exp": exp,
                        "trainer": "Classic",
                        "span": span,
                        "mod": mod,
                        "mode": mode_name.lower(),
                        "neuron": neuron_for(flags),
                        "train": f"SelectivityInhGrid/{exp}/Train",
                        "test": f"SelectivityInhGrid/{exp}/Test",
                        "src": str(src.relative_to(ST)),
                    }
                )
    for span, src in BRANCH_SRC.items():
        if not src.is_dir():
            raise SystemExit(f"missing branch src {src}")
        for mod, flags in MODS.items():
            exp = f"EXP_branch_S{span}_{mod}_InhGrid_N1"
            dst = ROOT / exp
            clone_one(src, dst, mode=1, flags=flags, classic=False)
            rows.append(
                {
                    "exp": exp,
                    "trainer": "Branch",
                    "span": span,
                    "mod": mod,
                    "mode": "n1",
                    "neuron": neuron_for(flags),
                    "train": f"SelectivityInhGrid/{exp}/Train",
                    "test": f"SelectivityInhGrid/{exp}/Test",
                    "src": str(src.relative_to(ST)),
                }
            )
    man = ROOT / "INH_EXP_MANIFEST.json"
    man.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} EXPs + {man}")


if __name__ == "__main__":
    main()
