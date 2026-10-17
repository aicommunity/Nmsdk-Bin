#!/usr/bin/env python3
"""Unit tests for SoftCold S1 fix (SBM=2 all + tip-1 Model). No NeuroModelerConsole."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from repro_cold_lib import (  # noqa: E402
    TIPR_COLD,
    force_structure_build_mode,
    get_all_tags,
    get_tag,
    soft_cold_reset_train,
    tip_indices,
)


ASYM50_TRAIN = (
    ROOT / "SelectivityAsymRm" / "EXP_span50ms_packA_preinh" / "Train"
)


class TestForceSbm(unittest.TestCase):
    def test_all_duplicates_become_2(self):
        xml = (
            "<Root>"
            '<StructureBuildMode Type="i">0</StructureBuildMode>'
            "<IsNeedToTrain>0</IsNeedToTrain>"
            '<StructureBuildMode Type="i">0</StructureBuildMode>'
            "</Root>"
        )
        out = force_structure_build_mode(xml, "2")
        self.assertEqual(get_all_tags(out, "StructureBuildMode"), ["2", "2"])

    def test_inject_when_missing(self):
        xml = "<Root><IsNeedToTrain>1</IsNeedToTrain></Root>"
        out = force_structure_build_mode(xml, "2")
        self.assertEqual(get_all_tags(out, "StructureBuildMode"), ["2"])


@unittest.skipUnless(ASYM50_TRAIN.is_dir(), "asym50 Train archive missing")
class TestSoftColdAsym50(unittest.TestCase):
    def test_sbm2_strip_tip1_contract(self):
        with tempfile.TemporaryDirectory() as td:
            train = Path(td) / "Train"
            shutil.copytree(
                ASYM50_TRAIN,
                train,
                ignore=shutil.ignore_patterns(
                    "StatisticLog", "EventsLog", ".cache", "*.bak", "save.tmp"
                ),
            )
            pt0 = (train / "Parameters_00.xml").read_text(encoding="utf-8")
            mt0 = (train / "Model_00.xml").read_text(encoding="utf-8")
            self.assertIn("0", get_all_tags(pt0, "StructureBuildMode"))
            self.assertGreater(max(tip_indices(mt0)), 1)

            soft_cold_reset_train(train)

            pt = (train / "Parameters_00.xml").read_text(encoding="utf-8")
            mt = (train / "Model_00.xml").read_text(encoding="utf-8")
            sbm_p = get_all_tags(pt, "StructureBuildMode")
            sbm_m = get_all_tags(mt, "StructureBuildMode")
            self.assertTrue(sbm_p and all(s == "2" for s in sbm_p), sbm_p)
            self.assertTrue(sbm_m and all(s == "2" for s in sbm_m), sbm_m)
            L = " ".join((get_tag(pt, "DendriteLength") or "").split())
            self.assertEqual(L, "1 1 1 1")
            tipr = " ".join((get_tag(pt, "TipSynapseResistance") or "").split())
            self.assertEqual(tipr, TIPR_COLD)
            self.assertEqual(get_tag(pt, "NumDendriteMembraneParts"), "1")
            tips = tip_indices(mt)
            self.assertTrue(tips and max(tips) <= 1, tips)

            ini = (train / "Project.ini").read_text(encoding="utf-8")
            self.assertIn("<ProjectAutoSaveModelTimeInterval>10</ProjectAutoSaveModelTimeInterval>", ini)

            contract = json.loads(
                (train / "cold_reset_contract.json").read_text(encoding="utf-8")
            )
            self.assertEqual(contract["softcold_fix"], "2026-09-27_sbm2_strip_tip1")
            self.assertEqual(contract["mode"], "soft")
            self.assertEqual(contract["project_autosave_model_time_interval"], "10")
            self.assertLessEqual(contract["model_topology"]["max_seg"], 1)
            self.assertTrue(
                all(s == "2" for s in contract["xml_before_nm"]["StructureBuildMode_all"])
            )


if __name__ == "__main__":
    unittest.main()
