#!/usr/bin/env python3
"""Unit tests for posttune_verify A16 helpers (no NeuroModelerConsole)."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import posttune_verify as pv  # noqa: E402
import repro_cold_lib as cold  # noqa: E402


class TestConsoleResolution(unittest.TestCase):
    def test_console_defaults_to_the_current_checkout(self):
        root = Path("/isolated/nmsdk")
        self.assertEqual(
            cold.resolve_console(root, {}),
            root / "Bin/Platform/Linux/NeuroModelerConsole",
        )

    def test_console_can_be_overridden_for_a_host(self):
        self.assertEqual(
            cold.resolve_console(Path("/isolated/nmsdk"), {"NMSDK_CONSOLE": "/tmp/console"}),
            Path("/tmp/console"),
        )

    def test_phase_gate_scripts_follow_the_active_checkout_and_console(self):
        repo_root = cold.NMSDK_ROOT
        scripts = (
            repo_root
            / "Bin/Configs/SpikeSamples/StructTrain/SelectivityBranch/scripts/phase8_tiprmin_gate.py",
            repo_root
            / "Bin/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/phase9_preinh_bc_gate.py",
        )
        with patch.dict(os.environ, {"NMSDK_CONSOLE": "/tmp/audit-console"}):
            for index, script in enumerate(scripts):
                spec = importlib.util.spec_from_file_location(f"phase_gate_{index}", script)
                self.assertIsNotNone(spec)
                self.assertIsNotNone(spec.loader)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                with self.subTest(script=script.name):
                    self.assertNotIn("/home/user/Nmsdk", script.read_text(encoding="utf-8"))
                    self.assertEqual(module.ROOT, repo_root / "Bin/Configs/SpikeSamples/StructTrain")
                    self.assertEqual(module.NM, Path("/tmp/audit-console"))


class TestColdResetContract(unittest.TestCase):
    def _write_contract(self, train: Path, trainer: str) -> dict:
        train.mkdir(parents=True)
        (train / "Parameters_00.xml").write_text(
            "<Root>"
            "<NeuronClassName>NSPNeuronGenAsymRmD001C1e9</NeuronClassName>"
            "<DendriteLength>1 1 1 1</DendriteLength>"
            "<TipSynapseResistance>86000000 86000000 86000000 86000000</TipSynapseResistance>"
            "<IsNeedToTrain>1</IsNeedToTrain>"
            "<ResetToUntrainedState>1</ResetToUntrainedState>"
            "<FixedLTZThreshold>1</FixedLTZThreshold>"
            "<StructureBuildMode>2</StructureBuildMode>"
            f"<{trainer} Class=\"N{trainer}\"></{trainer}>"
            "</Root>",
            encoding="utf-8",
        )
        (train / "Model_00.xml").write_text("<Model/>", encoding="utf-8")
        contract_path = cold.write_cold_reset_contract(train)
        import json

        return json.loads(contract_path.read_text(encoding="utf-8"))

    def test_branch_detection_uses_trainer_and_records_post_build_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            contract = self._write_contract(
                Path(td) / "Train", "NeuronTimeLearnerBranch"
            )
        self.assertTrue(contract["is_branch"])
        runtime = contract["expected_runtime_after_reset"]
        self.assertEqual(runtime["DendriteLength"], "1 1 1 1")
        self.assertEqual(runtime["reference_dendrite_index"], 3)
        self.assertIn("clamps runtime length to 1", runtime["note"])

    def test_classic_trainer_has_no_branch_reference_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            contract = self._write_contract(
                Path(td) / "Train", "NeuronTimeLearner"
            )
        self.assertFalse(contract["is_branch"])
        runtime = contract["expected_runtime_after_reset"]
        self.assertEqual(runtime["DendriteLength"], "1 1 1 1")
        self.assertIsNone(runtime["reference_dendrite_index"])


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

    def test_training_audit_events_are_preserved_in_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            train = root / "work" / "Train"
            run_dir = root / "runs" / "case" / "run-1"
            train.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            source = train / "TimeLearnerTrainingAudit.log"
            source.write_text(
                "schema=1;kind=reset;trainer=branch;length_before=[1,1,1,0];length_after=[1,1,1,1]\n"
                "schema=1;kind=iteration;trainer=branch;iter=1;eol_sync=0;eol_amp=0\n",
                encoding="utf-8",
            )
            provenance = {"artifacts": []}
            records = pv.copy_training_audit(train, run_dir, provenance, "run-1")
            copied = run_dir / "Train" / source.name
            self.assertEqual(records, 2)
            self.assertEqual(copied.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
            self.assertEqual(provenance["training_audit"]["records"], 2)
            self.assertEqual(provenance["training_audit"]["sha256"], pv.sha256_file(copied))
            self.assertEqual(provenance["artifacts"][0]["path"], "Train/TimeLearnerTrainingAudit.log")


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


class TestFailureClass(unittest.TestCase):
    def test_done_gate_fail_is_gate_not_incomplete(self):
        row = {
            "train_status": "done_flag_flush_gate_FAIL_gate_rc=1",
            "gate_ok": False,
            "fires": "00000000",
            "tipr_class": "canon",
            "after": {"TipSynapseResistance": "2e7 2e7 2e7 8.6e7", "FixedLTZThreshold": "0.07"},
            "mid_source": "cpp",
            "fail_notes": "gate_rc=1",
        }
        ok, reasons = pv.accept_run(
            row, expect_fires="10000000", expect_tipr="canon", mode="cold", need="0"
        )
        self.assertFalse(ok)
        self.assertFalse(any(r.startswith("train_incomplete:") for r in reasons))
        self.assertEqual(pv.classify_failure_class(reasons, row), "gate_fail")

    def test_exited_is_train_incomplete(self):
        row = {
            "train_status": "exited",
            "gate_ok": True,
            "fires": "10000000",
            "tipr_class": "canon",
            "after": {"TipSynapseResistance": "2e7 2e7 2e7 8.6e7", "FixedLTZThreshold": "0.07"},
            "mid_source": "cpp",
        }
        ok, reasons = pv.accept_run(
            row, expect_fires="10000000", expect_tipr="canon", mode="cold", need="1"
        )
        self.assertFalse(ok)
        self.assertEqual(pv.classify_failure_class(reasons, row), "train_incomplete")


class TestSeparateTrainingAndQualityOutcomes(unittest.TestCase):
    def test_cpp_refusal_is_separate_and_skips_quality_gate(self):
        convergence = pv.classify_training_convergence(
            "1", {}, cpp_failure=(4, 1)
        )
        self.assertEqual(convergence, "cpp_training_refusal")
        self.assertFalse(pv.should_run_quality_gate(convergence))
        self.assertEqual(
            pv.classify_detection_quality(
                gate_ok=None,
                gate_fail="not_evaluated_training_incomplete",
                training_convergence=convergence,
            ),
            "not_evaluated_training_incomplete",
        )

    def test_cpp_refusal_failure_bucket_does_not_masquerade_as_gate_failure(self):
        row = {
            "train_status": "cpp_training_failure_1",
            "gate_evaluated": False,
            "gate_ok": None,
            "fires": "",
            "tipr_class": "",
            "after": {"IsNeedToTrain": "1"},
        }
        ok, reasons = pv.accept_run(
            row,
            expect_fires="10000000",
            expect_tipr="",
            mode="cold",
            need="1",
            child_rc=-15,
        )
        self.assertFalse(ok)
        self.assertFalse(any(r == "fires_missing" for r in reasons))
        self.assertEqual(pv.classify_failure_class(reasons, row), "trainer_refused")

    def test_posttune_nonseparable_is_still_completed_training(self):
        self.assertEqual(
            pv.classify_training_convergence("1", {"result": "2"}),
            "converged_posttune_finalized",
        )
        self.assertEqual(pv.classify_posttune_quality({"result": "2"}), "nonseparable")

    def test_need_one_without_posttune_flag_is_not_converged(self):
        self.assertEqual(
            pv.classify_training_convergence("1", {}), "not_converged_at_stop"
        )
        self.assertEqual(
            pv.classify_detection_quality(
                gate_ok=False,
                gate_fail="fires_missing",
                training_convergence="not_converged_at_stop",
            ),
            "not_evaluated_training_incomplete",
        )

    def test_detection_gate_is_reported_independently(self):
        self.assertEqual(
            pv.classify_detection_quality(
                gate_ok=True,
                gate_fail="",
                training_convergence="converged_posttune_finalized",
            ),
            "pass",
        )
        self.assertEqual(
            pv.classify_detection_quality(
                gate_ok=False,
                gate_fail="fires_missing",
                training_convergence="converged_posttune_finalized",
            ),
            "target_not_detected",
        )

    def test_skipped_and_unknown_states_are_explicit(self):
        self.assertEqual(
            pv.classify_training_convergence("", {}, skipped=True), "not_run"
        )
        self.assertEqual(
            pv.classify_training_convergence("", {}), "insufficient_data"
        )
        self.assertEqual(
            pv.classify_posttune_quality({"result": "99"}), "not_reached_or_unknown"
        )

    def test_markdown_report_has_independent_outcome_columns(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "result.md"
            row = {
                "case": "fixture",
                "train_status": "done_gate_FAIL_gate_rc=1",
                "training_convergence": "converged_posttune_finalized",
                "posttune_quality": "nonseparable",
                "detection_quality": "target_not_detected",
                "after": {"IsNeedToTrain": "0"},
                "tipr_class": "canon",
                "fires": "",
                "metrics": "fires_missing",
                "mid_source": "missing",
                "tipr_vs_snapshot": "",
                "search_reverted": 0,
                "gold_thr": "",
                "fail_notes": [],
            }
            with patch.object(pv, "OUT", out):
                pv.append_result([row])
            report = out.read_text(encoding="utf-8")
            self.assertIn("| training convergence | PostTune separability | test target detection |", report)
            self.assertIn("| converged_posttune_finalized | nonseparable | target_not_detected |", report)


class TestRmaxStallTick(unittest.TestCase):
    def test_streak_grows_when_tipr_at_rmax_and_L_frozen(self):
        rmax = 1e11
        tipr = "100000000000 100000000000 5e7 8.6e7"
        L = "49 41 25 1"
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr, length=L, need="1", rmax=rmax,
            prev_L=None, prev_tipr=None, streak=0,
        )
        self.assertEqual(streak, 1)
        self.assertEqual(prev_L, L)
        for expect in range(2, 9):
            streak, prev_L, prev_t = pv.rmax_stall_tick(
                tipr=tipr, length=L, need="1", rmax=rmax,
                prev_L=prev_L, prev_tipr=prev_t, streak=streak,
            )
            self.assertEqual(streak, expect)

    def test_streak_resets_when_L_grows(self):
        rmax = 1e11
        tipr = "1e11 1e11 5e7 8.6e7"
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr, length="49 41 25 1", need="1", rmax=rmax,
            prev_L=None, prev_tipr=None, streak=0,
        )
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr, length="49 41 25 1", need="1", rmax=rmax,
            prev_L=prev_L, prev_tipr=prev_t, streak=streak,
        )
        self.assertEqual(streak, 2)
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr, length="50 41 25 1", need="1", rmax=rmax,
            prev_L=prev_L, prev_tipr=prev_t, streak=streak,
        )
        self.assertEqual(streak, 1)
        self.assertEqual(prev_L, "50 41 25 1")

    def test_streak_resets_when_tipr_moves_off_rmax(self):
        """Escape in progress: TipR leaves Rmax on one dend — do not abort."""
        rmax = 1e11
        L = "97 51 25 1"
        tipr_hi = "100000000000 100000000000 5e7 8.6e7"
        tipr_esc = "2740486816 100000000000 5e7 8.6e7"
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr_hi, length=L, need="1", rmax=rmax,
            prev_L=None, prev_tipr=None, streak=0,
        )
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr_hi, length=L, need="1", rmax=rmax,
            prev_L=prev_L, prev_tipr=prev_t, streak=streak,
        )
        self.assertEqual(streak, 2)
        streak, _, _ = pv.rmax_stall_tick(
            tipr=tipr_esc, length=L, need="1", rmax=rmax,
            prev_L=prev_L, prev_tipr=prev_t, streak=streak,
        )
        self.assertEqual(streak, 1)

    def test_streak_resets_when_need0_or_tipr_leaves_rmax(self):
        rmax = 1e11
        tipr_hi = "1e11 1e11 5e7 8.6e7"
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr_hi, length="49 41 25 1", need="1", rmax=rmax,
            prev_L=None, prev_tipr=None, streak=0,
        )
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr_hi, length="49 41 25 1", need="0", rmax=rmax,
            prev_L=prev_L, prev_tipr=prev_t, streak=streak,
        )
        self.assertEqual(streak, 0)
        streak, prev_L, prev_t = pv.rmax_stall_tick(
            tipr=tipr_hi, length="49 41 25 1", need="1", rmax=rmax,
            prev_L=None, prev_tipr=None, streak=0,
        )
        streak, _, _ = pv.rmax_stall_tick(
            tipr="2e7 2e7 2e7 8.6e7",
            length="49 41 25 1",
            need="1",
            rmax=rmax,
            prev_L=prev_L,
            prev_tipr=prev_t,
            streak=streak,
        )
        self.assertEqual(streak, 0)

    def test_tipr_any_at_rmax(self):
        self.assertTrue(pv.tipr_any_at_rmax("1e11 1 1 1", 1e11))
        self.assertFalse(pv.tipr_any_at_rmax("2e7 2e7 2e7 8.6e7", 1e11))


class TestAutosavePoll(unittest.TestCase):
    def test_poll_params_detects_mtime_bump(self):
        with tempfile.TemporaryDirectory() as td:
            params = Path(td) / "Parameters_00.xml"
            params.write_text(
                "<Root><IsNeedToTrain>1</IsNeedToTrain>"
                "<TipSynapseResistance>1 1 1 1</TipSynapseResistance>"
                "<DendriteLength>1 1 1 1</DendriteLength></Root>\n",
                encoding="utf-8",
            )
            m0 = params.stat().st_mtime
            snap0 = pv.poll_params_snapshot(params, prev_mtime=m0)
            self.assertFalse(snap0["autosave_seen"])
            self.assertEqual(snap0["need"], "1")
            time.sleep(0.02)
            params.write_text(
                "<Root><IsNeedToTrain>0</IsNeedToTrain>"
                "<TipSynapseResistance>2e7 2e7 2e7 8.6e7</TipSynapseResistance>"
                "<DendriteLength>10 10 10 10</DendriteLength></Root>\n",
                encoding="utf-8",
            )
            snap1 = pv.poll_params_snapshot(params, prev_mtime=m0)
            self.assertTrue(snap1["autosave_seen"])
            self.assertEqual(snap1["need"], "0")
            self.assertTrue(snap1["tipr_settled"])
            self.assertTrue(pv.softcold_early_done(snap1, flag_hit=False))

    def test_early_done_requires_settled_without_flag(self):
        snap = {
            "need": "0",
            "tipr_settled": False,
            "tipr": "2e7 2e7 2e7 8.6e7",
        }
        self.assertFalse(pv.softcold_early_done(snap, flag_hit=False))
        self.assertTrue(pv.softcold_early_done(snap, flag_hit=True))

    def test_early_done_rejects_cold_flat_tipr(self):
        snap = {
            "need": "0",
            "tipr_settled": True,
            "tipr": "86000000 86000000 86000000 86000000",
        }
        self.assertFalse(pv.softcold_early_done(snap, flag_hit=False))
        self.assertTrue(pv.softcold_early_done(snap, flag_hit=True))

    def test_early_done_accepts_canon_tipr(self):
        snap = {
            "need": "0",
            "tipr_settled": True,
            "tipr": "2e7 2e7 2e7 8.6e7",
        }
        self.assertTrue(pv.softcold_early_done(snap, flag_hit=False))


class TestClassicAmpNormEpsHeader(unittest.TestCase):
    """TL-01: classic kAmpNormEps must stay a floating literal (not int→0)."""

    def test_header_declares_double_eps(self):
        hdr = (
            Path(__file__).resolve().parents[5]
            / "Libraries"
            / "Nmsdk-PulseLib"
            / "Core"
            / "NNeuronTimeLearner.h"
        )
        # parents: tests→scripts→StructTrain→SpikeSamples→Configs→Bin→Nmsdk = 6?
        # Path(__file__)=.../StructTrain/scripts/tests/test_...
        # parents[0]=tests, [1]=scripts, [2]=StructTrain, [3]=SpikeSamples, [4]=Configs, [5]=Bin
        # Need Nmsdk root = parents[6]
        hdr = Path(__file__).resolve().parents[6] / "Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.h"
        text = hdr.read_text(encoding="utf-8", errors="replace")
        self.assertRegex(
            text,
            r"static\s+constexpr\s+double\s+kAmpNormEps\s*=\s*1e-5\s*;",
        )
        self.assertNotRegex(
            text,
            r"static\s+constexpr\s+int\s+kAmpNormEps\s*=",
        )
        # Narrowing would make int(1e-5)==0; double must remain positive 1e-5.
        self.assertIn("static_assert(kAmpNormEps > 0.0", text)
        self.assertIn("static_assert(kAmpNormEps == 1e-5", text)


if __name__ == "__main__":
    unittest.main()
