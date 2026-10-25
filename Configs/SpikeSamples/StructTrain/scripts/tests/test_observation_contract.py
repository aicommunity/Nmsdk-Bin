"""Production scorer regressions. No simulator, network or experimental data writes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from selectivity_metrics import classify


def observations():
    rows = []
    for i in range(8):
        rows.append({"trial": str(i), "target_class": "1" if i == 0 else "0",
                     "stim_count": "4", "isis": ".01;.02;.03", "stim_times": "0;.01;.03;.06",
                     "neuron_fired": "1" if i == 0 else "0", "late_fired": "0",
                     "neuron_t_rel": ".1" if i == 0 else "-1", "late_t_rel": "-1",
                     "match": "1", "neuron_spike_count": "1" if i == 0 else "0",
                     "neuron_spike_times": ".1" if i == 0 else "",
                     "schema_version": "3", "complete": "1", "censored": "0"})
    return rows


class ObservationContractTest(unittest.TestCase):
    def test_valid_and_every_target_position(self):
        expected = classify(observations())
        self.assertEqual(expected["ok_audit"], 1)
        for i in range(8):
            rows = observations()
            rows.insert(i, rows.pop(0))
            result = classify(rows)
            for key in ("ok_audit", "fa_strict", "target_hit_strict", "acc_strict", "last_pulse_ok"):
                self.assertEqual(result[key], expected[key], (i, key))

    def test_corruption_cannot_confirm_audit(self):
        for field, value in (("complete", "0"), ("schema_version", "999"),
                             ("neuron_spike_times", ".1;bad"), ("neuron_spike_times", ""),
                             ("neuron_spike_count", "inf"), ("stim_times", "0;nan;.03;.06"),
                             ("stim_times", "0;bad;.03;.06"), ("censored", "1"),
                             ("isis", ".01;bad;.03"), ("isis", ".01;.01;.04"),
                             ("actual_observe_end", "NaN"), ("ltz_potential_max", "inf")):
            with self.subTest(field=field, value=value):
                rows = observations()
                rows[0][field] = value
                result = classify(rows)
                self.assertEqual(result["ok_audit"], 0)
                self.assertEqual(result["schema_ok"], 0)
                self.assertTrue(result["validation_errors"])

    def test_duplicate_and_missing_ids(self):
        rows = observations()
        rows[1]["trial"] = "0"
        self.assertEqual(classify(rows)["ok_audit"], 0)
        self.assertEqual(classify(observations()[:-1])["ok_audit"], 0)
        rows = observations()
        for row in rows:
            row["sample_id"] = "same"
        self.assertEqual(classify(rows)["ok_audit"], 0)

    def test_early_spike_has_one_canonical_failure(self):
        rows = observations()
        rows[0]["neuron_t_rel"] = rows[0]["neuron_spike_times"] = ".02"
        result = classify(rows)
        self.assertEqual(result["ok_audit"], 0)
        self.assertEqual(result["ok_audit_v2"], result["ok_audit"])

    def test_legacy_partial_accuracy_is_preserved(self):
        rows = observations()
        for row in rows[1:5]:
            row.update(neuron_fired="1", neuron_t_rel=".1", neuron_spike_times=".1",
                       neuron_spike_count="1", match="0")
        result = classify(rows)
        self.assertEqual(result["acc_legacy"], 4)
        self.assertEqual(result["target_hit_legacy"], 1)
        self.assertEqual(result["ok_legacy"], 1)
        self.assertEqual(result["ok_audit"], 0)

    def test_missing_historical_evidence_is_unknown(self):
        rows = observations()
        for row in rows:
            del row["complete"]
        result = classify(rows)
        self.assertEqual(result["acc_legacy"], 8)
        self.assertEqual(result["complete"], 0)
        self.assertEqual(result["ok_audit"], 0)

    def test_nonstandard_manifest_trial_set(self):
        rows = observations()[:2]
        rows[0]["trial"] = "target"
        rows[1]["trial"] = "foil"
        self.assertEqual(classify(rows, expected_trial_ids={"target", "foil"})["ok_audit"], 1)

    def test_schema4_requires_context_and_full_window(self):
        rows = observations()
        for row in rows:
            row.update(schema_version="4", run_id="run", trial_id=row["trial"],
                       sample_id=row["trial"], pattern_hash="hash", model_revision="model",
                       measurement_valid="1", soma_amplitudes=".01;.02;.03;.04;.05",
                       onset_abs="10", required_observe_end="11.56", actual_observe_end="11.56")
        self.assertEqual(classify(rows)["ok_audit"], 1)
        rows[0]["actual_observe_end"] = "11.55"
        self.assertEqual(classify(rows)["ok_audit"], 0)


if __name__ == "__main__":
    unittest.main()
