#!/usr/bin/env python3
"""Stream and summarize Branch TimeLearner per-tick dynamics logs.

This tool only reads telemetry emitted by the C++ trainer. It does not train,
modify model state, or infer classification quality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO


COMPONENT_RE = re.compile(
    r"(?:^|\|)(?P<name>s|d\d+):sum=(?P<sum>[^,]+),channels=(?P<count>\d+)"
    r"(?P<body>.*?)(?=(?:\|(?:s|d\d+):)|$)"
)
CHANNEL_RE = re.compile(r"(?:^|,)(?P<name>c\d+)=(?P<value>[^,]+)")
SYNAPSE_RE = re.compile(r"(?:^|,)(?P<name>[ei]\d+)=(?P<value>[^,]+)")


def _number(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


@dataclass
class Range:
    count: int = 0
    minimum: float | None = None
    maximum: float | None = None
    max_abs: float = 0.0
    min_at: float | None = None
    max_at: float | None = None
    non_finite: int = 0

    def add(self, value: float | None, at: float | None = None) -> None:
        if not _finite(value):
            self.non_finite += 1
            return
        assert value is not None
        self.count += 1
        self.max_abs = max(self.max_abs, abs(value))
        if self.minimum is None or value < self.minimum:
            self.minimum, self.min_at = value, at
        if self.maximum is None or value > self.maximum:
            self.maximum, self.max_at = value, at

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "min": self.minimum,
            "min_at_model_time": self.min_at,
            "max": self.maximum,
            "max_at_model_time": self.max_at,
            "max_abs": self.max_abs,
            "non_finite": self.non_finite,
        }


def parse_record(line: str) -> dict[str, Any] | None:
    """Parse one schema-1 Branch dynamics line; return None for other records."""
    marker = ";component_state="
    if not line.startswith("schema=1;trainer=branch;") or marker not in line:
        return None
    header, component_state = line.rstrip("\r\n").split(marker, 1)
    fields: dict[str, str] = {}
    for item in header.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value

    record: dict[str, Any] = {
        "iter": _number(fields.get("iter")),
        "phase": _number(fields.get("phase")),
        "now": _number(fields.get("now")),
        "rel": _number(fields.get("rel")),
        "pulse_index": _number(fields.get("pulse_index")),
        "active_pulse": _number(fields.get("active_pulse")),
        "soma": _number(fields.get("soma")),
        "components": [],
    }

    for component_match in COMPONENT_RE.finditer(component_state):
        component: dict[str, Any] = {
            "name": component_match.group("name"),
            "sum": _number(component_match.group("sum")),
            "channels": [],
            "synapses": [],
        }
        body = component_match.group("body")
        for channel_match in CHANNEL_RE.finditer(body):
            raw = channel_match.group("value")
            primary, separator, bio_raw = raw.partition(":bio=")
            channel_fields = primary.split(":")
            channel: dict[str, Any] = {
                "name": channel_match.group("name"),
                "output": _number(channel_fields[0] if len(channel_fields) > 0 else None),
                "sum_channel_input": _number(channel_fields[1] if len(channel_fields) > 1 else None),
                # SumSynapticInput is a separately serialized state and may be
                # stale/zero. The trainer actually sums SynapticInputs in
                # NPulseChannel::ACalculate2, so replace this fallback below
                # whenever the per-synapse vector is present in the snapshot.
                "sum_synaptic_input_state": _number(channel_fields[2] if len(channel_fields) > 2 else None),
                "synaptic_conductance": _number(channel_fields[2] if len(channel_fields) > 2 else None),
                "activated": _number(channel_fields[3] if len(channel_fields) > 3 else None),
                "type": _number(channel_fields[4].split("=", 1)[1])
                if len(channel_fields) > 4 and channel_fields[4].startswith("type=") else None,
            }
            if separator:
                bio_prefix, channel_inputs_separator, input_vectors = bio_raw.partition(":channel_inputs=")
                bio_values = bio_prefix.split(":")
                channel["bio"] = {
                    "channel_input": _number(bio_values[0] if len(bio_values) > 0 else None),
                    "capacity": _number(bio_values[1] if len(bio_values) > 1 else None),
                    "resistance": _number(bio_values[2] if len(bio_values) > 2 else None),
                    "fb_resistance": _number(bio_values[3] if len(bio_values) > 3 else None),
                    "resting_resistance": _number(bio_values[4] if len(bio_values) > 4 else None),
                    "time_constant": _number(bio_values[5] if len(bio_values) > 5 else None),
                    "connected_synapses": _number(bio_values[6] if len(bio_values) > 6 else None),
                }
                if channel_inputs_separator:
                    channel_inputs_raw, synaptic_separator, synaptic_inputs_raw = input_vectors.partition(":synaptic_inputs=")
                    channel["bio"]["channel_inputs"] = [
                        value for token in channel_inputs_raw.split(":")
                        if (value := _number(token)) is not None
                    ]
                    if synaptic_separator:
                        synaptic_inputs = [
                            value for token in synaptic_inputs_raw.split(":")
                            if (value := _number(token)) is not None
                        ]
                        channel["bio"]["synaptic_inputs"] = synaptic_inputs
                        channel["synaptic_conductance"] = sum(synaptic_inputs)
                        channel["synaptic_conductance_source"] = "SynapticInputs"
                    else:
                        channel["synaptic_conductance_source"] = "SumSynapticInput_fallback"
                else:
                    channel["synaptic_conductance_source"] = "SumSynapticInput_fallback"
            component["channels"].append(channel)

        for synapse_match in SYNAPSE_RE.finditer(body):
            values = synapse_match.group("value").split(":")
            if len(values) < 4:
                continue
            component["synapses"].append({
                "name": synapse_match.group("name"),
                "output": _number(values[1] if len(values) > 1 else None),
                "pre_output": _number(values[2] if len(values) > 2 else None),
                "resistance": _number(values[3] if len(values) > 3 else None),
                "weight": _number(values[4] if len(values) > 4 else None),
            })
        record["components"].append(component)
    return record


@dataclass
class ChannelStats:
    output: Range = field(default_factory=Range)
    input: Range = field(default_factory=Range)
    conductance: Range = field(default_factory=Range)
    channel_input: Range = field(default_factory=Range)
    effective_membrane_resistance: Range = field(default_factory=Range)
    q: Range = field(default_factory=Range)
    step_gain: Range = field(default_factory=Range)
    declared_type: float | None = None
    first_nonzero_sign: int = 0
    signed_envelope_violations: int = 0
    zero_crossing_samples: int = 0
    outside_absolute_unit_interval: int = 0
    gain_over_one: int = 0
    gain_over_two: int = 0
    invalid_gain_estimates: int = 0

    def add(self, channel: dict[str, Any], at: float | None, rest_bound: float,
            time_step_hz: float | None) -> None:
        output = channel.get("output")
        self.output.add(output, at)
        self.input.add(channel.get("sum_channel_input"), at)
        self.conductance.add(channel.get("synaptic_conductance"), at)
        bio = channel.get("bio", {})
        self.channel_input.add(bio.get("channel_input"), at)

        if _finite(output):
            assert output is not None
            if abs(output) > rest_bound:
                self.outside_absolute_unit_interval += 1
            channel_type = channel.get("type")
            if _finite(channel_type) and channel_type != 0.0:
                self.declared_type = channel_type
                orientation = 1 if channel_type > 0 else -1
            elif self.first_nonzero_sign != 0:
                orientation = self.first_nonzero_sign
            else:
                orientation = 0
            if orientation == 0 and abs(output) > 1e-15:
                self.first_nonzero_sign = 1 if output > 0 else -1
                orientation = self.first_nonzero_sign
            if orientation < 0:
                if output > 0.0 or output < -rest_bound:
                    self.signed_envelope_violations += 1
                if output > 0.0:
                    self.zero_crossing_samples += 1
            elif orientation > 0:
                if output < 0.0 or output > rest_bound:
                    self.signed_envelope_violations += 1
                if output < 0.0:
                    self.zero_crossing_samples += 1

        if time_step_hz is None:
            return
        capacity = bio.get("capacity")
        tau = bio.get("time_constant")
        conductance = channel.get("synaptic_conductance")
        if not all(_finite(v) for v in (capacity, tau, conductance)) or tau <= 0.0:
            self.invalid_gain_estimates += 1
            return
        assert capacity is not None and tau is not None and conductance is not None
        # From tau=C/(G+1/R), recover the resistance selected by the channel
        # for this sample. K=(1+G*R)/(tau*f) is the explicit-step coefficient.
        inverse_resistance = capacity / tau - conductance
        if not math.isfinite(inverse_resistance) or inverse_resistance <= 0.0:
            self.invalid_gain_estimates += 1
            return
        effective_resistance = 1.0 / inverse_resistance
        self.effective_membrane_resistance.add(effective_resistance, at)
        q = capacity * effective_resistance * time_step_hz
        gain = (1.0 + conductance * effective_resistance) / (tau * time_step_hz)
        self.q.add(q, at)
        self.step_gain.add(gain, at)
        if gain > 1.0:
            self.gain_over_one += 1
        if gain > 2.0:
            self.gain_over_two += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "output": self.output.as_dict(),
            "sum_channel_input": self.input.as_dict(),
            "synaptic_conductance": self.conductance.as_dict(),
            "post_feedback_channel_input": self.channel_input.as_dict(),
            "declared_channel_type": self.declared_type,
            "fallback_first_nonzero_output_sign": self.first_nonzero_sign or None,
            "samples_crossing_expected_sign": self.zero_crossing_samples,
            "samples_outside_expected_signed_envelope": self.signed_envelope_violations,
            "samples_outside_absolute_rest_bound": self.outside_absolute_unit_interval,
            "effective_membrane_resistance_from_time_constant": self.effective_membrane_resistance.as_dict(),
            "q_from_observed_time_constant": self.q.as_dict(),
            "explicit_step_gain_from_observed_time_constant": self.step_gain.as_dict(),
            "samples_step_gain_over_1": self.gain_over_one,
            "samples_step_gain_over_2": self.gain_over_two,
            "invalid_step_gain_estimates": self.invalid_gain_estimates,
        }


@dataclass
class ScalarStats:
    values: dict[str, Range] = field(default_factory=dict)

    def add(self, name: str, value: float | None, at: float | None) -> None:
        self.values.setdefault(name, Range()).add(value, at)

    def as_dict(self) -> dict[str, Any]:
        return {name: stat.as_dict() for name, stat in sorted(self.values.items())}


def analyze_file(path: Path, *, rest_bound: float = 1.0,
                 soma_abs_limit: float | None = None,
                 time_step_hz: float | None = None) -> dict[str, Any]:
    channel_stats: dict[str, ChannelStats] = {}
    membrane_stats = ScalarStats()
    synapse_resistance_stats = ScalarStats()
    soma_stats = Range()
    soma_over_limit = 0
    digest = hashlib.sha256()
    records = 0
    ignored_lines = 0
    non_finite_examples: list[dict[str, Any]] = []
    first_model_time: float | None = None
    last_model_time: float | None = None
    max_line_bytes = 0

    with path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            digest.update(raw_line)
            max_line_bytes = max(max_line_bytes, len(raw_line))
            line = raw_line.decode("utf-8", errors="replace")
            record = parse_record(line)
            if record is None:
                ignored_lines += 1
                continue
            records += 1
            at = record["now"]
            if first_model_time is None and _finite(at):
                first_model_time = at
            if _finite(at):
                last_model_time = at
            soma = record["soma"]
            soma_stats.add(soma, at)
            if soma_abs_limit is not None and _finite(soma) and abs(soma) >= soma_abs_limit:
                soma_over_limit += 1
            for component in record["components"]:
                name = component["name"]
                membrane_stats.add(f"{name}.sum_potential", component.get("sum"), at)
                for channel in component["channels"]:
                    key = f"{name}.{channel['name']}"
                    stat = channel_stats.setdefault(key, ChannelStats())
                    stat.add(channel, at, rest_bound, time_step_hz)
                    if any(not _finite(v) for v in (
                        channel.get("output"), channel.get("sum_channel_input"),
                        channel.get("synaptic_conductance"),
                        channel.get("bio", {}).get("channel_input"),
                    )) and len(non_finite_examples) < 20:
                        non_finite_examples.append({"line": line_number, "channel": key})
                for synapse in component["synapses"]:
                    synapse_resistance_stats.add(
                        f"{name}.{synapse['name']}.resistance", synapse.get("resistance"), at
                    )

    if records == 0:
        raise ValueError(f"No schema-1 Branch dynamics records found in {path}")

    return {
        "schema": 1,
        "source_file": str(path),
        "source_size_bytes": path.stat().st_size,
        "source_sha256": digest.hexdigest(),
        "records": records,
        "ignored_lines": ignored_lines,
        "max_line_bytes": max_line_bytes,
        "model_time_start": first_model_time,
        "model_time_end": last_model_time,
        "assumptions": {
            "rest_bound": rest_bound,
            "signed_channel_envelope": "serialized NPulseChannel.Type when available; otherwise the first nonzero observed output sign is used as a provisional fallback orientation",
            "time_step_hz": time_step_hz,
            "synaptic_conductance": "summed serialized SynapticInputs vector, matching NPulseChannel::ACalculate2; older snapshots without the vector fall back to SumSynapticInput state",
            "step_gain": "estimated from C, observed TimeConstant and actual summed SynapticInputs conductance; fixed-input local step only",
            "soma_abs_limit": soma_abs_limit,
        },
        "soma_sum_potential": {
            **soma_stats.as_dict(),
            "samples_at_or_above_abs_limit": soma_over_limit if soma_abs_limit is not None else None,
        },
        "membrane_sum_potentials": membrane_stats.as_dict(),
        "channels": {key: value.as_dict() for key, value in sorted(channel_stats.items())},
        "synapse_resistances": synapse_resistance_stats.as_dict(),
        "non_finite_examples": non_finite_examples,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="TimeLearnerTrainingDynamics.log")
    parser.add_argument("--rest-bound", type=float, default=1.0,
                        help="absolute resting bound used for telemetry flags (default: 1)")
    parser.add_argument("--soma-abs-limit", type=float,
                        help="optional trainer-specific absolute soma limit to count crossings")
    parser.add_argument("--time-step-hz", type=float,
                        help="model update frequency; enables per-sample explicit-step gain estimates")
    parser.add_argument("--output", type=Path, help="write JSON summary atomically to this path")
    args = parser.parse_args(argv)
    if args.rest_bound <= 0 or (args.soma_abs_limit is not None and args.soma_abs_limit <= 0) \
            or (args.time_step_hz is not None and args.time_step_hz <= 0):
        parser.error("rest bound, soma limit, and time-step frequency must be positive")
    try:
        result = analyze_file(args.log, rest_bound=args.rest_bound,
                              soma_abs_limit=args.soma_abs_limit,
                              time_step_hz=args.time_step_hz)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_name(args.output.name + f".{os.getpid()}.tmp")
        temp.write_text(rendered, encoding="utf-8", newline="\n")
        os.replace(temp, args.output)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
