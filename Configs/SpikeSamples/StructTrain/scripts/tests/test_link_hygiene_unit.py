#!/usr/bin/env python3
"""A15 regression tests: generator-tap rewrites must not touch synapse->channel links.

Fixture tests/data/a15_clean_classic_model.xml = Bin dfbfea63
SelectivityAsymRm/EXP_span25ms_packA_gen/Test/Model_00.xml (Classic, DendriteLength 15 12 8 1,
with stale multi-taps 9/13/15, 9/11/12, 7/8).  No NeuroModelerConsole needed.
Run: python3 -m unittest tests.test_link_hygiene_unit -v   (from StructTrain/scripts)
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from repro_cold_lib import (  # noqa: E402
    fix_branch_tip_links,
    fix_generator_tip_links,
    rewrite_links_to_tip1,
    strip_dendrite_segments_above_one,
)

FIXTURE = Path(__file__).resolve().parent / "data" / "a15_clean_classic_model.xml"
ELEM = re.compile(r'<elem Type="ULink">(.*?)</elem>', re.S)
ITEM = re.compile(r'<Item Type="ULinkSide" Index="[^"]*" Name="[^"]+">([^<]+)</Item>')
CONN = re.compile(r'<Connector Type="ULinkSide" Index="[^"]*" Name="([^"]+)">([^<]+)</Connector>')
MEMB = re.compile(r'\.(Dendrite\d+_\d+)\.')


def links(text):
    out = []
    for m in ELEM.finditer(text):
        im = ITEM.search(m.group(1))
        out.append((im.group(1) if im else "", [(n, c) for n, c in CONN.findall(m.group(1))], m.group(0)))
    return out


def synapse_violations(text):
    bad = []
    for item, conns, _ in links(text):
        sm = re.search(r'\.(Dendrite\d+_\d+)\.(?:Exc|Inh)Synapse\d+$', item)
        if not sm:
            continue
        targets = [c for n, c in conns if n == "SynapticInputs"]
        membs = {MEMB.search(c).group(1) for c in targets if MEMB.search(c)}
        if len(targets) != 1 or membs != {sm.group(1)}:
            bad.append((item, targets))
    return bad


def generator_taps(text):
    taps = []
    for item, conns, _ in links(text):
        if item.endswith("DatasetMatrix.Generator1"):
            taps += [c for n, c in conns if n == "Input" and "Synapse" in c]
    return taps


class LinkHygieneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = FIXTURE.read_text(encoding="utf-8")

    def test_fixture_is_clean(self):
        self.assertEqual(synapse_violations(self.clean), [])

    def test_fix_generator_tip_links_keeps_synapse_links(self):
        out = fix_generator_tip_links(self.clean, [15, 12, 8, 1])
        self.assertEqual(synapse_violations(out), [], "A15: synapse fan-out introduced")
        taps = generator_taps(out)
        self.assertEqual(len(taps), len(set(taps)), f"duplicate generator taps: {taps}")
        self.assertEqual(sorted(taps), sorted(
            f"NeuronTimeLearner.Neuron.Dendrite{d}_{L}.ExcSynapse1"
            for d, L in enumerate([15, 12, 8, 1], start=1)))

    def test_only_generator_elements_change(self):
        out = fix_generator_tip_links(self.clean, [15, 12, 8, 1])
        before = [raw for item, _, raw in links(self.clean) if not item.endswith("Generator1")]
        after = [raw for item, _, raw in links(out) if not item.endswith("Generator1")]
        self.assertEqual(before, after)
        strip = lambda t: ELEM.sub("", t)  # noqa: E731
        self.assertEqual(strip(self.clean), strip(out), "non-link bytes changed")

    def test_idempotent(self):
        once = fix_generator_tip_links(self.clean, [15, 12, 8, 1])
        self.assertEqual(once, fix_generator_tip_links(once, [15, 12, 8, 1]))

    def test_branch_variant_does_not_touch_synapse_items(self):
        out = fix_branch_tip_links(self.clean, [5, 3])
        self.assertEqual(synapse_violations(out), [])

    def test_strip_then_rewrite_to_tip1(self):
        out = rewrite_links_to_tip1(strip_dendrite_segments_above_one(self.clean))
        present = set(re.findall(r'<(Dendrite\d+_\d+) Class="', out))
        self.assertEqual(present, {f"Dendrite{d}_1" for d in range(1, 5)})
        refs = set(MEMB.findall(" ".join(i + " " + " ".join(c for _, c in cs) for i, cs, _ in links(out))))
        self.assertTrue(refs <= present, f"dangling links to {sorted(refs - present)[:5]}")
        self.assertEqual(synapse_violations(out), [])
        self.assertEqual(sorted(generator_taps(out)), sorted(
            f"NeuronTimeLearner.Neuron.Dendrite{d}_1.ExcSynapse1" for d in range(1, 5)))
        n = len(ELEM.findall(out))
        self.assertIn(f'<Links Type="ULinksList" Size="{n}">', out)


if __name__ == "__main__":
    unittest.main()
