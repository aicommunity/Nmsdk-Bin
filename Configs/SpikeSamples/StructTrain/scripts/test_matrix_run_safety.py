import importlib.util
import hashlib
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from pathlib import Path

from matrix_run_safety import (
    allocate_case_attempt,
    atomic_write_json,
    cpu_percent_from_counters,
    exclusive_file_lock,
    linux_console_pids,
    reserve_run_root,
    resolve_runs_base,
    verify_run_manifest,
)


SCRIPTS = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location(
    "timelearner_matrix_safety_tests", SCRIPTS / "timelearner_matrix.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

QUEUE_SPEC = importlib.util.spec_from_file_location(
    "matrix_queue_safety_tests", SCRIPTS / "run_timelearner_matrix_queue.py"
)
QUEUE = importlib.util.module_from_spec(QUEUE_SPEC)
assert QUEUE_SPEC and QUEUE_SPEC.loader
QUEUE_SPEC.loader.exec_module(QUEUE)


class RunNamespaceSafetyTests(unittest.TestCase):
    def test_runs_root_override_requires_absolute_path_and_is_resolved(self):
        default = Path("relative-default")
        with tempfile.TemporaryDirectory() as temporary:
            configured = str(Path(temporary) / "external" / "runs")
            self.assertEqual(
                resolve_runs_base(default, {"TIMELEARNER_MATRIX_RUNS_ROOT": configured}),
                (Path(configured)).resolve(),
            )
        with self.assertRaisesRegex(ValueError, "must be an absolute path"):
            resolve_runs_base(default, {"TIMELEARNER_MATRIX_RUNS_ROOT": "relative/runs"})
        self.assertEqual(resolve_runs_base(default, {}), default)

    def test_cpu_percentage_uses_idle_and_total_counter_deltas(self):
        self.assertEqual(cpu_percent_from_counters((1000, 200), (1100, 250)), 50.0)
        self.assertEqual(cpu_percent_from_counters((1000, 200), (1100, 100)), 100.0)
        self.assertIsNone(cpu_percent_from_counters((1000, 200), (1000, 210)))

    def test_explicit_parallel_subset_requires_no_commit_and_rejects_bad_ids(self):
        wave = [{"id": "C1"}, {"id": "C2"}, {"id": "C3"}]
        selected, partial = QUEUE.select_wave_cases(wave, ["C1", "C3"], no_commit=True)
        self.assertEqual([case["id"] for case in selected], ["C1", "C3"])
        self.assertTrue(partial)
        with self.assertRaisesRegex(ValueError, "require --no-commit"):
            QUEUE.select_wave_cases(wave, ["C1"], no_commit=False)
        with self.assertRaisesRegex(ValueError, "duplicate IDs"):
            QUEUE.select_wave_cases(wave, ["C1", "C1"], no_commit=True)
        with self.assertRaisesRegex(ValueError, "unknown case"):
            QUEUE.select_wave_cases(wave, ["missing"], no_commit=True)

    def test_run_id_is_reserved_once_and_distinct_ids_are_disjoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = reserve_run_root(root, "case-a")
            second = reserve_run_root(root, "case-b")
            self.assertNotEqual(first, second)
            with self.assertRaises(FileExistsError):
                reserve_run_root(root, "case-a")

    def test_concurrent_same_run_id_has_one_winner_and_case_attempts_do_not_collide(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def reserve_same_id(_):
                try:
                    return reserve_run_root(root / "runs", "shared")
                except FileExistsError:
                    return None
            with ThreadPoolExecutor(max_workers=8) as pool:
                reserved = list(pool.map(reserve_same_id, range(8)))
            self.assertEqual(sum(path is not None for path in reserved), 1)
            case_root = root / "cases" / "one-case"
            with ThreadPoolExecutor(max_workers=8) as pool:
                attempts = list(pool.map(lambda _: allocate_case_attempt(case_root), range(8)))
            self.assertEqual(len({attempt_id for attempt_id, _ in attempts}), 8)
            self.assertEqual(len({path for _, path in attempts}), 8)

    def test_attempts_are_never_reused_and_result_write_is_no_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary) / "run" / "W01" / "case"
            first_id, first = allocate_case_attempt(case_root)
            second_id, second = allocate_case_attempt(case_root)
            self.assertEqual((first_id, second_id), ("attempt-0001", "attempt-0002"))
            self.assertNotEqual(first, second)
            result = first / "matrix_result.json"
            atomic_write_json(result, {"value": 1}, replace=False)
            with self.assertRaises(FileExistsError):
                atomic_write_json(result, {"value": 2}, replace=False)
            self.assertEqual(json.loads(result.read_text(encoding="utf-8")), {"value": 1})

    def test_resume_requires_same_run_id_and_fingerprint(self):
        expected = {"run_fingerprint": "same"}
        verify_run_manifest({"run_id": "run-1", **expected}, expected, "run-1")
        with self.assertRaises(RuntimeError):
            verify_run_manifest({"run_id": "run-1", "run_fingerprint": "old"}, expected, "run-1")
        with self.assertRaises(RuntimeError):
            verify_run_manifest({"run_id": "other", **expected}, expected, "run-1")

    def test_lock_rejects_a_second_owner_and_releases_its_own_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "queue.lock"
            with exclusive_file_lock(lock, purpose="test"):
                self.assertTrue(lock.is_file())
                with self.assertRaises(RuntimeError):
                    with exclusive_file_lock(lock, purpose="second"):
                        pass
            self.assertFalse(lock.exists())

    def test_linux_console_detection_uses_full_cmdline_when_comm_is_truncated(self):
        with tempfile.TemporaryDirectory() as temporary:
            proc_root = Path(temporary)
            console = proc_root / "4321"
            console.mkdir()
            (console / "comm").write_text("NeuroModelerCo\n", encoding="ascii")
            (console / "cmdline").write_bytes(b"/opt/Nmsdk/NeuroModelerConsole\0-c\0Project.ini\0")
            other = proc_root / "9876"
            other.mkdir()
            (other / "comm").write_text("python3\n", encoding="ascii")
            (other / "cmdline").write_bytes(b"/usr/bin/python3\0worker.py\0")
            self.assertEqual(linux_console_pids(proc_root), {4321})

    def test_duplicate_experiment_fingerprint_is_found_across_run_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            old_runs = QUEUE.RUNS_BASE
            try:
                QUEUE.RUNS_BASE = Path(temporary)
                prior = reserve_run_root(QUEUE.RUNS_BASE, "old-run")
                (prior / "run_manifest.json").write_text(json.dumps({
                    "experiment_fingerprint": "same-condition",
                }), encoding="utf-8")
                self.assertEqual(
                    QUEUE.find_duplicate_run({"experiment_fingerprint": "same-condition"}),
                    "old-run",
                )
                self.assertIsNone(
                    QUEUE.find_duplicate_run({"experiment_fingerprint": "different-condition"})
                )
            finally:
                QUEUE.RUNS_BASE = old_runs

    def test_exact_published_result_is_detected_but_stale_provenance_is_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            old_matrix = QUEUE.MATRIX
            try:
                QUEUE.MATRIX = Path(temporary)
                wave_dir = QUEUE.MATRIX / "W01"
                wave_dir.mkdir()
                spec = {"id": "C1", "wave": "W01", "duration_ms": 50}
                fingerprint = {
                    "input_manifest_sha256": {"C1": "input-sha"},
                    "console_sha256": "console-sha",
                    "root_git": "root-sha",
                    "gitlinks": {"Bin": "bin-sha"},
                    "source_sha256": {"trainer.cpp": "source-sha"},
                    "launcher_sha256": {"queue.py": "launcher-sha"},
                    "condition_runtime": {
                        "quiet_debug_logs": False,
                        "max_polls": None,
                        "branch_gamma_mode": None,
                        "branch_rs_rm_limit": None,
                        "train_time_limit_override_seconds": None,
                    },
                }
                report = {
                    "run_id": "run-old",
                    "cases": [{
                        "case": "C1",
                        "factors": spec,
                        "result": {
                            "matrix_run_id": "run-old",
                            "training_convergence": "not_converged_at_stop",
                            "input_manifest_sha256": "input-sha",
                            "matrix_launcher_sha256": {"queue.py": "launcher-sha"},
                            "runtime_execution_options": {
                                "quiet_debug_logs": False,
                                "max_polls": None,
                                "branch_gamma_mode": None,
                                "train_time_limit_override_seconds": None,
                            },
                            "run_provenance": {
                                "binary_sha256": "console-sha",
                                "binary_sha256_after": "console-sha",
                                "root_git": "root-sha",
                                "gitlinks": {"Bin": "bin-sha"},
                                "source_sha256": {"trainer.cpp": "source-sha"},
                                "source_sha256_after": {"trainer.cpp": "source-sha"},
                                "binary_changed_during_run": False,
                                "source_changed_during_run": False,
                                "training_config_changed_during_run": True,
                                "inputs_mutated_during_run": True,
                                "config_sha256_before": {
                                    "Test/Parameters_00.xml": "test-params",
                                    "Test/Model_00.xml": "test-model",
                                },
                                "config_sha256_after": {
                                    "Test/Parameters_00.xml": "test-params",
                                    "Test/Model_00.xml": "test-model",
                                },
                            },
                        },
                    }],
                }
                target = wave_dir / "results.json"
                target.write_text(json.dumps(report), encoding="utf-8")
                self.assertEqual(QUEUE.find_duplicate_result("W01", [spec], fingerprint)["run_id"], "run-old")
                report["cases"][0]["result"].pop("matrix_launcher_sha256")
                target.write_text(json.dumps(report), encoding="utf-8")
                self.assertIsNone(QUEUE.find_duplicate_result("W01", [spec], fingerprint))
                self.assertEqual(QUEUE.find_related_result("W01", [spec], fingerprint)["run_id"], "run-old")
                fingerprint["input_manifest_sha256"]["C1"] = "new-input"
                self.assertIsNone(QUEUE.find_duplicate_result("W01", [spec], fingerprint))
                self.assertIsNone(QUEUE.find_related_result("W01", [spec], fingerprint))
            finally:
                QUEUE.MATRIX = old_matrix

    def test_archived_full_matrix_row_is_reported_as_related_not_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            matrix = Path(temporary)
            diagnostics = matrix / "diagnostics"
            diagnostics.mkdir()
            factors = {
                "template": "historical_branch",
                "trainer": "NNeuronTimeLearnerBranch",
                "duration_ms": 50,
                "pattern_family": "Branch historical",
                "normalization_mode": 1,
                "presynaptic_inhibition": False,
                "presynaptic_coefficient": 0.0,
                "branch_nextseg": False,
                "posttrain_tuning": True,
                "tipr_mode": 1,
                "train_t": 320,
            }
            (diagnostics / "full_matrix_followup_audit_fixture.json").write_text(
                json.dumps({"cases": [{
                    "id": "W10_HIST_br50_gen",
                    "wave": "W10",
                    "factors": factors,
                    "outcome": {
                        "training_convergence": "converged_posttune_finalized",
                        "separation_quality": "pass",
                    },
                    "provenance": {"matrix_run_id": "historical-run"},
                }]}),
                encoding="utf-8",
            )
            expected = {"id": "W10_HIST_br50_gen", "wave": "W10", **factors}
            fingerprint = {}
            old_matrix = QUEUE.MATRIX
            try:
                QUEUE.MATRIX = matrix
                related = QUEUE.find_related_result("W10", [expected], fingerprint)
                mismatched = {**expected, "presynaptic_inhibition": True}
                unrelated = QUEUE.find_related_result("W10", [mismatched], fingerprint)
                wrong_wave = QUEUE.find_related_result("W11", [expected], fingerprint)
                exact = QUEUE.find_duplicate_result("W10", [expected], fingerprint)
            finally:
                QUEUE.MATRIX = old_matrix

            self.assertEqual(related["reason"], "archived_matrix_history_related")
            self.assertEqual(related["run_id"], "historical-run")
            self.assertIsNone(unrelated)
            self.assertIsNone(wrong_wave)
            self.assertIsNone(exact)


class CompletedAttemptProvenanceTests(unittest.TestCase):
    def test_prepared_input_hashes_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            train = root / "Train" / "Parameters.xml"
            test = root / "Test" / "Parameters.xml"
            train.parent.mkdir()
            test.parent.mkdir()
            train.write_text("train\n", encoding="utf-8")
            test.write_text("test\n", encoding="utf-8")
            manifest = {
                "source_files": [
                    {"side": "Train", "file": "Parameters.xml", "sha256": MODULE.sha256(train)},
                    {"side": "Test", "file": "Parameters.xml", "sha256": MODULE.sha256(test)},
                ]
            }
            MODULE.verify_prepared_input_snapshot(root, manifest)
            train.write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                MODULE.verify_prepared_input_snapshot(root, manifest)

    def test_existing_input_snapshot_rejects_matrix_definition_relabel(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            matrix_definition = base / "matrix.json"
            matrix_definition.write_text('{"revision":2}\n', encoding="utf-8")
            destination = base / "TimeLearnerMatrix" / "W01" / "inputs" / "C1"
            (destination / "Train").mkdir(parents=True)
            (destination / "Test").mkdir()
            spec = {"id": "C1", "wave": "W01", "template": "T", "duration_ms": 50}
            manifest = {
                "factors": {k: v for k, v in spec.items() if k not in ("id", "wave")},
                "matrix_definition_sha256": "older-matrix-sha",
                "source_files": [],
            }
            (destination / "matrix_input_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            old_base, old_manifest = MODULE.BASE, MODULE.MANIFEST
            try:
                MODULE.BASE = base
                MODULE.MANIFEST = matrix_definition
                with self.assertRaisesRegex(RuntimeError, "matrix definition differs"):
                    MODULE.prepare_case(spec, {"T": {"preinh_source": "unused"}}, None)
            finally:
                MODULE.BASE, MODULE.MANIFEST = old_base, old_manifest

    def test_existing_input_snapshot_accepts_only_line_ending_checkout_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            matrix_definition = base / "matrix.json"
            matrix_lf = b'{"revision":2}\n'
            matrix_crlf = matrix_lf.replace(b"\n", b"\r\n")
            matrix_definition.write_bytes(matrix_lf)
            destination = base / "TimeLearnerMatrix" / "W01" / "inputs" / "C1"
            (destination / "Train").mkdir(parents=True)
            (destination / "Test").mkdir()
            train = b"train\n"
            test = b"test\n"
            (destination / "Train" / "Parameters.xml").write_bytes(train)
            (destination / "Test" / "Parameters.xml").write_bytes(test)
            manifest = {
                "factors": {"template": "T", "duration_ms": 50},
                "matrix_definition_sha256": hashlib.sha256(matrix_crlf).hexdigest(),
                "source_files": [
                    {
                        "side": "Train",
                        "file": "Parameters.xml",
                        "sha256": hashlib.sha256(train.replace(b"\n", b"\r\n")).hexdigest(),
                    },
                    {
                        "side": "Test",
                        "file": "Parameters.xml",
                        "sha256": hashlib.sha256(test.replace(b"\n", b"\r\n")).hexdigest(),
                    },
                ],
            }
            (destination / "matrix_input_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            old_base, old_manifest = MODULE.BASE, MODULE.MANIFEST
            try:
                MODULE.BASE = base
                MODULE.MANIFEST = matrix_definition
                prepared = MODULE.prepare_case(
                    {"id": "C1", "wave": "W01", "template": "T", "duration_ms": 50},
                    {"T": {"preinh_source": "unused"}},
                    None,
                )
                self.assertEqual(prepared["matrix_definition_sha256"], hashlib.sha256(matrix_crlf).hexdigest())
            finally:
                MODULE.BASE, MODULE.MANIFEST = old_base, old_manifest

    def test_line_ending_compatibility_does_not_accept_input_content_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "Train" / "Parameters.xml"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"changed\n")
            manifest = {
                "source_files": [{
                    "side": "Train",
                    "file": "Parameters.xml",
                    "sha256": hashlib.sha256(b"original\r\n").hexdigest(),
                }]
            }
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                MODULE.verify_prepared_input_snapshot(root, manifest)

    def test_only_complete_matching_provenance_is_reusable(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempt = Path(temporary) / "attempt-0001"
            attempt.mkdir()
            manifest = {
                "run_id": "run-a",
                "run_fingerprint": "run-fp",
                "case_fingerprints": {"case-a": "case-fp"},
                "binary_sha256": "console-sha",
                "root_git": "root-sha",
                "gitlinks": {"Bin": "bin-sha"},
                "source_sha256": {"trainer.cpp": "source-sha"},
                "launcher_sha256": {"queue.py": "launcher-sha"},
            }
            input_sha = "input-sha"
            config_before = {
                "Train/Parameters_00.xml": "train-before",
                "Train/Model_00.xml": "model-before",
                "Test/Parameters_00.xml": "test-params-before",
                "Test/Model_00.xml": "test-model-before",
            }
            config_after = {
                "Train/Parameters_00.xml": "train-after",
                "Train/Model_00.xml": "model-after",
                "Test/Parameters_00.xml": "test-params-after",
                "Test/Model_00.xml": "test-model-after",
            }
            (attempt / "inputs_manifest.json").write_text(json.dumps({
                "copied": [
                    {"side": "Test", "rel": "Parameters_00.xml", "sha256": "test-params-before"},
                    {"side": "Test", "rel": "Model_00.xml", "sha256": "test-model-before"},
                ],
            }), encoding="utf-8")
            result = {
                "case": "case-a",
                "matrix_run_id": "run-a",
                "matrix_run_fingerprint": "run-fp",
                "case_fingerprint": "case-fp",
                "matrix_launcher_sha256": {"queue.py": "launcher-sha"},
                "input_manifest_sha256": input_sha,
                "run_provenance": {
                    "binary_sha256": "console-sha",
                    "binary_sha256_after": "console-sha",
                    "root_git": "root-sha",
                    "gitlinks": {"Bin": "bin-sha"},
                    "source_sha256": {"trainer.cpp": "source-sha"},
                    "source_sha256_after": {"trainer.cpp": "source-sha"},
                    "source_changed_during_run": False,
                    "binary_changed_during_run": False,
                    "training_config_changed_during_run": True,
                    "inputs_mutated_during_run": True,
                    "config_sha256_before": config_before,
                    "config_sha256_after": config_after,
                },
            }
            (attempt / "matrix_result.json").write_text(json.dumps(result), encoding="utf-8")
            (attempt / "provenance.json").write_text(json.dumps({
                "binary_sha256_at_launch": "console-sha",
                "binary_sha256_after": "console-sha",
                "root_git": "root-sha",
                "root_git_at_launch": "root-sha",
                "gitlinks_at_launch": {"Bin": "bin-sha"},
                "source_sha256_at_launch": {"trainer.cpp": "source-sha"},
                "source_sha256_after": {"trainer.cpp": "source-sha"},
                "source_changed_during_run": False,
                "binary_changed_during_run": False,
                "training_config_changed_during_run": True,
                "inputs_mutated_during_run": True,
                "config_sha256_before": config_before,
                "config_sha256_after": config_after,
            }), encoding="utf-8")
            provenance = json.loads((attempt / "provenance.json").read_text(encoding="utf-8"))
            found = MODULE.case_attempt_result(
                attempt.parent,
                case_id="case-a",
                run_manifest=manifest,
                input_manifest_sha256=input_sha,
            )
            self.assertIsNotNone(found)

            input_manifest_record = json.loads((attempt / "inputs_manifest.json").read_text(encoding="utf-8"))
            input_manifest_record["copied"][0]["sha256"] = "changed-test-params"
            (attempt / "inputs_manifest.json").write_text(json.dumps(input_manifest_record), encoding="utf-8")
            self.assertIsNone(MODULE.case_attempt_result(
                attempt.parent, case_id="case-a", run_manifest=manifest,
                input_manifest_sha256=input_sha,
            ))
            input_manifest_record["copied"][0]["sha256"] = "test-params-before"
            (attempt / "inputs_manifest.json").write_text(json.dumps(input_manifest_record), encoding="utf-8")

            provenance["config_sha256_after"]["Test/Model_00.xml"] = "mutated-test-model"
            (attempt / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
            self.assertIsNone(MODULE.case_attempt_result(
                attempt.parent, case_id="case-a", run_manifest=manifest,
                input_manifest_sha256=input_sha,
            ))
            provenance["config_sha256_after"]["Test/Model_00.xml"] = "test-model-after"
            (attempt / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")

            result["case_fingerprint"] = "stale-case-fp"
            (attempt / "matrix_result.json").write_text(json.dumps(result), encoding="utf-8")
            stale = MODULE.case_attempt_result(
                attempt.parent,
                case_id="case-a",
                run_manifest=manifest,
                input_manifest_sha256=input_sha,
            )
            self.assertIsNone(stale)

    def test_wave_resume_skips_valid_saved_result_without_launching_console(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / "StructTrain"
            matrix = base / "TimeLearnerMatrix"
            case_input = matrix / "W01" / "inputs" / "C1"
            case_input.mkdir(parents=True)
            input_manifest = case_input / "matrix_input_manifest.json"
            train_input = case_input / "Train" / "fixture.xml"
            test_input = case_input / "Test" / "fixture.xml"
            train_input.parent.mkdir(parents=True)
            test_input.parent.mkdir(parents=True)
            train_input.write_text("train-input\n", encoding="utf-8")
            test_input.write_text("test-input\n", encoding="utf-8")
            input_manifest.write_text(json.dumps({
                "source_files": [
                    {"side": "Train", "file": "fixture.xml", "sha256": MODULE.sha256(train_input)},
                    {"side": "Test", "file": "fixture.xml", "sha256": MODULE.sha256(test_input)},
                ],
            }) + "\n", encoding="utf-8")
            matrix_manifest = {
                "schema": 1,
                "templates": {"T": {"train_t": 1.0, "kind": "classic"}},
                "cases": [{
                    "id": "C1", "wave": "W01", "template": "T",
                    "duration_ms": 50, "normalization_mode": 0,
                    "presynaptic_inhibition": False,
                }],
            }
            manifest_path = matrix / "matrix.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(matrix_manifest), encoding="utf-8")
            run_id = "run-resume"
            run_root = base / "_repro" / "TimeLearnerMatrixRuns" / run_id
            attempt = run_root / "W01" / "C1" / "attempt-0001"
            attempt.mkdir(parents=True)
            (attempt / "inputs_manifest.json").write_text(json.dumps({
                "copied": [
                    {"side": "Test", "rel": "Parameters_00.xml", "sha256": "test-params"},
                    {"side": "Test", "rel": "Model_00.xml", "sha256": "test-model"},
                ],
            }), encoding="utf-8")
            input_sha = MODULE.sha256(input_manifest)
            run_manifest = {
                "run_id": run_id,
                "run_fingerprint": "run-fp",
                "selected_cases": ["C1"],
                "case_fingerprints": {"C1": "case-fp"},
                "input_manifest_sha256": {"C1": input_sha},
                "binary_sha256": "console-sha",
                "root_git": "root-sha",
                "gitlinks": {"Bin": "bin-sha"},
                "source_sha256": {"trainer.cpp": "source-sha"},
                "launcher_sha256": {"queue.py": "launcher-sha"},
            }
            (run_root / "run_manifest.json").write_text(json.dumps(run_manifest), encoding="utf-8")
            (attempt / "matrix_result.json").write_text(json.dumps({
                "case": "C1", "matrix_run_id": run_id,
                "matrix_run_fingerprint": "run-fp", "case_fingerprint": "case-fp",
                "matrix_launcher_sha256": {"queue.py": "launcher-sha"},
                "input_manifest_sha256": input_sha,
                "training_convergence": "converged_need_zero",
                "gate_evaluated": True, "separation_quality": "pass",
                "detection_quality": "detected", "row_fail": False,
                "run_provenance": {
                    "binary_sha256": "console-sha", "root_git": "root-sha",
                    "binary_sha256_after": "console-sha", "gitlinks": {"Bin": "bin-sha"},
                    "source_sha256": {"trainer.cpp": "source-sha"},
                    "source_sha256_after": {"trainer.cpp": "source-sha"},
                    "source_changed_during_run": False, "binary_changed_during_run": False,
                    "training_config_changed_during_run": False, "inputs_mutated_during_run": False,
                    "config_sha256_before": {
                        "Test/Parameters_00.xml": "test-params",
                        "Test/Model_00.xml": "test-model",
                    },
                    "config_sha256_after": {
                        "Test/Parameters_00.xml": "test-params",
                        "Test/Model_00.xml": "test-model",
                    },
                },
            }), encoding="utf-8")
            (attempt / "provenance.json").write_text(json.dumps({
                "binary_sha256_at_launch": "console-sha", "root_git": "root-sha",
                "binary_sha256_after": "console-sha", "root_git_at_launch": "root-sha",
                "gitlinks_at_launch": {"Bin": "bin-sha"},
                "source_sha256_at_launch": {"trainer.cpp": "source-sha"},
                "source_sha256_after": {"trainer.cpp": "source-sha"},
                "source_changed_during_run": False, "binary_changed_during_run": False,
                "training_config_changed_during_run": False, "inputs_mutated_during_run": False,
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
            }), encoding="utf-8")

            old_base = MODULE.BASE
            old_manifest = MODULE.MANIFEST
            old_runs = MODULE.RUNS_BASE
            old_run_id = os.environ.get("TIMELEARNER_MATRIX_RUN_ID")
            try:
                MODULE.BASE = base
                MODULE.MANIFEST = manifest_path
                MODULE.RUNS_BASE = base / "_repro" / "TimeLearnerMatrixRuns"
                os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id
                rc = MODULE.run_wave("W01", 1)
            finally:
                MODULE.BASE = old_base
                MODULE.MANIFEST = old_manifest
                MODULE.RUNS_BASE = old_runs
                if old_run_id is None:
                    os.environ.pop("TIMELEARNER_MATRIX_RUN_ID", None)
                else:
                    os.environ["TIMELEARNER_MATRIX_RUN_ID"] = old_run_id

            self.assertEqual(rc, 0)
            self.assertEqual(sorted(path.name for path in (run_root / "W01" / "C1").iterdir()), ["attempt-0001"])
            status = json.loads((run_root / "W01" / "wave_status.json").read_text(encoding="utf-8"))
            self.assertTrue(status["cases"]["C1"]["resumed"])
            self.assertEqual(status["cases"]["C1"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
