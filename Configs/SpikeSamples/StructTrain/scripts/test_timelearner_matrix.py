import concurrent.futures
import importlib.util
import json
import os
import re
import tempfile
from threading import Barrier, Lock
import unittest
from pathlib import Path
from unittest.mock import patch

from posttune_verify import compare_run_inputs, snapshot_prelaunch_train_configs
from repro_cold_lib import apply_branch_segment_rm_profile_to_train, resolve_console
from matrix_run_safety import (
    allocate_case_attempt,
    atomic_write_json,
    exclusive_file_lock,
    reserve_run_root,
    verify_run_manifest,
)


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


class InitialRsOverrideTests(unittest.TestCase):
    def test_validates_train_inputs_and_returns_value_to_reapply_after_softcold(self):
        with tempfile.TemporaryDirectory() as temporary:
            train = Path(temporary) / "Train"
            train.mkdir()
            xml = (
                "<Root><SynapseResistanceBase>10000000</SynapseResistanceBase>"
                "<TipSynapseResistance>10000000 10000000 10000000 10000000"
                "</TipSynapseResistance></Root>"
            )
            for name in ("Parameters_00.xml", "Model_00.xml"):
                (train / name).write_text(xml, encoding="utf-8")

            value = MODULE.initial_rs_override_from_input(
                {"normalization_mode": 1, "initial_rs_to_rm": 1.0}, Path(temporary)
            )

        self.assertEqual(value, 10_000_000.0)

    def test_rejects_model_parameters_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            train = Path(temporary) / "Train"
            train.mkdir()
            consistent = (
                "<Root><SynapseResistanceBase>10000000</SynapseResistanceBase>"
                "<TipSynapseResistance>10000000 10000000 10000000 10000000"
                "</TipSynapseResistance></Root>"
            )
            mismatched = consistent.replace("10000000", "86000000")
            (train / "Parameters_00.xml").write_text(consistent, encoding="utf-8")
            (train / "Model_00.xml").write_text(mismatched, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "disagree on initial Rs"):
                MODULE.initial_rs_override_from_input(
                    {"normalization_mode": 1, "initial_rs_to_rm": 1.0}, Path(temporary)
                )

    def test_no_override_without_initial_rs_factor(self):
        self.assertIsNone(MODULE.initial_rs_override_from_input({}, Path("missing")))


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


class RuntimeClassicGammaOverlayTests(unittest.TestCase):
    def test_fixed_shared_gamma_overlay_is_train_only_and_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            xml = '<Params><AttenuationGamma Type="d">0.141</AttenuationGamma></Params>'
            for filename in ("Model_00.xml", "Parameters_00.xml"):
                (source / "Train" / filename).write_text(xml, encoding="utf-8")
            (source / "Test" / "Model_00.xml").write_text(xml, encoding="utf-8")
            attempt = base / "runs" / "r1" / "W01" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            overlay, record = MODULE.make_runtime_input_overlay(
                source, attempt, "W01", "case",
                quiet_debug_logs=False, branch_gamma_mode=None,
                classic_gamma_mode="shared-fixed-005",
            )

            train_xml = (overlay / "Train" / "Parameters_00.xml").read_text(encoding="utf-8")
            self.assertIn(">0.05</AttenuationGamma>", train_xml)
            self.assertIn(">0</AutoEstimateAttenuationGamma>", train_xml)
            self.assertEqual((overlay / "Test" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            self.assertEqual((source / "Train" / "Parameters_00.xml").read_text(encoding="utf-8"), xml)
            self.assertEqual(record["classic_gamma_mode"], "shared-fixed-005")
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


class RuntimeBranchRsRmOverlayTests(unittest.TestCase):
    def test_segment_rm_profile_changes_only_selected_train_membrane_channels(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            state = (
                '<DendriteLength Type="simplevector">1 1 1 1</DendriteLength>'
                '<InitialSomaPotential Type="simplevector">0.1 0.2 0.3 0.4</InitialSomaPotential>'
                '<TipSynapseResistance Type="simplevector">20000000 30000000 40000000 86000000</TipSynapseResistance>'
                '<LTZThreshold Type="d">0.11358</LTZThreshold>'
                '<FixedLTZThreshold Type="d">0.11358</FixedLTZThreshold>'
                '<UseFixedLTZThreshold Type="b">1</UseFixedLTZThreshold>'
                '<IsNeedToTrain Type="b">1</IsNeedToTrain>'
                '<StructureBuildMode Type="i">2</StructureBuildMode>'
            )
            xml = (
                f'<Root>{state}<Neuron><Dendrite1_65 Class="Membrane"><Components>'
                '<ExcChannel><Parameters><Resistance>10000000</Resistance>'
                '<FBResistance>10000000</FBResistance><RestingResistance>10000000</RestingResistance>'
                '</Parameters></ExcChannel><InhChannel><Parameters><Resistance>10000000</Resistance>'
                '<FBResistance>10000000</FBResistance><RestingResistance>10000000</RestingResistance>'
                '</Parameters></InhChannel></Components></Dendrite1_65></Neuron></Root>'
            )
            (source / "Train" / "Model_00.xml").write_text(xml, encoding="utf-8")
            (source / "Train" / "Parameters_00.xml").write_text(f"<Parameters>{state}{xml}</Parameters>", encoding="utf-8")
            (source / "Test" / "Model_00.xml").write_text(xml, encoding="utf-8")
            attempt = base / "runs" / "r5" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            profile = MODULE.parse_branch_segment_rm_profile("65=5000000")
            overlay, record = MODULE.make_runtime_input_overlay(
                source, attempt, "W04", "case",
                quiet_debug_logs=False, branch_gamma_mode=None,
                branch_segment_rm_profile=profile,
                branch_initial_lengths=MODULE.parse_branch_initial_lengths("1,65,1,1"),
            )

            trained = (overlay / "Train" / "Model_00.xml").read_text(encoding="utf-8")
            self.assertIn("<Resistance>5000000</Resistance>", trained)
            self.assertIn("<FBResistance>5000000</FBResistance>", trained)
            self.assertIn("<RestingResistance>5000000</RestingResistance>", trained)
            self.assertIn("<DendriteLength Type=\"simplevector\">1 65 1 1</DendriteLength>", trained)
            self.assertIn(
                '<InitialSomaPotential Type="simplevector">0.1 0.2 0.3 0.4</InitialSomaPotential>',
                trained,
            )
            self.assertIn(
                '<TipSynapseResistance Type="simplevector">20000000 30000000 40000000 86000000</TipSynapseResistance>',
                trained,
            )
            self.assertIn('<LTZThreshold Type="d">0.11358</LTZThreshold>', trained)
            self.assertIn('<FixedLTZThreshold Type="d">0.11358</FixedLTZThreshold>', trained)
            self.assertIn('<UseFixedLTZThreshold Type="b">1</UseFixedLTZThreshold>', trained)
            self.assertRegex(trained, r'<ResetToUntrainedState\b[^>]*>0</ResetToUntrainedState>')
            self.assertIn("<IsNeedToTrain Type=\"b\">1</IsNeedToTrain>", trained)
            parameters = (overlay / "Train" / "Parameters_00.xml").read_text(encoding="utf-8")
            self.assertIn("<DendriteLength Type=\"simplevector\">1 65 1 1</DendriteLength>", parameters)
            self.assertIn("<Resistance>5000000</Resistance>", parameters)
            self.assertRegex(parameters, r'<ResetToUntrainedState\b[^>]*>0</ResetToUntrainedState>')
            self.assertEqual((overlay / "Test" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            self.assertEqual((source / "Train" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            self.assertEqual(record["branch_segment_rm_profile"], {65: 5000000.0})
            self.assertEqual(record["branch_initial_lengths"], [1, 65, 1, 1])
            self.assertEqual(len(record["overrides"]), 4)

    def test_segment_rm_profile_requires_prebuilt_lengths(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            attempt = base / "runs" / "r6" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "prebuilt initial lengths"):
                MODULE.make_runtime_input_overlay(
                    source, attempt, "W04", "case",
                    quiet_debug_logs=False, branch_gamma_mode=None,
                    branch_segment_rm_profile={65: 5000000.0},
                )
            self.assertFalse((attempt / "runtime-input-overrides").exists())

    def test_segment_one_rm_profile_keeps_standard_softcold_reset_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            state = (
                '<DendriteLength Type="simplevector">97 50 25 1</DendriteLength>'
                '<InitialSomaPotential Type="simplevector">0.1 0.2 0.3 0.4</InitialSomaPotential>'
                '<TipSynapseResistance Type="simplevector">20000000 30000000 40000000 86000000</TipSynapseResistance>'
            )
            model = (
                f'<Root>{state}<Neuron><Dendrite1_1 Class="Membrane"><Components>'
                '<ExcChannel><Parameters><Resistance>10000000</Resistance>'
                '<FBResistance>10000000</FBResistance><RestingResistance>10000000</RestingResistance>'
                '</Parameters></ExcChannel><InhChannel><Parameters><Resistance>10000000</Resistance>'
                '<FBResistance>10000000</FBResistance><RestingResistance>10000000</RestingResistance>'
                '</Parameters></InhChannel></Components></Dendrite1_1></Neuron></Root>'
            )
            (source / "Train" / "Model_00.xml").write_text(model, encoding="utf-8")
            (source / "Train" / "Parameters_00.xml").write_text(f"<Parameters>{state}{model}</Parameters>", encoding="utf-8")
            (source / "Test" / "Model_00.xml").write_text(model, encoding="utf-8")
            attempt = base / "runs" / "r7" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            overlay, record = MODULE.make_runtime_input_overlay(
                source, attempt, "W04", "case",
                quiet_debug_logs=False, branch_gamma_mode=None,
                branch_segment_rm_profile={1: 5000000.0},
            )

            trained = (overlay / "Train" / "Model_00.xml").read_text(encoding="utf-8")
            self.assertIn("<Resistance>5000000</Resistance>", trained)
            self.assertIn("<DendriteLength Type=\"simplevector\">97 50 25 1</DendriteLength>", trained)
            self.assertIn(
                '<InitialSomaPotential Type="simplevector">0.1 0.2 0.3 0.4</InitialSomaPotential>',
                trained,
            )
            self.assertIn(
                '<TipSynapseResistance Type="simplevector">20000000 30000000 40000000 86000000</TipSynapseResistance>',
                trained,
            )
            parameters = (overlay / "Train" / "Parameters_00.xml").read_text(encoding="utf-8")
            self.assertIn("<Resistance>5000000</Resistance>", parameters)
            self.assertIsNone(record["branch_initial_lengths"])
            self.assertEqual(record["branch_segment_rm_profile"], {1: 5000000.0})
            self.assertEqual((source / "Train" / "Model_00.xml").read_text(encoding="utf-8"), model)

    def test_post_softcold_rm_profile_updates_both_train_xmls(self):
        with tempfile.TemporaryDirectory() as temporary:
            train = Path(temporary) / "Train"
            train.mkdir()
            segment = (
                '<Dendrite1_1 Class="Membrane"><ExcChannel><Resistance>10000000</Resistance>'
                '<FBResistance>10000000</FBResistance><RestingResistance>10000000</RestingResistance>'
                '</ExcChannel><InhChannel><Resistance>10000000</Resistance>'
                '<FBResistance>10000000</FBResistance><RestingResistance>10000000</RestingResistance>'
                '</InhChannel></Dendrite1_1>'
            )
            for name in ("Model_00.xml", "Parameters_00.xml"):
                (train / name).write_text(
                    '<Root><ResetToUntrainedState Type="b">1</ResetToUntrainedState>'
                    '<StructureBuildMode Type="i">1</StructureBuildMode>'
                    f'{segment}<Neuron><StructureBuildMode Type="i">2</StructureBuildMode></Neuron></Root>',
                    encoding="utf-8",
                )

            updated = apply_branch_segment_rm_profile_to_train(train, {1: 5000000.0})

            self.assertEqual(updated, ["Model_00.xml", "Parameters_00.xml"])
            for name in ("Model_00.xml", "Parameters_00.xml"):
                text = (train / name).read_text(encoding="utf-8")
                self.assertEqual(text.count("<Resistance>5000000</Resistance>"), 2)
                self.assertEqual(text.count("<FBResistance>5000000</FBResistance>"), 2)
                self.assertEqual(text.count("<RestingResistance>5000000</RestingResistance>"), 2)
                self.assertRegex(text, r'<ResetToUntrainedState\b[^>]*>0</ResetToUntrainedState>')
                self.assertEqual(
                    re.findall(r'<StructureBuildMode\b[^>]*>(.*?)</StructureBuildMode>', text),
                    ["2", "2"],
                )

    def test_prelaunch_snapshot_validates_live_profile_and_preserves_xml(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            train = base / "Train"
            train.mkdir()
            channel = (
                '<ExcChannel><Resistance>5000000</Resistance><FBResistance>5000000</FBResistance>'
                '<RestingResistance>5000000</RestingResistance></ExcChannel>'
                '<InhChannel><Resistance>5000000</Resistance><FBResistance>5000000</FBResistance>'
                '<RestingResistance>5000000</RestingResistance></InhChannel>'
            )
            xml = (
                '<Root><ResetToUntrainedState Type="b">0</ResetToUntrainedState>'
                '<StructureBuildMode Type="i">2</StructureBuildMode>'
                f'<Neuron><StructureBuildMode Type="i">2</StructureBuildMode>'
                f'<Dendrite1_1>{channel}</Dendrite1_1></Neuron></Root>'
            )
            for name in ("Model_00.xml", "Parameters_00.xml"):
                (train / name).write_text(xml, encoding="utf-8")

            snapshot = snapshot_prelaunch_train_configs(train, base / "attempt", {1: 5_000_000.0})

            self.assertEqual(snapshot["files"]["Model_00.xml"]["profile_values"]["1"]["ExcChannel"]["RestingResistance"], 5_000_000.0)
            self.assertEqual(
                (base / "attempt" / "prelaunch-inputs" / "Train" / "Model_00.xml").read_text(encoding="utf-8"),
                xml,
            )

    def test_segment_rm_profile_rejects_invalid_or_duplicate_entries(self):
        for raw in ("", "0=1000000", "1=0", "1=nan", "1=1000000,1=2000000", "one=1000000"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                MODULE.parse_branch_segment_rm_profile(raw)
        for raw in ("", "0,1", "1,x", "1,-2"):
            with self.subTest(lengths=raw), self.assertRaises(ValueError):
                MODULE.parse_branch_initial_lengths(raw)

    def test_rs_rm_limit_overlay_is_isolated_and_train_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            xml = '<Params><ResistanceMax Type="d">100000000000</ResistanceMax></Params>'
            for filename in ("Model_00.xml", "Parameters_00.xml"):
                (source / "Train" / filename).write_text(xml, encoding="utf-8")
            (source / "Test" / "Model_00.xml").write_text(xml, encoding="utf-8")
            attempt = base / "runs" / "r3" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            overlay, record = MODULE.make_runtime_input_overlay(
                source, attempt, "W04", "case",
                quiet_debug_logs=False, branch_gamma_mode=None,
                branch_rs_rm_limit=10.0,
            )

            self.assertEqual((source / "Train" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            for filename in ("Model_00.xml", "Parameters_00.xml"):
                updated = (overlay / "Train" / filename).read_text(encoding="utf-8")
                self.assertIn(
                    '<MaxSynapseToMembraneResistanceRatio Type="d" PType="257" IoType="17">10</MaxSynapseToMembraneResistanceRatio>',
                    updated,
                )
            self.assertEqual((overlay / "Test" / "Model_00.xml").read_text(encoding="utf-8"), xml)
            self.assertEqual(record["branch_rs_rm_limit"], 10.0)
            self.assertEqual(len(record["overrides"]), 2)

    def test_rs_rm_limit_requires_finite_value_at_least_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            attempt = base / "runs" / "r4" / "W04" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)
            for value in (0.5, float("inf"), float("nan")):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    MODULE.make_runtime_input_overlay(
                        source, attempt, "W04", "case",
                        quiet_debug_logs=False, branch_gamma_mode=None,
                        branch_rs_rm_limit=value,
                    )
            self.assertFalse((attempt / "runtime-input-overrides").exists())


class RuntimeStructuralSynapseStepOverlayTests(unittest.TestCase):
    def test_step_override_changes_only_attempt_local_train_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            (source / "matrix_input_manifest.json").write_text("{}\n", encoding="utf-8")
            xml = (
                '<Params><NormalizationMode Type="i">0</NormalizationMode>'
                '<SynapseResistanceStep Type="d">1000000000</SynapseResistanceStep></Params>'
            )
            for side in ("Train", "Test"):
                for filename in ("Model_00.xml", "Parameters_00.xml"):
                    (source / side / filename).write_text(xml, encoding="utf-8")
            attempt = base / "runs" / "r8" / "W01" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)

            overlay, record = MODULE.make_runtime_input_overlay(
                source, attempt, "W01", "case",
                quiet_debug_logs=False, branch_gamma_mode=None,
                synapse_resistance_step=86000000.0,
            )

            updated = '<SynapseResistanceStep Type="d">86000000</SynapseResistanceStep>'
            for filename in ("Model_00.xml", "Parameters_00.xml"):
                self.assertIn(updated, (overlay / "Train" / filename).read_text(encoding="utf-8"))
                self.assertEqual((overlay / "Test" / filename).read_text(encoding="utf-8"), xml)
                self.assertEqual((source / "Train" / filename).read_text(encoding="utf-8"), xml)
            self.assertEqual(record["synapse_resistance_step"], 86000000.0)
            self.assertEqual(len(record["overrides"]), 2)

    def test_invalid_step_is_rejected_before_overlay_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            for side in ("Train", "Test"):
                (source / side).mkdir(parents=True)
            attempt = base / "runs" / "r9" / "W01" / "case" / "attempt-0001"
            attempt.mkdir(parents=True)
            for value in (0.0, -1.0, float("inf"), float("nan")):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    MODULE.make_runtime_input_overlay(
                        source, attempt, "W01", "case",
                        quiet_debug_logs=False, branch_gamma_mode=None,
                        synapse_resistance_step=value,
                    )
            self.assertFalse((attempt / "runtime-input-overrides").exists())


class RunProvenanceTests(unittest.TestCase):
    def test_console_resolution_uses_host_platform_and_respects_override(self):
        root = Path("/repo")
        if os.name == "nt":
            expected = root / "Bin/Platform/Win/NeuroModelerConsole.exe"
        else:
            expected = root / "Bin/Platform/Linux/NeuroModelerConsole"
        self.assertEqual(resolve_console(root, env={}), expected)
        self.assertEqual(resolve_console(root, env={"NMSDK_CONSOLE": "custom/Console"}), Path("custom/Console"))

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

            old_base, old_matrix, old_manifest, old_runs = (
                MODULE.BASE, MODULE.MATRIX, MODULE.MANIFEST, MODULE.RUNS_BASE
            )
            old_run_id = os.environ.get("TIMELEARNER_MATRIX_RUN_ID")
            MODULE.BASE = base
            MODULE.MATRIX = matrix
            MODULE.MANIFEST = matrix_definition
            MODULE.RUNS_BASE = base / "_repro" / "TimeLearnerMatrixRuns"
            os.environ["TIMELEARNER_MATRIX_RUN_ID"] = run_id
            calls = []
            calls_lock = Lock()
            parallel_barrier = Barrier(2)

            def stub_worker(command, *, cwd, env, log_path):
                # Worker options follow the positional wave/case arguments.
                case_id = command[command.index("--worker") + 2]
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
                    "Test/Parameters_00.xml": f"{case_id}-test-params-after",
                    "Test/Model_00.xml": f"{case_id}-test-model-after",
                }
                (attempt_dir / "inputs_manifest.json").write_text(json.dumps({
                    "copied": [
                        {"side": "Test", "rel": "Parameters_00.xml", "sha256": config_before["Test/Parameters_00.xml"]},
                        {"side": "Test", "rel": "Model_00.xml", "sha256": config_before["Test/Model_00.xml"]},
                    ],
                }), encoding="utf-8")
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
                        "config_sha256_before": config_before,
                        "config_sha256_after": config_after,
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
                    return MODULE.run_wave("W01", 3)

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
                self.assertEqual(status["process_limit"], 3)
            finally:
                MODULE.BASE, MODULE.MATRIX, MODULE.MANIFEST, MODULE.RUNS_BASE = (
                    old_base, old_matrix, old_manifest, old_runs
                )
                if old_run_id is None:
                    os.environ.pop("TIMELEARNER_MATRIX_RUN_ID", None)
                else:
                    os.environ["TIMELEARNER_MATRIX_RUN_ID"] = old_run_id


class RunNamespaceSafetyTests(unittest.TestCase):
    def test_duplicate_run_id_is_rejected_without_clobbering_existing_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            runs = Path(temporary)
            reserved = reserve_run_root(runs, "same-run")
            sentinel = reserved / "partial-result.json"
            sentinel.write_text('{"preserve": true}\n', encoding="utf-8")

            with self.assertRaises(FileExistsError):
                reserve_run_root(runs, "same-run")

            self.assertEqual(sentinel.read_text(encoding="utf-8"), '{"preserve": true}\n')

    def test_parallel_run_ids_and_case_attempts_get_disjoint_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = root / "runs"
            attempts = root / "case-attempts"
            barrier = Barrier(8)

            def reserve_pair(index: int) -> tuple[Path, Path]:
                barrier.wait(timeout=5)
                run_root = reserve_run_root(runs, f"run-{index}")
                _, attempt_root = allocate_case_attempt(attempts)
                (run_root / "owner.txt").write_text(str(index), encoding="utf-8")
                (attempt_root / "owner.txt").write_text(str(index), encoding="utf-8")
                return run_root, attempt_root

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                allocated = list(pool.map(reserve_pair, range(8)))

            run_roots = [pair[0] for pair in allocated]
            attempt_roots = [pair[1] for pair in allocated]
            self.assertEqual(len(set(run_roots)), 8)
            self.assertEqual(len(set(attempt_roots)), 8)
            self.assertEqual(
                {path.name for path in attempt_roots},
                {f"attempt-{index:04d}" for index in range(1, 9)},
            )
            run_owners = sorted(
                path.joinpath("owner.txt").read_text(encoding="utf-8")
                for path in run_roots
            )
            attempt_owners = sorted(
                path.joinpath("owner.txt").read_text(encoding="utf-8")
                for path in attempt_roots
            )
            self.assertEqual(run_owners, [str(i) for i in range(8)])
            self.assertEqual(attempt_owners, [str(i) for i in range(8)])

    def test_resume_requires_exact_fingerprint_and_lock_is_exclusive(self):
        manifest = {"run_id": "run-a", "run_fingerprint": "fingerprint-a"}
        verify_run_manifest(manifest, {"run_fingerprint": "fingerprint-a"}, "run-a")
        with self.assertRaisesRegex(RuntimeError, "resume refused"):
            verify_run_manifest(manifest, {"run_fingerprint": "fingerprint-b"}, "run-a")

        with tempfile.TemporaryDirectory() as temporary:
            lock_path = Path(temporary) / "queue.lock"
            with exclusive_file_lock(lock_path, purpose="test"):
                self.assertTrue(lock_path.is_file())
                with self.assertRaisesRegex(RuntimeError, "another matrix launch"):
                    with exclusive_file_lock(lock_path, purpose="second writer"):
                        self.fail("the second owner must not acquire an active lock")
            self.assertFalse(lock_path.exists())

    def test_atomic_no_replace_preserves_existing_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = Path(temporary) / "result.json"
            atomic_write_json(result, {"attempt": 1}, replace=False)
            with self.assertRaises(FileExistsError):
                atomic_write_json(result, {"attempt": 2}, replace=False)
            self.assertEqual(json.loads(result.read_text(encoding="utf-8")), {"attempt": 1})


class PostTuneRunsRootTests(unittest.TestCase):
    def test_worker_workdirs_follow_external_matrix_run_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"TIMELEARNER_MATRIX_RUNS_ROOT": temporary}):
                posttune = MODULE.load_pv()
            self.assertEqual(posttune.RUNS_ROOT, Path(temporary).resolve())


if __name__ == "__main__":
    unittest.main()
