#!/usr/bin/env python3
"""PHASE8 post-train: rebuild Test hygiene, TipR@Rmin, silent mid thr, gate.

Critical hygiene (learned S1):
- Overlay Train <Neuron> tree into Test (template still has L=85 tips).
- Generator tip links must be Dendrite1_{L[i]} for Done lengths.
- TipR@Rmin via TipSynapseResistance + tip ExcSynapse1 Resistance (scoped).
- Parameters: Learner StructureBuildMode=0, MatrixData/Classes NumSamples=8 from AsymRm packA.
- Model: Learner SB=1, Neuron SB=2 (PHASE7 pattern); Model DatasetMatrix stays 1-sample.
- mid thr from soma_amp_sum (not ltz_potential_max).
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

NM = Path("/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
ROOT = Path("/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain")
SCRIPTS = ROOT / "SelectivityLtzCalibrate" / "scripts"
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
ASYM = ROOT / "SelectivityAsymRm"
TIPRMIN = "20000000 20000000 20000000 86000000"
RMIN = "20000000"
SILENT_THR = "1.0"


def set_tag(text: str, tag: str, value: str, count: int = 0) -> str:
    return re.sub(
        rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
        lambda m: m.group(1) + value + m.group(2),
        text,
        count=count or 0,
    )


def get_tag(text: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).strip() if m else None


def copy_tag(src: str, dst: str, tag: str) -> str:
    m = re.search(rf"(<{tag}\b[^>]*>.*?</{tag}>)", src, re.S)
    if not m:
        return dst
    if re.search(rf"<{tag}\b", dst):
        return re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", m.group(1), dst, count=1, flags=re.S)
    return dst


def read_lengths(params: Path) -> list[int]:
    raw = get_tag(params.read_text(encoding="utf-8"), "DendriteLength")
    if not raw:
        raise SystemExit(f"no DendriteLength in {params}")
    return [int(float(x)) for x in raw.replace(",", " ").split()]


def set_neuron_sb(text: str, learner_sb: str, neuron_sb: str) -> str:
    def repl_neuron(m: re.Match[str]) -> str:
        return re.sub(
            r'(<StructureBuildMode Type="i"[^>]*>)[^<]*(</StructureBuildMode>)',
            lambda mm: mm.group(1) + neuron_sb + mm.group(2),
            m.group(0),
            count=1,
        )

    text = re.sub(
        r'<Neuron Class="[^"]+">.*?</Neuron>', repl_neuron, text, count=1, flags=re.S
    )
    # Model XML often has no <NNeuronTimeLearnerBranch> element — set first SB before Neuron
    idx = text.find("<Neuron Class=")
    if idx < 0:
        return text
    head, tail = text[:idx], text[idx:]
    head = re.sub(
        r'(<StructureBuildMode Type="i"[^>]*>)[^<]*(</StructureBuildMode>)',
        lambda mm: mm.group(1) + learner_sb + mm.group(2),
        head,
        count=1,
    )
    return head + tail


def ensure_generator_tips(text: str, tips: list[int]) -> str:
    pat = re.compile(
        r'<elem Type="ULink">\s*'
        r'<Item Type="ULinkSide" Index="-1" Name="Output">'
        r"NeuronTimeLearnerBranch\.DatasetMatrix\.Generator1</Item>\s*"
        r"(?:<Connector Type=\"ULinkSide\" Index=\"-1\" Name=\"Input\">"
        r"NeuronTimeLearnerBranch\.Neuron\.Dendrite1_\d+\.ExcSynapse1</Connector>\s*)+"
        r"</elem>",
        re.S,
    )
    link = (
        '<elem Type="ULink">\n'
        '\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="Output">'
        "NeuronTimeLearnerBranch.DatasetMatrix.Generator1</Item>\n"
    )
    for L in tips:
        link += (
            '\t\t\t\t<Connector Type="ULinkSide" Index="-1" Name="Input">'
            f"NeuronTimeLearnerBranch.Neuron.Dendrite1_{L}.ExcSynapse1</Connector>\n"
        )
    link += "\t\t\t</elem>"
    if pat.search(text):
        return pat.sub(link, text, count=1)
    # insert after StimulusInputs analyzer link if present
    anchor = re.search(
        r'(<elem Type="ULink">\s*'
        r'<Item Type="ULinkSide" Index="-1" Name="Output">'
        r"NeuronTimeLearnerBranch\.DatasetMatrix\.Generator1</Item>\s*"
        r'<Connector Type="ULinkSide" Index="-1" Name="StimulusInputs">'
        r"PatternResponseAnalyzer</Connector>\s*</elem>)",
        text,
        re.S,
    )
    if anchor:
        text = text[: anchor.end()] + "\n\t\t\t" + link + text[anchor.end() :]
        n_elem = text.count('<elem Type="ULink">')
        text = re.sub(
            r'(<Links Type="ULinksList" Size=")\d+(">)',
            rf"\g<1>{n_elem}\2",
            text,
            count=1,
        )
        return text
    raise SystemExit("cannot place Generator tip links")


def patch_tip_exc_r(text: str, tips: list[int]) -> str:
    for i, L in enumerate(tips):
        r = "20000000" if i < 3 else "86000000"
        pat = re.compile(
            rf'(<Dendrite1_{L} Class="[^"]+">.*?<ExcSynapse1 Class="[^"]+">'
            rf'.*?<Resistance Type="d"[^>]*>)[^<]*(</Resistance>)',
            re.S,
        )
        text, n = pat.subn(lambda m, _r=r: m.group(1) + _r + m.group(2), text, count=1)
        if not n:
            print(f"WARN: no ExcSynapse Resistance for Dendrite1_{L}", file=sys.stderr)
    return text


def overlay_train_neuron(train_model: Path, test_model: Path) -> None:
    train = train_model.read_text(encoding="utf-8")
    test = test_model.read_text(encoding="utf-8")
    mn = re.search(r'(<Neuron Class="[^"]+">.*?</Neuron>)', train, re.S)
    if not mn:
        raise SystemExit(f"no Neuron in {train_model}")
    test, n = re.subn(
        r'<Neuron Class="[^"]+">.*?</Neuron>', mn.group(1), test, count=1, flags=re.S
    )
    if not n:
        raise SystemExit(f"no Neuron in {test_model}")
    test_model.write_text(test, encoding="utf-8")


def apply_asym_matrix(params: Path, span_ms: int, pack: str = "A") -> None:
    pack = pack.upper()
    asym = ASYM / f"EXP_span{span_ms}ms_pack{pack}_gen" / "Test" / "Parameters_00.xml"
    if not asym.exists():
        # br480 / long-span: keep gold Test MatrixData (no AsymRm foil pack)
        if span_ms >= 480:
            print(f"keep existing MatrixData (no AsymRm source for span {span_ms})")
            return
        raise SystemExit(f"missing AsymRm matrix source {asym}")
    src = asym.read_text(encoding="utf-8")
    md = re.search(r"(<MatrixData\b[^>]*>.*?</MatrixData>)", src, re.S).group(1)
    mc = re.search(r"(<MatrixClasses\b[^>]*>.*?</MatrixClasses>)", src, re.S).group(1)
    t = params.read_text(encoding="utf-8")
    t = re.sub(r"<MatrixData\b[^>]*>.*?</MatrixData>", md, t, count=1, flags=re.S)
    t = re.sub(r"<MatrixClasses\b[^>]*>.*?</MatrixClasses>", mc, t, count=1, flags=re.S)
    t = set_tag(t, "NumSamples", "8")
    params.write_text(t, encoding="utf-8")


def set_fixed_thr(path: Path, thr: str) -> None:
    t = path.read_text(encoding="utf-8")
    for tag in ("FixedLTZThreshold", "LTZThreshold"):
        t = set_tag(t, tag, thr)
    t = set_tag(t, "UseFixedLTZThreshold", "1")
    t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0")
    path.write_text(t, encoding="utf-8")


def run_nm(ini: Path, tsec: float, log: Path, save: bool = False) -> int:
    """Run NM; SIGTERM when SelectivityLog has ≥8 rows and wall > max(tsec, 100)."""
    import time

    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tsec), "-x"]
    if save:
        cmd.append("-S")
    csv_path = ini.parent / "SelectivityLog" / "results.csv"
    with log.open("w") as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    # Do not kill early before 8 samples — span100 silent can exceed 3×-t wall.
    hard_deadline = time.time() + max(float(tsec) * 8.0, 600.0)
    while proc.poll() is None:
        if time.time() > hard_deadline:
            print(f"SIGTERM NM (hard deadline) pid={proc.pid}")
            proc.terminate()
            break
        if csv_path.exists():
            try:
                n = sum(1 for _ in csv_path.open(encoding="utf-8")) - 1
            except OSError:
                n = 0
            try:
                et = int(
                    subprocess.check_output(
                        ["ps", "-o", "etimes=", "-p", str(proc.pid)], text=True
                    ).strip()
                    or "0"
                )
            except subprocess.CalledProcessError:
                et = 0
            if n >= 8 and et > max(int(tsec), 100):
                print(f"SIGTERM NM pid={proc.pid} n={n} et={et}")
                proc.terminate()
                break
        time.sleep(5)
    try:
        return proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=30)


def soma_from_csv(csv_path: Path) -> list[float]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    out = []
    for r in rows:
        v = r.get("soma_amp_sum") or "0"
        try:
            out.append(float(v))
        except ValueError:
            out.append(0.0)
    return out


def mid_thr(somas: list[float]) -> tuple[float, float]:
    tgt = somas[0]
    below = [s for s in somas[1:] if s < tgt]
    foil = max(below) if below else max(somas[1:] or [0.0])
    gap = tgt - foil
    mid = 0.5 * (tgt + foil) if below else tgt * 0.99
    return mid, gap


def prepare_test(
    root: Path,
    span_ms: int,
    tips: list[int],
    pack: str = "A",
    *,
    keep_tipr: bool = False,
) -> None:
    train, test = root / "Train", root / "Test"
    train_p = (train / "Parameters_00.xml").read_text(encoding="utf-8")
    L = " ".join(str(x) for x in tips)
    tipr_src = get_tag(train_p, "TipSynapseResistance") or TIPRMIN
    tipr_use = tipr_src if keep_tipr else TIPRMIN

    # Fresh Test shell if missing analyzer pattern
    if not (test / "Model_00.xml").exists():
        subprocess.check_call(
            [
                str(SCRIPTS / "copy_config_branch.sh"),
                "test",
                str(test),
                f"{root.name}_Test",
            ]
        )

    subprocess.check_call([str(SCRIPTS / "copy_config_branch.sh"), "sync", str(train), str(test)])
    overlay_train_neuron(train / "Model_00.xml", test / "Model_00.xml")
    subprocess.check_call(
        [sys.executable, str(SCRIPTS / "patch_pattern_scale.py"),
         str(test / "Parameters_00.xml"), str(test / "Model_00.xml"),
         "--span-ms", str(span_ms)]
    )
    subprocess.check_call(
        [sys.executable, str(SCRIPTS / "patch_test_model_branch.py"), str(test / "Model_00.xml")]
    )
    apply_asym_matrix(test / "Parameters_00.xml", span_ms, pack=pack)

    for rel, learner_sb in [("Parameters_00.xml", "0"), ("Model_00.xml", "1")]:
        p = test / rel
        t = p.read_text(encoding="utf-8")
        for tag in (
            "NeuronClassName",
            "MembraneCapacity",
            "DendriteLength",
            "ResistanceMin",
            "ResistanceMax",
            "SynapseResistanceBase",
        ):
            t = copy_tag(train_p, t, tag)
        t = set_tag(t, "TipSynapseResistance", tipr_use)
        t = set_tag(t, "ResistanceMin", RMIN)
        t = set_tag(t, "DendriteLength", L)
        t = set_tag(t, "IsNeedToTrain", "0")
        t = set_tag(t, "FixedLTZThreshold", SILENT_THR)
        t = set_tag(t, "LTZThreshold", SILENT_THR)
        t = set_tag(t, "UseFixedLTZThreshold", "1")
        t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0")
        if rel.startswith("Parameters"):
            t = set_tag(t, "StructureBuildMode", "0")
        else:
            t = set_neuron_sb(t, learner_sb="1", neuron_sb="2")
            t = ensure_generator_tips(t, tips)
            if not keep_tipr:
                t = patch_tip_exc_r(t, tips)
        p.write_text(t, encoding="utf-8")

    # GTS
    ini = (test / "Project.ini").read_text(encoding="utf-8")
    ini = re.sub(
        r"<GlobalTimeStep>[0-9]+</GlobalTimeStep>",
        "<GlobalTimeStep>20000</GlobalTimeStep>",
        ini,
    )
    (test / "Project.ini").write_text(ini, encoding="utf-8")

    # TipR on Train: TipR@Rmin unless keep_tipr (Done TipR path)
    if not keep_tipr:
        for rel in ["Parameters_00.xml", "Model_00.xml"]:
            p = train / rel
            t = p.read_text(encoding="utf-8")
            t = set_tag(t, "TipSynapseResistance", TIPRMIN)
            t = set_tag(t, "ResistanceMin", RMIN)
            if rel.endswith("Model_00.xml"):
                t = patch_tip_exc_r(t, tips)
            p.write_text(t, encoding="utf-8")
    else:
        print(f"keep-tipr: TipSynapseResistance={tipr_use[:48]}…")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_root", type=Path)
    ap.add_argument("--span-ms", type=int, required=True)
    ap.add_argument("--test-t", type=float, default=40.0)
    ap.add_argument("--skip-prepare", action="store_true")
    ap.add_argument("--pack", default="A", help="AsymRm foil pack A|B|C for MatrixData")
    ap.add_argument(
        "--matrix-only",
        action="store_true",
        help="With --skip-prepare: overlay Matrix from --pack before silent/gate",
    )
    ap.add_argument(
        "--allow-done-tipr-fallback",
        action="store_true",
        help="If silent gap<=0, keep current TipR (Done TipR) and mid from foil max anyway",
    )
    ap.add_argument(
        "--keep-tipr",
        action="store_true",
        help="Do not force TipR@Rmin; keep Train TipSynapseResistance (Done TipR)",
    )
    args = ap.parse_args()
    root = args.exp_root.resolve()
    train, test = root / "Train", root / "Test"
    tips = read_lengths(train / "Parameters_00.xml")
    print("L=", tips, "pack=", args.pack.upper(), "keep_tipr=", args.keep_tipr)

    if not args.skip_prepare:
        prepare_test(
            root, args.span_ms, tips, pack=args.pack, keep_tipr=args.keep_tipr
        )
        print("prepared Test hygiene")
    elif args.matrix_only:
        apply_asym_matrix(test / "Parameters_00.xml", args.span_ms, pack=args.pack)
        # Model Parameters often mirror Matrix — keep Params as gate source of foils
        print(f"matrix overlay pack{args.pack.upper()}")

    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        set_fixed_thr(p, SILENT_THR)

    slog = test / "run_silent_probe.log"
    rc = run_nm(test / "Project.ini", args.test_t, slog)
    print("silent rc", rc)
    csv_silent = test / "SelectivityLog" / "results.csv"
    if not csv_silent.exists():
        raise SystemExit("no silent results.csv")
    archived = test / "SelectivityLog" / "results_silent_thr1.csv"
    shutil.copy2(csv_silent, archived)
    somas = soma_from_csv(archived)
    print("somas", somas)
    if len(somas) < 8 or max(somas) <= 0:
        raise SystemExit("silent FAIL: need n>=8 and soma>0")
    mid, gap = mid_thr(somas[:8])
    print(f"mid={mid} gap={gap}")
    if gap <= 0:
        if args.allow_done_tipr_fallback:
            # span100 gen PHASE8 pattern: use mid between target and max foil even if inverted amp
            tgt, foil = somas[0], max(somas[1:8])
            mid = 0.5 * (tgt + foil) if foil < tgt else tgt * 0.99
            print(f"WARN gap<=0 → Done TipR fallback mid={mid}", file=sys.stderr)
        else:
            print("FAIL negative/zero gap — abort gate", file=sys.stderr)
            sys.exit(3)

    mid_s = f"{mid:.12g}"
    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        set_fixed_thr(p, mid_s)

    glog = test / "run_gate.log"
    rc = run_nm(test / "Project.ini", args.test_t, glog)
    print("gate rc", rc)
    subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_silent)])
    rows = list(csv.DictReader(csv_silent.open(encoding="utf-8")))
    if rows:
        r0 = rows[0]
        t_rel = float(r0.get("neuron_t_rel") or -1)
        isis = [float(r0.get(f"isi{i}") or 0) for i in range(3)]
        pend = sum(isis)
        print(
            f"last-pulse t_rel={t_rel} pattern_end={pend} "
            f"ok={t_rel >= 0.8 * pend if t_rel >= 0 and pend else False}"
        )
    print("thr", mid_s)


if __name__ == "__main__":
    main()
