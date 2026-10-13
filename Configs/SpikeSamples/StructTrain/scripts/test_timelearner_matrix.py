import importlib.util
import json
import os
import tempfile
from threading import Barrier, Lock
import unittest
from pathlib import Path
from unittest.mock import patch

from posttune_verify import compare_run_inputs
from repro_cold_lib import resolve_console


SCRIPT = Path(__file__).with_name("timelearner_matrix.py")
SPEC = importlib.util.spec_from_file_location("timelearner_matrix_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class QuietDebugLoggingTests(unittest.TestCase):
    def test_only_project_wide_debug_flag_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_ini = Path(temporary) / "Project.ini"
            project_ini.write_text(
                "<Project><MultiGeneral><DebugModeFlag>1</DebugModeFlag>"
                "</MultiGeneral><Channels><00><DebugModeFlag>0</DebugModeFlag>"
                "</00></Channels></Project>",
                encoding="utf-8",
            )

            result = MODULE.set_project_debug_logging(project_ini, enabled=False)
            updated = project_ini.read_text(encoding="utf-8")

        self.assertEqual(result["debug_logging"], "0")
        self.assertNotEqual(result["sha256_before"], result["sha256_after"])
        self.assertIn("<MultiGeneral><DebugModeFlag>0</DebugModeFlag>", updated)
        self.assertIn("<Channels><00><DebugModeFlag>0</DebugModeFlag>", updated)

    def test_missing_multigeneral_debug_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_ini = Path(temporary) / "Project.ini"
            project_ini.write_text("<Project><MultiGeneral /></Project>", encoding="utf-8")

            with self.assertRaises(ValueError):
                MODULE.set_project_debug_logging(project_ini, enabled=False)


class TrainingLimitOverrideTests(unittest.TestCase):
    def test_default_and_diagnostic_override_are_resolved(self):
        spec = {"template": "t", "train_t": 640}
        templates = {"t": {"train_t": 800}}
        self.assertEqual(
            MODULE.effective_train_time_limit_seconds(spec, templates, {"runtime": {}}),
            640,
        )
        self.assertEqual(
            MODULE.effective_train_time_limit_seconds(
                spec, templates, {"runtime": {"train_time_limit_override_seconds": 1200}}
            ),
            1200,
        )

    def test_invalid_override_is_rejected(self):
        spec = {"template": "t", "train_t": 640}
        templates = {"t": {"train_t": 800}}
        for value in (0, -1, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MODULE.effective_train_time_limit_seconds(
                    spec, templates, {"runtime": {"train_time_limit_override_seconds": value}}
                )


class ReportPathTests(unittest.TestCase):
    def test_checkout_paths_are_relative_and_external_paths_are_absolute(self):
        with tempfile.TemporaryDirectory() as temporary:
            old_base = MODULE.BASE
            try:
                MODULE.BASE = Path(temporary) / "repo"
                inside = MODULE.BASE / "Bin" / "result.json"
                outside = Path(temporary) / "archive" / "result.json"
                self.assertEqual(MODULE.report_path(inside), str(Path("Bin") / "result.json"))
                self.assertEqual(MODULE.report_path(outside), str(outside.resolve()))
            finally:
                MODULE.BASE = old_base


class RuntimeBranchGammaOverlayTests(unittest.TestCase):
    def test_per_input_gamma_overlay_is_isolated_and_train_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            xml = '<Params><AttenuationGamma Type="d">0.11</AttenuationGamma></Params>'
            for filename in ("Model_00.xml", "Parameters_00.xml"):
                (source / "Train" / filename).write_text(xml, encoding="utf-8")
            (source / "Test" / "Model_00.xml").write_text(xml, encoding="utf-8")
            attempt = base / "runs" / "r1" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            overlay, record = MODULE.make_runtime_input_overlay(
                source, attempt, "W04", "case",
                quiet_debug_logs=False, branch_gamma_mode="per-input-auto",
            )

            self.assertEqual((source / "Train" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            self.assertIn("<AutoEstimateAttenuationGamma", (overlay / "Train" / "Model_00.xml").read_text(encoding="utf-8"))
            self.assertIn("<UsePerInputAttenuationGamma", (overlay / "Train" / "Model_00.xml").read_text(encoding="utf-8"))
            self.assertEqual((overlay / "Test" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            self.assertEqual(record["branch_gamma_mode"], "per-input-auto")
            self.assertEqual(len(record["overrides"]), 2)

    def test_fixed_gamma_overlay_disables_auto_and_per_input_modes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            for filename in ("Model_00.xml", "Parameters_00.xml"):
                (source / "Train" / filename).write_text(
                    '<Params><AttenuationGamma Type="d">0.11</AttenuationGamma></Params>',
                    encoding="utf-8",
                )
            attempt = base / "runs" / "r2" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            overlay, _ = MODULE.make_runtime_input_overlay(
                source, attempt, "W04", "case",
                quiet_debug_logs=False, branch_gamma_mode="shared-fixed-005",
            )

            xml = (overlay / "Train" / "Parameters_00.xml").read_text(encoding="utf-8")
            self.assertIn(">0.05</AttenuationGamma>", xml)
            self.assertIn(">0</AutoEstimateAttenuationGamma>", xml)
            self.assertIn(">0</UsePerInputAttenuationGamma>", xml)


class RunProvenanceTests(unittest.TestCase):
    def test_console_resolution_uses_host_platform_and_respects_override(self):
        root = Path("/repo")
        if os.name == "nt":
            expected = root / "Bin/Platform/Win/NeuroModelerConsole.exe"
        else:
            expected = root / "Bin/Platform/Linux/NeuroModelerConsole"
        self.assertEqual(resolve_console(root, env={}), expected)
        self.assertEqual(resolve_console(root, env={"NMSDK_CONSOLE": "custom/Console"}), Path("custom/Console"))

    def test_expected_train_output_change_is_allowed_but_test_input_change_is_not(self):
        provenance = {
            "config_sha256_before": {
                "Train/Parameters_00.xml": "train-before",
                "Train/Model_00.xml": "model-before",
                "Test/Parameters_00.xml": "test-params",
                "Test/Model_00.xml": "test-model",
            },
            "config_sha256_after": {
                "Train/Parameters_00.xml": "train-after",
                "Train/Model_00.xml": "model-after",
                "Test/Parameters_00.xml": "test-params",
                "Test/Model_00.xml": "test-model",
            },
        }
        self.assertTrue(MODULE.test_config_hashes_unchanged(provenance))
        provenance["config_sha256_after"]["Test/Model_00.xml"] = "changed-test-model"
        self.assertFalse(MODULE.test_config_hashes_unchanged(provenance))

    def test_launch_hashes_detect_source_or_binary_changes(self):
        before = {
            "source_sha256_at_launch": {"trainer.cpp": "source-a"},
            "binary_sha256_at_launch": "console-a",
        }
        unchanged = compare_run_inputs(
            before,
            source_sha_after={"trainer.cpp": "source-a"},
            binary_sha_after="console-a",
            config_sha_before={"Train/Parameters_00.xml": "input-a"},
            config_sha_after={"Train/Parameters_00.xml": "input-b"},
        )
        self.assertFalse(unchanged["source_changed_during_run"])
        self.assertFalse(unchanged["binary_changed_during_run"])
        self.assertTrue(unchanged["training_config_changed_during_run"])
        self.assertTrue(unchanged["inputs_mutated_during_run"])

        changed = compare_run_inputs(
            before,
            source_sha_after={"trainer.cpp": "source-b"},
            binary_sha_after="console-b",
            config_sha_before={"Train/Parameters_00.xml": "input-a"},
            config_sha_after={"Train/Parameters_00.xml": "input-a"},
        )
        self.assertTrue(changed["source_changed_during_run"])
        self.assertTrue(changed["binary_changed_during_run"])
        self.assertFalse(changed["training_config_changed_during_run"])
        self.assertTrue(changed["inputs_mutated_during_run"])


class IsolatedAttemptDispatchTests(unittest.TestCase):
    def test_worker_accepts_queue_log_but_rejects_preexisting_attempt_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempt = Path(temporary) / "attempt-0001"
            attempt.mkdir()
            (attempt / "worker.log").write_text("queue-owned log\n", encoding="utf-8")
            MODULE.validate_worker_attempt_directory(attempt)
            (attempt / "stale-result.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "pre-existing artifacts"):
                MODULE.validate_worker_attempt_directory(attempt)

    def test_parallel_stub_workers_and_stale_resume_never_overwrite_attempts(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "StructTrain"
            matrix = base / "TimeLearnerMatrix"
            cases = ["C1", "C2"]
            specs = [
                {
                    "id": case_id, "wave": "W01", "template": "T",
                    "duration_ms": 50, "normalization_mode": 0,
                    "presynaptic_inhibition": False,
                }
                for case_id in cases
            ]
            (matrix / "W01").mkdir(parents=True)
            matrix_definition = matrix / "matrix.json"
            matrix_definition.write_text(json.dumps({"schema": 1, "templates": {"T": {}}, "cases": specs}), encoding="utf-8")

            inputs = {}
            for case_id in cases:
                input_root = matrix / "W01" / "inputs" / case_id
                file_entries = []
                for side in ("Train", "Test"):
                    side_dir = input_root / side
                    side_dir.mkdir(parents=True)
                    for name in ("Parameters_00.xml", "Model_00.xml"):
                        path = side_dir / name
                        path.write_text(f"{case_id}-{side}-{name}\n", encoding="utf-8")
                        file_entries.append({"side": side, "file": name, "sha256": MODULE.sha256(path)})
                manifest_path = input_root / "matrix_input_manifest.json"
                manifest_path.write_text(json.dumps({"source_files": file_entries}) + "\n", encoding="utf-8")
                inputs[case_id] = MODULE.sha256(manifest_path)

            run_id = "stub-run"
            run_root = base / "_repro" / "TimeLearnerMatrixRuns" / run_id
            run_root.mkdir(parents=True)
            run_manifest = {
                "run_id": run_id,
                "run_fingerprint": "run-fingerprint",
                "selected_cases": cases,
                "case_fingerprints": {case_id: f"fingerprint-{case_id}" for case_id in cases},
                "input_manifest_sha256": inputs,
                "binary_sha256": "console-sha",
                "root_git": "root-sha",
                "gitlinks": {"Libraries/Nmsdk-PulseLib": "pulse-sha", "Rdk": "rdk-sha"},
                "source_sha256": {"trainer.cpp": "source-sha"},
                "launcher_sha256": {"runner.py": "launcher-sha"},
            }
            (run_root / "run_manifest.json").write_text(json.dumps(run_manifest), encoding="utf-8")

            old_base, old_manifest, old_runs = MODULE.BASE, MODULE.MANIFEST, MODULE.RUNS_BASE
            old_run_id = os.environ.get("TIMELEARNER_MATRIX_RUN_ID")
            MODULE.BASE = base
            MODULE.MANIFEST = matrix_definition
            MODULE.RUNS_BASE = base / "_repro" / "TimeLearnerMatrixRuns"
            os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id
            calls = []
            calls_lock = Lock()
            parallel_barrier = Barrier(2)

            def stub_worker(command, *, cwd, env, log_path):
                case_id = command[-1]
                with calls_lock:
                    calls.append(case_id)
                    call_number = len(calls)
                if call_number <= 2:
                    parallel_barrier.wait(timeout=5)
                attempt_dir = Path(env["TIMELEARNER_MATRIX_ATTEMPT_DIR"])
                (attempt_dir / "case.marker").write_text(case_id, encoding="utf-8")
                log_path.write_text(f"stub worker {case_id}\n", encoding="utf-8")
                config_before = {
                    "Train/Parameters_00.xml": "train-before",
                    "Train/Model_00.xml": "model-before",
                    "Test/Parameters_00.xml": f"{case_id}-test-params",
                    "Test/Model_00.xml": f"{case_id}-test-model",
                }
                config_after = {
                    "Train/Parameters_00.xml": "train-after",
                    "Train/Model_00.xml": "model-after",
                    "Test/Parameters_00.xml": f"{case_id}-test-params",
                    "Test/Model_00.xml": f"{case_id}-test-model",
                }
                provenance = {
                    "root_git": "root-sha", "root_git_at_launch": "root-sha",
                    "gitlinks": run_manifest["gitlinks"],
                    "gitlinks_at_launch": run_manifest["gitlinks"],
                    "binary_sha256": "console-sha", "binary_sha256_at_launch": "console-sha",
                    "binary_sha256_after": "console-sha",
                    "source_sha256": run_manifest["source_sha256"],
                    "source_sha256_at_launch": run_manifest["source_sha256"],
                    "source_sha256_after": run_manifest["source_sha256"],
                    "source_changed_during_run": False, "binary_changed_during_run": False,
                    "training_config_changed_during_run": True, "inputs_mutated_during_run": True,
                    "config_sha256_before": config_before, "config_sha256_after": config_after,
                }
                (attempt_dir / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
                MODULE.atomic_write_json(attempt_dir / "matrix_result.json", {
                    "case": case_id,
                    "matrix_run_id": run_id,
                    "matrix_run_fingerprint": run_manifest["run_fingerprint"],
                    "case_fingerprint": run_manifest["case_fingerprints"][case_id],
                    "matrix_launcher_sha256": run_manifest["launcher_sha256"],
                    "input_manifest_sha256": inputs[case_id],
                    "training_convergence": "converged_need_zero",
                    "gate_evaluated": True,
                    "separation_quality": "pass",
                    "detection_quality": "detected",
                    "row_fail": False,
                    "run_provenance": {
                        "root_git": "root-sha", "gitlinks": run_manifest["gitlinks"],
                        "binary_sha256": "console-sha", "binary_sha256_after": "console-sha",
                        "source_sha256": run_manifest["source_sha256"],
                        "source_sha256_after": run_manifest["source_sha256"],
                        "source_changed_during_run": False, "binary_changed_during_run": False,
                    },
                }, replace=False)
                return 0

            def execute_once():
                with (
                    patch.object(MODULE, "execute_worker", side_effect=stub_worker),
                    patch.object(MODULE, "CpuLoadSampler", lambda: type("QuietSampler", (), {"sample": lambda self: 0.0})()),
                    patch.object(MODULE, "active_console_count", return_value=0),
                    patch.object(MODULE, "active_console_pids", return_value=set()),
                    patch.object(MODULE, "logical_cpu_count", return_value=3),
                ):
                    return MODULE.run_wave("W01", 2)

            try:
                first_rc = execute_once()
                self.assertEqual(first_rc, 0)
                self.assertEqual(set(calls), set(cases))
                for case_id in cases:
                    attempt = run_root / "W01" / case_id / "attempt-0001"
                    self.assertEqual((attempt / "case.marker").read_text(encoding="utf-8"), case_id)

                stale_path = run_root / "W01" / "C1" / "attempt-0001" / "matrix_result.json"
                stale_result = json.loads(stale_path.read_text(encoding="utf-8"))
                stale_result["case_fingerprint"] = "stale-fingerprint"
                stale_path.write_text(json.dumps(stale_result), encoding="utf-8")
                self.assertEqual(execute_once(), 0)
                self.assertEqual(calls.count("C1"), 2)
                self.assertEqual(calls.count("C2"), 1)
                self.assertTrue((run_root / "W01" / "C1" / "attempt-0001" / "case.marker").is_file())
                self.assertTrue((run_root / "W01" / "C1" / "attempt-0002" / "case.marker").is_file())
                status = json.loads((run_root / "W01" / "wave_status.json").read_text(encoding="utf-8"))
                self.assertTrue(status["cases"]["C2"]["resumed"])
                self.assertEqual(status["cases"]["C1"]["attempt_id"], "attempt-0002")
            finally:
                MODULE.BASE, MODULE.MANIFEST, MODULE.RUNS_BASE = old_base, old_manifest, old_runs
                if old_run_id is None:
                    os.environ.pop("TIMELEARNER_MATRIX_RUN_ID", None)
                else:
                    os.environ["TIMELEARNER_MATRIX_RUN_ID"] = old_run_id


class PostTuneRunsRootTests(unittest.TestCase):
    def test_worker_workdirs_follow_external_matrix_run_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"TIMELEARNER_MATRIX_RUNS_ROOT": temporary}):
                posttune = MODULE.load_pv()
            self.assertEqual(posttune.RUNS_ROOT, Path(temporary).resolve())


if __name__ == "__main__":
    unittest.main()
