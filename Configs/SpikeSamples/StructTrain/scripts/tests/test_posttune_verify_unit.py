#!/usr/bin/env python3
"""Unit tests for posttune_verify A16 helpers (no NeuroModelerConsole)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import posttune_verify as pv  # noqa: E402


class TestTiprNumeric(unittest.TestCase):
    def test_tipr_numeric_equal_sci_vs_decimal(self):
        a = pv.parse_tipr_vec("2e7 2e7 2e7 8.6e7")
        b = pv.parse_tipr_vec("20000000 20000000 20000000 86000000")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertTrue(pv.tipr_close(a, b))

    def test_tipr_vs_snapshot_reverted(self):
        tipr = "2e7 2e7 2e7 8.6e7"
        self.assertEqual(
            pv.tipr_vs_snapshot(tipr, "20000000 20000000 20000000 86000000", search_reverted=True),
            "same_reverted",
        )

    def test_tipr_vs_snapshot_same_fail(self):
        tipr = "2e7 2e7 2e7 8.6e7"
        self.assertEqual(
            pv.tipr_vs_snapshot(tipr, "20000000 20000000 20000000 86000000", search_reverted=False),
            "same_FAIL",
        )

    def test_tipr_vs_snapshot_applied_best(self):
        self.assertEqual(
            pv.tipr_vs_snapshot(
                "3e7 3e7 3e7 9e7",
                "2e7 2e7 2e7 8.6e7",
                search_reverted=False,
            ),
            "applied_best",
        )


class TestFlags(unittest.TestCase):
    def test_parse_flag_tipr_multivalue(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "posttune_complete.flag"
            p.write_text(
                "mid=0.5 gap=0.1 landscape_ok=1 inference=1 FixedLTZ=0.5 search_reverted=1\n"
                "tipr=7.4e+07 8.9e+07 1.3e+08 5.2e+08\n"
                "tipr_snapshot=2e7 2e7 2e7 8.6e7\n"
                "metrics=0.5,0.2\n",
                encoding="utf-8",
            )
            meta = pv.parse_flag_file(p)
            self.assertEqual(meta["search_reverted"], "1")
            self.assertEqual(meta["tipr"], "7.4e+07 8.9e+07 1.3e+08 5.2e+08")
            self.assertEqual(meta["tipr_snapshot"], "2e7 2e7 2e7 8.6e7")
            self.assertEqual(meta["metrics"], "0.5,0.2")

    def test_train_test_flags_not_merged(self):
        with tempfile.TemporaryDirectory() as td:
            train = Path(td) / "train.flag"
            test = Path(td) / "test.flag"
            train.write_text(
                "mid=1.0 landscape_ok=0 inference=0 search_reverted=1\n"
                "tipr=1 2 3 4\n"
                "tipr_snapshot=1 2 3 4\n",
                encoding="utf-8",
            )
            test.write_text(
                "mid=0.01 landscape_ok=1 inference=1 search_reverted=0\n"
                "tipr=9 9 9 9\n",
                encoding="utf-8",
            )
            phase = pv.load_phase_meta(train, test)
            self.assertTrue(phase.search_reverted)
            self.assertEqual(phase.train["search_reverted"], "1")
            self.assertEqual(phase.test["search_reverted"], "0")
            self.assertEqual(phase.test["mid"], "0.01")


class TestMidSource(unittest.TestCase):
    def test_mid_source_requires_landscape(self):
        meta = {"inference": "1", "mid": "0.05", "landscape_ok": "0"}
        self.assertEqual(pv.mid_source_of(meta, "0.05"), "invalid_landscape")

    def test_mid_source_cpp_ok(self):
        meta = {"inference": "1", "mid": "0.05", "landscape_ok": "1"}
        self.assertEqual(pv.mid_source_of(meta, "0.05"), "cpp")

    def test_mid_source_rejects_nonfinite(self):
        meta = {"inference": "1", "mid": "-inf", "landscape_ok": "1"}
        self.assertEqual(pv.mid_source_of(meta, "-inf"), "invalid_nonfinite")


class TestTiprNan(unittest.TestCase):
    def test_tipr_close_rejects_nan(self):
        a = [float("nan"), 2e7, 2e7, 8.6e7]
        b = [float("nan"), 2e7, 2e7, 8.6e7]
        self.assertFalse(pv.tipr_close(a, b))


class TestAcceptRun(unittest.TestCase):
    def test_search_diff_after_revert_fails(self):
        row = {
            "train_status": "done_search_diff",
            "after": {
                "TipSynapseResistance": "3e7 3e7 3e7 9e7",
                "FixedLTZThreshold": "0.05",
                "IsNeedToTrain": "0",
            },
            "fires": "10000000",
            "tipr_vs_snapshot": "diff_after_revert",
            "mid_source": "cpp",
            "tipr_class": "canon",
            "gate_ok": True,
        }
        ok, reasons = pv.accept_run(
            row, expect_fires="10000000", expect_tipr="search", mode="search", need="0"
        )
        self.assertFalse(ok)
        self.assertTrue(any("search_tipr" in r for r in reasons))

    def test_need1_exited_fails(self):
        row = {
            "train_status": "exited",
            "after": {
                "TipSynapseResistance": "2e7 2e7 2e7 8.6e7",
                "FixedLTZThreshold": "0.05",
                "IsNeedToTrain": "1",
            },
            "fires": "10000000",
            "tipr_vs_snapshot": "",
            "mid_source": "cpp",
            "tipr_class": "canon",
            "gate_ok": True,
        }
        ok, reasons = pv.accept_run(
            row, expect_fires="10000000", expect_tipr="canon", mode="cold", need="1"
        )
        self.assertFalse(ok)

    def test_need1_with_gate_ok_still_fails(self):
        """D2.3: Need=1 + full fires + cpp mid must still fail accept_run."""
        row = {
            "train_status": "incomplete_flag_need1",
            "after": {
                "TipSynapseResistance": "2e7 2e7 2e7 8.6e7",
                "FixedLTZThreshold": "0.05",
                "IsNeedToTrain": "1",
            },
            "fires": "10000000",
            "tipr_vs_snapshot": "",
            "mid_source": "cpp",
            "tipr_class": "canon",
            "gate_ok": True,
            "require_cpp_mid": True,
        }
        ok, reasons = pv.accept_run(
            row, expect_fires="10000000", expect_tipr="canon", mode="cold", need="1"
        )
        self.assertFalse(ok)
        self.assertTrue(any("Need=1" in r for r in reasons))

    def test_empty_fires_fails(self):
        row = {
            "train_status": "done",
            "after": {
                "TipSynapseResistance": "2e7 2e7 2e7 8.6e7",
                "FixedLTZThreshold": "0.05",
                "IsNeedToTrain": "0",
            },
            "fires": "",
            "tipr_vs_snapshot": "",
            "mid_source": "cpp",
            "tipr_class": "canon",
            "gate_ok": True,
        }
        ok, reasons = pv.accept_run(
            row, expect_fires="10000000", expect_tipr="canon", mode="cold", need="0"
        )
        self.assertFalse(ok)
        self.assertTrue(any("fires" in r for r in reasons))


class TestCleanWorkdir(unittest.TestCase):
    def test_prepare_clean_excludes_flag(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "EXP"
            for side in ("Train", "Test"):
                (archive / side).mkdir(parents=True)
                (archive / side / "Parameters_00.xml").write_text("<P/>", encoding="utf-8")
                (archive / side / "Model_00.xml").write_text("<M/>", encoding="utf-8")
                (archive / side / "Project.ini").write_text("[x]\n", encoding="utf-8")
            (archive / "Test" / "posttune_complete.flag").write_text(
                "mid=0.0116458 inference=1 landscape_ok=1\n", encoding="utf-8"
            )
            (archive / "Train" / "posttune_tipr_live.txt").write_text(
                "tipr=91 92 93 94\n", encoding="utf-8"
            )
            old_root = pv.RUNS_ROOT
            try:
                pv.RUNS_ROOT = Path(td) / "runs"
                work = pv.prepare_clean_case("tcase", archive)
                self.assertFalse((work / "Test" / "posttune_complete.flag").exists())
                self.assertFalse((work / "Train" / "posttune_tipr_live.txt").exists())
                self.assertTrue((work / "Train" / "Parameters_00.xml").exists())
            finally:
                pv.RUNS_ROOT = old_root

    def test_flush_current_train_flag_not_archive_salvage(self):
        """H2: current-run flag TipR/Need sync when Console -S lagged."""
        with tempfile.TemporaryDirectory() as td:
            train = Path(td) / "Train"
            train.mkdir()
            (train / "Parameters_00.xml").write_text(
                "<root><TipSynapseResistance>86000000 86000000 86000000 86000000"
                "</TipSynapseResistance><IsNeedToTrain>1</IsNeedToTrain>"
                "<FixedLTZThreshold>1</FixedLTZThreshold>"
                "<LTZThreshold>1</LTZThreshold></root>",
                encoding="utf-8",
            )
            (train / "posttune_complete.flag").write_text(
                "mid=1 gap=-0.001 landscape_ok=0 inference=0 result=2 FixedLTZ=1\n"
                "tipr=2e+07 2e+07 2e+07 8.6e+07\n",
                encoding="utf-8",
            )
            self.assertEqual(pv.flush_current_train_flag(train), "flag_flush")
            t = (train / "Parameters_00.xml").read_text(encoding="utf-8")
            self.assertEqual(pv.get_tag(t, "IsNeedToTrain"), "0")
            tipr = pv.get_tag(t, "TipSynapseResistance") or ""
            self.assertEqual(pv.tipr_class(tipr, "canon"), "canon")
            self.assertEqual(pv.flush_current_train_flag(Path(td) / "missing"), "none")

    def test_weights_identity_mismatch_before_flush(self):
        """D2.2: params TipR ≠ flag TipR before flush → match False."""
        with tempfile.TemporaryDirectory() as td:
            train = Path(td) / "Train"
            train.mkdir()
            (train / "Parameters_00.xml").write_text(
                "<root><TipSynapseResistance>86000000 86000000 86000000 86000000"
                "</TipSynapseResistance><DendriteLength>1 1 1 1</DendriteLength>"
                "<IsNeedToTrain>1</IsNeedToTrain>"
                "<FixedLTZThreshold>1</FixedLTZThreshold>"
                "<LTZThreshold>1</LTZThreshold></root>",
                encoding="utf-8",
            )
            (train / "posttune_complete.flag").write_text(
                "mid=0.05 landscape_ok=1 inference=1 result=1 FixedLTZ=0.05\n"
                "tipr=2e+07 2e+07 2e+07 8.6e+07\n",
                encoding="utf-8",
            )
            before = pv.tipr_weights_identity(train, params_source="none")
            self.assertFalse(before["flag_params_tipr_match"])
            self.assertTrue(before["tipr_sha256"])
            self.assertEqual(pv.flush_current_train_flag(train), "flag_flush")
            after = pv.tipr_weights_identity(train, params_source="flag_flush")
            self.assertTrue(after["flag_params_tipr_match"])
            self.assertEqual(after["params_source"], "flag_flush")


class TestSlog(unittest.TestCase):
    def test_classify_slog_order(self):
        self.assertEqual(pv.classify_slog_gib(1.0), "ok")
        self.assertEqual(pv.classify_slog_gib(2.5), "prune")
        self.assertEqual(pv.classify_slog_gib(3.5), "abort")
        # abort must win over prune for large logs
        self.assertEqual(pv.classify_slog_gib(17.0), "abort")


class TestVerdict(unittest.TestCase):
    def test_verdict_exit(self):
        ok_row = {"row_fail": False, "train_status": "done"}
        bad_row = {"row_fail": True, "train_status": "done", "fail_notes": ["x"]}
        self.assertEqual(pv.verdict_rows([ok_row]), 0)
        self.assertEqual(pv.verdict_rows([ok_row, bad_row]), 1)
        self.assertEqual(pv.verdict_rows([{"row_fail": False, "train_status": "x_FAIL_y"}]), 1)


class TestProvenanceHash(unittest.TestCase):
    def test_sha256_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.bin"
            p.write_bytes(b"nmsdk-a16")
            digest = pv.sha256_file(p)
            self.assertEqual(len(digest), 64)
            self.assertEqual(digest, pv.sha256_file(p))
            self.assertIsNone(pv.sha256_file(Path(td) / "missing"))

    def test_sha256_paths_keys(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            p.write_text("a", encoding="utf-8")
            d = pv.sha256_paths([p])
            self.assertEqual(len(d), 1)
            self.assertTrue(all(v and len(v) == 64 for v in d.values()))


class TestTiprExpect(unittest.TestCase):
    def test_tipr_matches_expect_canon_flat(self):
        self.assertTrue(pv.tipr_matches_expect("canon", "canon"))
        self.assertTrue(pv.tipr_matches_expect("flat", "flat"))
        self.assertFalse(pv.tipr_matches_expect("flat", "canon"))

    def test_tipr_matches_expect_legacy(self):
        self.assertTrue(pv.tipr_matches_expect("other", "legacy"))
        self.assertTrue(pv.tipr_matches_expect("legacy", "legacy"))
        self.assertFalse(pv.tipr_matches_expect("canon", "legacy"))

    def test_tipr_expect_fail_fixture(self):
        """Canon case with flat TipR must fail the expect gate."""
        tipr = "8.6e7 8.6e7 8.6e7 8.6e7"
        got = pv.tipr_class(tipr, "canon")
        self.assertEqual(got, "flat")
        self.assertFalse(pv.tipr_matches_expect(got, "canon"))


if __name__ == "__main__":
    unittest.main()
