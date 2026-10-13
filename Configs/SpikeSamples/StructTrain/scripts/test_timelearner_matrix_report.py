import importlib.util
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("update_timelearner_matrix_report.py")
SPEC = importlib.util.spec_from_file_location("matrix_report_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ImmutableWaveReportTests(unittest.TestCase):
    def test_each_run_snapshot_is_kept_and_index_updates_atomically(self):
        with tempfile.TemporaryDirectory() as temporary:
            wave_dir = Path(temporary) / "W01"
            first = {
                "wave": "W01",
                "run_id": "run-a",
                "run_fingerprint": "fp-a",
                "run_complete": True,
                "updated_utc": "2026-10-13T00:00:00+00:00",
                "cases": [{"case": "C1", "result": {"value": "first"}}],
            }
            second = {
                "wave": "W01",
                "run_id": "run-b",
                "run_fingerprint": "fp-b",
                "run_complete": True,
                "updated_utc": "2026-10-13T00:01:00+00:00",
                "cases": [{"case": "C1", "result": {"value": "second"}}],
            }
            first_path = MODULE.append_wave_snapshot(wave_dir, first)
            second_path = MODULE.append_wave_snapshot(wave_dir, second)
            index = json.loads((wave_dir / "results.json").read_text(encoding="utf-8"))
            self.assertTrue(first_path.is_file())
            self.assertTrue(second_path.is_file())
            self.assertEqual([item["run_id"] for item in index["runs"]], ["run-a", "run-b"])
            self.assertEqual(index["run_id"], "run-b")
            self.assertEqual(index["cases"][0]["result"]["value"], "second")
            repeated = {**first, "updated_utc": "2026-10-13T00:02:00+00:00"}
            repeated_path = MODULE.append_wave_snapshot(wave_dir, repeated)
            self.assertEqual(repeated_path, first_path)
            index = json.loads((wave_dir / "results.json").read_text(encoding="utf-8"))
            self.assertEqual([item["run_id"] for item in index["runs"]], ["run-a", "run-b"])
            conflicting = {**first, "cases": [{"case": "C1", "result": {"value": "changed"}}]}
            with self.assertRaisesRegex(RuntimeError, "immutable result snapshot"):
                MODULE.append_wave_snapshot(wave_dir, conflicting)

    def test_parallel_index_updates_keep_every_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            wave_dir = Path(temporary) / "W02"
            snapshots = [
                {
                    "wave": "W02", "run_id": f"run-{index}",
                    "run_fingerprint": f"fp-{index}", "run_complete": True,
                    "updated_utc": f"2026-10-13T00:00:{index:02d}+00:00",
                    "cases": [{"case": f"C{index}", "result": {"value": index}}],
                }
                for index in range(8)
            ]
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda snapshot: MODULE.append_wave_snapshot(wave_dir, snapshot), snapshots))
            index = json.loads((wave_dir / "results.json").read_text(encoding="utf-8"))
            self.assertEqual({item["run_id"] for item in index["runs"]}, {f"run-{i}" for i in range(8)})
            self.assertEqual(len(list((wave_dir / "run_results").glob("*.json"))), 8)


if __name__ == "__main__":
    unittest.main()
