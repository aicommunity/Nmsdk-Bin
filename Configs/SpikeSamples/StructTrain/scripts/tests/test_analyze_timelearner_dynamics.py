from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from analyze_timelearner_dynamics import analyze_file, parse_record


def channel(
    output: float,
    *,
    channel_type: int,
    conductance: float = 1e-7,
    sum_synaptic_state: float | None = None,
    channel_input: float = 0.1,
    time_constant: float = 0.005,
    resistance: float = 1e7,
) -> str:
    if sum_synaptic_state is None:
        sum_synaptic_state = conductance
    return (
        f"{output}:0:{sum_synaptic_state}:0:type={channel_type}:bio={channel_input}:1e-9:"
        f"{resistance}:1e8:1e7:{time_constant}:1:"
        f"channel_inputs={channel_input}:synaptic_inputs={conductance}"
    )


def record(
    now: float,
    c0: float,
    c1: float,
    soma: float,
    *,
    c0_options: dict[str, float] | None = None,
    c1_options: dict[str, float] | None = None,
) -> str:
    state = (
        f"s:sum={soma},channels=2,c0={channel(c0, channel_type=-1, **(c0_options or {}))},"
        f"c1={channel(c1, channel_type=1, **(c1_options or {}))},"
        f"e1,e0=0:1e-7:1:10000000:1|d1:sum={soma},channels=2,"
        f"c0={channel(c0, channel_type=-1, **(c0_options or {}))},"
        f"c1={channel(c1, channel_type=1, **(c1_options or {}))},"
        f"e1,e0=0:1e-7:1:10000000:1"
    )
    return (
        f"schema=1;trainer=branch;iter=0;phase=0;now={now};rel={now};"
        f"new_pulses=0;pulse_index=0;active_pulse=0;est_delay_per_seg=0.005;"
        f"peak_measure_margin=0.06;dataset_sample=0;dataset_iteration=0;"
        f"dataset_next_spike=[0];generator=[];soma={soma};"
        f"dendrite_length=[1];peak_amp=[0];peak_time=[0];peak_seen=[0];"
        f"peak_locked=[0];peak_window_lo_rel=[0];peak_window_hi_rel=[0];"
        f"dissynchronization=[0];prev_dissynchronization=[0];component_state={state}\n"
    )


class AnalyzeTimeLearnerDynamicsTest(unittest.TestCase):
    def test_parse_record_extracts_channel_and_membrane_state(self) -> None:
        parsed = parse_record(record(0.01, -0.5, 0.5, 0.0))
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(len(parsed["components"]), 2)
        self.assertEqual(parsed["components"][0]["channels"][0]["output"], -0.5)
        self.assertEqual(parsed["components"][0]["channels"][0]["type"], -1.0)
        self.assertEqual(parsed["components"][0]["channels"][0]["bio"]["capacity"], 1e-9)
        self.assertEqual(parsed["components"][0]["channels"][0]["bio"]["synaptic_inputs"], [1e-7])
        self.assertEqual(parsed["components"][0]["channels"][0]["synaptic_conductance"], 1e-7)
        self.assertEqual(parsed["components"][0]["synapses"][0]["resistance"], 1e7)

    def test_step_gain_uses_synaptic_input_vector_when_sum_state_is_stale(self) -> None:
        # SumSynapticInput is deliberately zero while the actual vector consumed
        # by NPulseChannel::ACalculate2 contains 1e-7 S.
        stale_state_record = record(0.01, -0.5, 0.5, 0.0).replace(
            "-0.5:0:1e-07:0:type=-1",
            "-0.5:0:0:0:type=-1",
        )
        parsed = parse_record(stale_state_record)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        channel = parsed["components"][0]["channels"][0]
        self.assertEqual(channel["sum_synaptic_input_state"], 0.0)
        self.assertEqual(channel["synaptic_conductance"], 1e-7)
        self.assertEqual(channel["synaptic_conductance_source"], "SynapticInputs")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stale-sum-synaptic-input.log"
            path.write_text(stale_state_record, encoding="utf-8")
            result = analyze_file(path, time_step_hz=2000.0)

        channel_stats = result["channels"]["s.c0"]
        self.assertAlmostEqual(
            channel_stats["explicit_step_gain_from_observed_time_constant"]["min"],
            0.2,
        )

    def test_high_synaptic_conductance_reports_unstable_explicit_step(self) -> None:
        # This mirrors the archived BR480 transition: channel Type=-1, input=-1,
        # R=10 MOhm, C=1 nF, f=2 kHz, and G=0.75 uS. The actual Euler gain is
        # 3.6125 even though the separately serialized SumSynapticInput is zero.
        unstable = record(
            0.010,
            -1.73125,
            0.5,
            0.0,
            c0_options={
                "conductance": 0.75e-6,
                "sum_synaptic_state": 0.0,
                "channel_input": -1.0,
                "time_constant": 1e-9 / (0.75e-6 + 1 / 1e7),
                "resistance": 1e7,
            },
        )
        crossing = record(
            0.0105,
            3.08041015625,
            0.5,
            0.0,
            c0_options={
                "conductance": 0.675e-6,
                "sum_synaptic_state": 0.0,
                "channel_input": -1.0,
                "time_constant": 1e-9 / (0.675e-6 + 1 / 1e7),
                "resistance": 1e7,
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unstable-explicit-step.log"
            path.write_text(unstable + crossing, encoding="utf-8")
            result = analyze_file(path, time_step_hz=2000.0)

        channel_stats = result["channels"]["s.c0"]
        self.assertAlmostEqual(
            channel_stats["explicit_step_gain_from_observed_time_constant"]["max"],
            3.6125,
        )
        self.assertEqual(channel_stats["samples_step_gain_over_2"], 2)
        self.assertEqual(channel_stats["samples_crossing_expected_sign"], 1)
        self.assertEqual(channel_stats["samples_outside_expected_signed_envelope"], 2)

    def test_older_records_without_serialized_type_use_observed_sign_fallback(self) -> None:
        old_record = record(0.01, -0.5, 0.5, 0.0).replace(":type=-1", "").replace(":type=1", "")
        parsed = parse_record(old_record)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertIsNone(parsed["components"][0]["channels"][0]["type"])

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy-dynamics.log"
            path.write_text(old_record, encoding="utf-8")
            result = analyze_file(path)

        legacy_channel = result["channels"]["s.c0"]
        self.assertIsNone(legacy_channel["declared_channel_type"])
        self.assertEqual(legacy_channel["fallback_first_nonzero_output_sign"], -1)
        self.assertIn("serialized NPulseChannel.Type when available",
                      result["assumptions"]["signed_channel_envelope"])

    def test_stream_summary_flags_sign_and_soma_excursions_and_estimates_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "TimeLearnerTrainingDynamics.log"
            path.write_text(
                record(0.01, -0.5, 0.5, 0.0)
                + record(0.02, 0.25, 1.2, 1.45),
                encoding="utf-8",
            )
            result = analyze_file(path, soma_abs_limit=1.0, time_step_hz=2000.0)

        self.assertEqual(result["records"], 2)
        self.assertEqual(result["soma_sum_potential"]["samples_at_or_above_abs_limit"], 1)
        self.assertEqual(result["channels"]["s.c0"]["samples_crossing_expected_sign"], 1)
        self.assertEqual(result["channels"]["s.c0"]["samples_outside_expected_signed_envelope"], 1)
        self.assertEqual(result["channels"]["s.c1"]["samples_outside_expected_signed_envelope"], 1)
        self.assertEqual(result["channels"]["s.c0"]["declared_channel_type"], -1.0)
        self.assertAlmostEqual(
            result["channels"]["s.c0"]["q_from_observed_time_constant"]["min"], 20.0
        )
        self.assertAlmostEqual(
            result["channels"]["s.c0"]["explicit_step_gain_from_observed_time_constant"]["min"],
            0.2,
        )

    def test_cli_json_is_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.txt"
            path.write_text(record(0.01, -0.5, 0.5, 0.0), encoding="utf-8")
            result = analyze_file(path)
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
