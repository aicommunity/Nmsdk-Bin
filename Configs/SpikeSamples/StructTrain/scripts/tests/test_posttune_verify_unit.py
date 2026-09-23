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


if __name__ == "__main__":
    unittest.main()
