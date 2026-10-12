import importlib.util
import tempfile
import unittest
from pathlib import Path

from posttune_verify import compare_run_inputs


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


class RunProvenanceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
