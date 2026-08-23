#!/usr/bin/env python3
"""Clarify tab1 Pattern legends and overlay Stimulus/Neuron spike on tab2 Dendrite graph.

Patches all SelectivityFastSpan EXP_*/{Train,Test}/Interface.xml (default), or paths given
on the CLI. Idempotent: skips tab2 insert if Stimulus series already present.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Contrasting overlays on dendrite axis (-0.01..0.08): 0/1 spikes clip at top as markers.
STIMULUS_COLOR = "-16777216"  # black
NEURON_SPIKE_COLOR = "-6750055"  # same as tab1 Neuron.Output


def _replace_first(text: str, old: str, new: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def patch_tab1_pattern(text: str) -> tuple[str, bool]:
    m_tab1 = re.search(
        r"<UGEngineControllWidget\.UWatch\.tab_1>.*?</UGEngineControllWidget\.UWatch\.tab_1>",
        text,
        flags=re.DOTALL,
    )
    if not m_tab1:
        return text, False

    tab1 = m_tab1.group(0)
    m_g0 = re.search(r"<graph_0>.*?</graph_0>", tab1, flags=re.DOTALL)
    if not m_g0:
        return text, False

    g0 = m_g0.group(0)
    changed = False

    g0, c = _replace_first(
        g0,
        "<ChartTitle>Pattern and Trigger</ChartTitle>",
        "<ChartTitle>Pattern: ISI + Stimulus</ChartTitle>",
    )
    changed = changed or c

    for i in range(4):
        old_name = f"<SerieName>InputPattern({i},0)</SerieName>"
        new_name = f"<SerieName>ISI dend{i + 1}</SerieName>"
        g0, c = _replace_first(g0, old_name, new_name)
        changed = changed or c

        # Set YShift on serie_i (ISI lines)
        yshift = f"{0.15 * (i + 1):g}"

        def set_yshift(m: re.Match[str], ys: str = yshift) -> str:
            nonlocal changed
            block = m.group(0)
            new_block, n = re.subn(
                r"<SerieYShift>[^<]*</SerieYShift>",
                f"<SerieYShift>{ys}</SerieYShift>",
                block,
                count=1,
            )
            if n and new_block != block:
                changed = True
            return new_block

        g0, _ = re.subn(
            rf"<serie_{i}>.*?</serie_{i}>",
            set_yshift,
            g0,
            count=1,
            flags=re.DOTALL,
        )

    def patch_gen(m: re.Match[str]) -> str:
        nonlocal changed
        block = m.group(0)
        if "<SerieName>Generator1.Output</SerieName>" in block:
            block = block.replace(
                "<SerieName>Generator1.Output</SerieName>",
                "<SerieName>Stimulus</SerieName>",
            )
            changed = True
        if "<SerieName>Stimulus</SerieName>" in block:
            new_block, n = re.subn(
                r"<SerieWidth>[^<]*</SerieWidth>",
                "<SerieWidth>2</SerieWidth>",
                block,
                count=1,
            )
            if n and new_block != block:
                changed = True
            block = new_block
        return block

    g0, _ = re.subn(
        r"<serie_4>.*?</serie_4>",
        patch_gen,
        g0,
        count=1,
        flags=re.DOTALL,
    )

    g0, c = _replace_first(
        g0,
        "<SerieName>Neuron.Output</SerieName>",
        "<SerieName>Neuron spike</SerieName>",
    )
    changed = changed or c

    if not changed:
        return text, False

    tab1_new = tab1[: m_g0.start()] + g0 + tab1[m_g0.end() :]
    text = text[: m_tab1.start()] + tab1_new + text[m_tab1.end() :]
    return text, True


def make_overlay_serie(
    index: int,
    name: str,
    color: str,
    component: str,
    prop: str,
    width: int,
    yshift: str,
    window_size: str,
) -> str:
    return f"""			<serie_{index}>
				<SerieName>{name}</SerieName>
				<SerieWidth>{width}</SerieWidth>
				<SerieLineType>1</SerieLineType>
				<SerieColor>{color}</SerieColor>
				<SerieYShift>{yshift}</SerieYShift>
				<SerieEnabled>1</SerieEnabled>
				<SerieChannel>0</SerieChannel>
				<SerieWindowSize>{window_size}</SerieWindowSize>
				<SerieXyMinIntervalMs>0</SerieXyMinIntervalMs>
				<SerieXyMinDistance>0</SerieXyMinDistance>
				<SerieNameComponent>{component}</SerieNameComponent>
				<SerieNameProperty>{prop}</SerieNameProperty>
				<SerieJx>0</SerieJx>
				<SerieJy>0</SerieJy>
				<SerieXKind>0</SerieXKind>
				<SerieXComponent></SerieXComponent>
				<SerieXProperty></SerieXProperty>
				<SerieXJx>-1</SerieXJx>
				<SerieXJy>-1</SerieXJy>
				<SerieXSlice>0</SerieXSlice>
				<SerieYKind>1</SerieYKind>
				<SerieYComponent>{component}</SerieYComponent>
				<SerieYProperty>{prop}</SerieYProperty>
				<SerieYJx>0</SerieYJx>
				<SerieYJy>0</SerieYJy>
				<SerieYSlice>0</SerieYSlice>
			</serie_{index}>"""


def patch_tab2_dendrite(text: str) -> tuple[str, bool]:
    m_tab2 = re.search(
        r"<UGEngineControllWidget\.UWatch\.tab_2>.*?</UGEngineControllWidget\.UWatch\.tab_2>",
        text,
        flags=re.DOTALL,
    )
    if not m_tab2:
        return text, False
    tab2 = m_tab2.group(0)
    m_g0 = re.search(r"<graph_0>.*?</graph_0>", tab2, flags=re.DOTALL)
    if not m_g0:
        return text, False
    g0 = m_g0.group(0)
    changed = False

    g0, c = _replace_first(
        g0,
        "<ChartTitle>Dendrite Amplitudes</ChartTitle>",
        "<ChartTitle>Dendrite Amplitudes + Stimulus</ChartTitle>",
    )
    changed = changed or c

    if "<SerieName>Stimulus</SerieName>" in g0:
        if changed:
            tab2_new = tab2[: m_g0.start()] + g0 + tab2[m_g0.end() :]
            text = text[: m_tab2.start()] + tab2_new + text[m_tab2.end() :]
        return text, changed

    wm = re.search(r"<SerieWindowSize>(\d+)</SerieWindowSize>", g0)
    window_size = wm.group(1) if wm else "22016"

    g0, n = re.subn(
        r"<SeriesCount>5</SeriesCount>",
        "<SeriesCount>7</SeriesCount>",
        g0,
        count=1,
    )
    if n:
        changed = True

    # YShift 0: dendrite AxisYmax ~0.08; 0/1 pulses clip at top as event markers.
    stim = make_overlay_serie(
        5,
        "Stimulus",
        STIMULUS_COLOR,
        "NeuronTimeLearner.DatasetMatrix.Generator1",
        "Output",
        2,
        "0",
        window_size,
    )
    neu = make_overlay_serie(
        6,
        "Neuron spike",
        NEURON_SPIKE_COLOR,
        "NeuronTimeLearner.Neuron",
        "Output",
        1,
        "0",
        window_size,
    )
    insert = stim + "\n" + neu + "\n"

    if re.search(r"</serie_4>\s*</graph_0>", g0):
        g0, n = re.subn(
            r"(</serie_4>)(\s*</graph_0>)",
            r"\1\n" + insert + r"\2",
            g0,
            count=1,
        )
        if not n:
            raise RuntimeError("tab2 graph_0: insert failed")
        changed = True
    else:
        raise RuntimeError("tab2 graph_0: cannot find serie_4 before </graph_0>")

    tab2_new = tab2[: m_g0.start()] + g0 + tab2[m_g0.end() :]
    text = text[: m_tab2.start()] + tab2_new + text[m_tab2.end() :]
    return text, changed


def patch_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    text, c1 = patch_tab1_pattern(raw)
    text, c2 = patch_tab2_dendrite(text)
    if c1 or c2:
        path.write_text(text, encoding="utf-8")
    return c1 or c2


def default_paths() -> list[Path]:
    return sorted(ROOT.glob("EXP_*/Train/Interface.xml")) + sorted(
        ROOT.glob("EXP_*/Test/Interface.xml")
    )


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else default_paths()
    if not paths:
        print("No Interface.xml found", file=sys.stderr)
        return 1
    n_changed = 0
    for p in paths:
        if not p.is_file():
            print(f"SKIP missing {p}", file=sys.stderr)
            continue
        try:
            did = patch_file(p)
        except Exception as e:
            print(f"FAIL {p}: {e}", file=sys.stderr)
            return 1
        rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
        print(f"{'PATCH' if did else 'OK  '} {rel}")
        if did:
            n_changed += 1
    print(f"Done: {n_changed}/{len(paths)} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
