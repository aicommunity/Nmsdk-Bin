#!/usr/bin/env python3
"""Build the current TimeLearner registry and immutable Train/Test snapshots.

This is experiment preparation only. It never launches NeuroModelerConsole.
The existing C++ trainers remain the sole implementation of learning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import runpy
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
BIN_ROOT = BASE.parents[2]
ROOT = BIN_ROOT.parent
MATRIX = BASE / "TimeLearnerMatrix"
MANIFEST = MATRIX / "matrix.json"
HISTORY_REPORT = ROOT / "Docs" / "Audit" / "TimeLearner-2026-09-26-review" / "TIMELEARNER_FULL_MATRIX_AND_HISTORY_2026-10-10.ru.md"
HISTORY_COVERAGE = MATRIX / "historical_coverage.json"
FULL49_HISTORY_SOURCE = MATRIX / "full49_history_source.json"
READINESS = MATRIX / "readiness.json"
HISTORICAL_BIN = "6a7ef63adb1b10ff468d7910424fc2ab75e0ad3d"
HISTORICAL_ROOT = "ae93cd7180164d9f25a19fff310ac764c2e5b06d"
HISTORICAL_PULSE = "b5229e471f6ad1f595f667f15339ed02f953518f"
HISTORICAL_CONSOLE = "39edc03c82665dba…"


def parse_history_table() -> dict[str, dict[str, str]]:
    for source_file in (FULL49_HISTORY_SOURCE, HISTORY_COVERAGE):
        if not source_file.is_file():
            continue
        try:
            prior = json.loads(source_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        prior_cases = prior.get("cases", {})
        if isinstance(prior_cases, dict) and len(prior_cases) == 49:
            return {
                case: {
                    "source": str(row.get("source", "")),
                    "historical_metrics": str(row.get("historical_metrics", "")),
                    "softcold_2026_10_03": str(row.get("softcold_2026_10_03", "")),
                    "softcold_2026_10_06": str(row.get("softcold_2026_10_06", "")),
                    "softcold_2026_10_09": str(row.get("softcold_2026_10_09", "")),
                }
                for case, row in prior_cases.items()
            }
    if not HISTORY_REPORT.is_file():
        raise FileNotFoundError(
            f"full49 history data is missing from {FULL49_HISTORY_SOURCE}, {HISTORY_COVERAGE}, and {HISTORY_REPORT}"
        )
    rows: dict[str, dict[str, str]] = {}
    for line in HISTORY_REPORT.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        case = cells[0].strip("`")
        if case in ("Case", ""):
            continue
        rows[case] = {
            "source": cells[1].strip("`").replace("\\`", "`"),
            "historical_metrics": cells[2],
            "softcold_2026_10_03": cells[3],
            "softcold_2026_10_06": cells[4],
            "softcold_2026_10_09": cells[5],
        }
    return rows


def trainer_for(kind: str) -> str:
    return "NNeuronTimeLearnerBranch" if kind == "branch" else "NNeuronTimeLearner"


def family_for(case_id: str, source: str) -> str:
    p = source.lower()
    if "fastspan" in p:
        return "FastSpan"
    if "ltzcalibrate" in p:
        return "LTZ-calibrated Pack A"
    if "phasea" in p:
        return "PhaseA/Phase6"
    if "presynapticinhib" in p:
        return "PSI historical sweep"
    if "timeneurontimelearner" in p:
        return "legacy Classic"
    if "branch" in p:
        return "Branch historical"
    if "asymrm" in p:
        return "AsymRm Pack A"
    return "historical configuration"


def source_rel(path: Path) -> str:
    return path.resolve().relative_to(BASE).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def latest_config_commit(source: str) -> str:
    git_path = "Configs/SpikeSamples/StructTrain/" + source
    commit = subprocess.check_output(
        ["git", "-C", str(BIN_ROOT), "log", "-1", "--format=%H", "--", git_path],
        text=True,
    ).strip()
    if not commit:
        raise ValueError(f"no committed source revision for historical config {source}")
    return commit


def template_for(template: dict[str, Any], name: str, *, source: str | None = None, preinh: str | None = None) -> str:
    if source is None and preinh is None:
        return name
    template[name] = {
        "source": source or preinh,
        "preinh_source": preinh or source,
        "paired_source": source or preinh,
        "kind": "branch" if "branch" in name else "asym",
        "train_t": 640,
    }
    if name.endswith("480"):
        template[name]["kind"] = "branch" if "branch" in name else "phase6"
        template[name]["train_t"] = 900
    return name


def build_registry() -> tuple[dict[str, Any], dict[str, Any]]:
    original = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_cases = [c for c in original["cases"] if c.get("wave") in {"W01", "W02", "W03", "W04"}]
    if len(base_cases) != 32:
        raise ValueError(f"expected the original 32-case W01-W04 baseline, found {len(base_cases)}")
    base_template_names = {c["template"] for c in base_cases}
    templates = {name: original["templates"][name] for name in base_template_names}
    cases = list(base_cases)
    waves: dict[str, dict[str, Any]] = {
        f"W{i:02d}": {"title": ""} for i in range(1, 48)
    }
    waves.update({
        "W01": {"title": "Classic: паттерны 25/50 мс; обе схемы нормализации амплитуды; пресинаптическое торможение выключено/включено"},
        "W02": {"title": "Classic: паттерны 100/480 мс; обе схемы нормализации амплитуды; пресинаптическое торможение выключено/включено"},
        "W03": {"title": "Branch: паттерны 25/50 мс; обе схемы нормализации; торможение следующего сегмента выключено"},
        "W04": {"title": "Branch: паттерны 100/480 мс; обе схемы нормализации; торможение следующего сегмента выключено"},
        "W05": {"title": "Classic: сравнение PSI-шаблонов с согласованными базовыми шаблонами на четырёх длительностях"},
        "W06": {"title": "Branch: сравнение PSI-шаблонов с согласованными базовыми шаблонами на четырёх длительностях"},
        "W07": {"title": "Branch: торможение следующего сегмента на 25/50 мс, отдельно с пресинаптическим торможением и без него"},
        "W08": {"title": "Branch: торможение следующего сегмента на 100/480 мс, отдельно с пресинаптическим торможением и без него"},
        "W09": {"title": "Точные повторы исторических входов: Classic Pack A, Branch Pack A и полный паттерн 480 мс"},
        "W10": {"title": "Точные повторы исторических входов Branch: общие и пресинаптически заторможенные паттерны, разные длительности"},
        "W11": {"title": "Точные повторы исторических входов Classic с асимметричными мембранами и Branch с разными режимами концевого сопротивления"},
        "W12": {"title": "Точные повторы сжатых коротких последовательностей и калибровки полного 480-мс паттерна"},
        "W13": {"title": "Точные повторы коротких последовательностей и калибровки порога локальной временной зоны"},
        "W14": {"title": "Точные повторы базового полного паттерна 480 мс и исторических настроек порога/пресинаптического торможения"},
        "W15": {"title": "Точные повторы исторических длинных последовательностей с разной силой торможения"},
        "W16": {"title": "Сила пресинаптического торможения 0.5 и 2.7: Classic, паттерны 25/50 мс"},
        "W17": {"title": "Сила пресинаптического торможения 0.5 и 2.7: Classic, паттерны 100/480 мс"},
        "W18": {"title": "Сила пресинаптического торможения 0.5 и 2.7: Branch, паттерны 25/50 мс"},
        "W19": {"title": "Сила пресинаптического торможения 0.5 и 2.7: Branch, паттерны 100/480 мс"},
        "W20": {"title": "Исторические пресинаптически заторможенные паттерны 200/300/400 мс в структурном режиме"},
        "W21": {"title": "Верхнее отношение сопротивления синапса к мембране: Classic, диагностические случаи"},
        "W22": {"title": "Верхнее отношение сопротивления синапса к мембране: Branch, диагностические случаи"},
        "W23": {"title": "Стартовое сопротивление синапса и синхронизация: Classic, паттерн 50 мс"},
        "W24": {"title": "Стартовое сопротивление синапса и синхронизация: Classic, паттерн 480 мс"},
        "W25": {"title": "Стартовое сопротивление синапса и синхронизация: Branch, паттерн 50 мс"},
        "W26": {"title": "Стартовое сопротивление синапса и синхронизация: Branch, паттерн 480 мс"},
        "W27": {"title": "Длинный паттерн и свойства кабеля мембраны: Classic; RC-постоянная, оценка задержки и максимальная длина"},
        "W28": {"title": "Длинный паттерн и свойства кабеля мембраны: Branch; RC-постоянная, оценка задержки и максимальная длина"},
        "W29": {"title": "Допуск синхронизации пиков: Classic, короткий и длинный паттерн"},
        "W30": {"title": "Допуск синхронизации пиков: Branch, короткий и длинный паттерн"},
        "W31": {"title": "Ширина окна измерения пиков: Classic, две схемы нормализации"},
        "W32": {"title": "Ширина окна измерения пиков: Branch, две схемы нормализации"},
        "W33": {"title": "Отдельная калибровка после обучения: Classic, паттерны 25/50 мс"},
        "W34": {"title": "Отдельная калибровка после обучения: Branch, паттерны 25/50 мс"},
        "W35": {"title": "Режимы сопротивления концевых синапсов после обучения: Classic, Canon/Flat"},
        "W36": {"title": "Режимы сопротивления концевых синапсов после обучения: Branch, Canon/Keep/Search"},
        "W37": {"title": "Второй и третий наборы паттернов: Classic, 25/100 мс, структурная и структурно-параметрическая схемы"},
        "W38": {"title": "Второй и третий наборы паттернов: Branch, 25/100 мс, структурная и структурно-параметрическая схемы"},
        "W39": {"title": "Порядок импульсов Branch развёрнут: структурная схема, четыре длительности, торможение off/on"},
        "W40": {"title": "Порядок импульсов Branch развёрнут: структурно-параметрическая схема, четыре длительности, торможение off/on"},
        "W41": {"title": "Сопротивление и ёмкость мембраны меняются по одному параметру: Classic"},
        "W42": {"title": "Сопротивление и ёмкость мембраны меняются по одному параметру: Branch"},
        "W43": {"title": "Повторяемость контрольного опыта Classic: два чистых запуска"},
        "W44": {"title": "Повторяемость контрольного опыта Branch: два чистых запуска"},
        "W45": {"title": "Сила пресинаптического торможения 2.6: Branch, все четыре длительности"},
        "W46": {"title": "Августовские FastResponse конфигурации: фактическая сетка постоянной диссоциации и ёмкости мембраны"},
        "W47": {"title": "Августовские случаи ручного уменьшения сопротивления концевых синапсов до Rmin"},
    })

    def add(wave: str, case_id: str, template_name: str, description: str, **factors: Any) -> None:
        row = {
            "id": case_id,
            "wave": wave,
            "template": template_name,
            "trainer": factors.pop("trainer", trainer_for(templates[template_name]["kind"])),
            "duration_ms": factors.pop("duration_ms"),
            "pattern_family": factors.pop("pattern_family", "AsymRm pack A"),
            "normalization_mode": factors.pop("normalization_mode", 1),
            "presynaptic_inhibition": factors.pop("presynaptic_inhibition", False),
            "presynaptic_coefficient": factors.pop("presynaptic_coefficient", 0.0),
            "branch_nextseg": factors.pop("branch_nextseg", False),
            "posttrain_tuning": factors.pop("posttrain_tuning", False),
            "tipr_mode": factors.pop("tipr_mode", 1),
            "train_t": factors.pop("train_t", templates[template_name]["train_t"]),
            "description_ru": description,
        }
        row.update(factors)
        cases.append(row)

    def current_template(trainer: str, duration: int, family: str = "AsymRm") -> str:
        if trainer == "NNeuronTimeLearnerBranch":
            return {25: "branch25", 50: "branch50", 100: "branch100", 480: "branch480"}[duration]
        if family == "FastSpan":
            return f"fast{duration}"
        if family == "LTZ-calibrated Pack A":
            return f"ltz{duration}"
        return {25: "classic25", 50: "classic50", 100: "classic100", 480: "classic480"}[duration]

    # Matrix rows W01-W04 remain the existing balanced 32-case block.

    # W05-W06 isolate the historic presynaptic model topology from the matched base.
    for wave, trainer in (("W05", "NNeuronTimeLearner"), ("W06", "NNeuronTimeLearnerBranch")):
        for duration in (25, 50, 100, 480):
            template_name = current_template(trainer, duration)
            for mode in (0, 1):
                cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_N{mode}_PSI25_HIST"
                add(wave, cid, template_name,
                    f"{trainer}: исторический пресинаптически заторможенный шаблон {duration} мс, NormalizationMode={mode}; сравнение с matched PSI-клеткой базовой волны.",
                    trainer=trainer, duration_ms=duration, normalization_mode=mode,
                    presynaptic_inhibition=True, presynaptic_coefficient=2.5,
                    source_config=templates[template_name]["preinh_source"],
                    control_case_id=f"{'W01' if trainer == 'NNeuronTimeLearner' and duration < 100 else 'W02' if trainer == 'NNeuronTimeLearner' else 'W03' if duration < 100 else 'W04'}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_N{mode}_PSI25")

    # Branch NextSeg alone and its interaction with presynaptic inhibition.
    # The NextSeg topology has a different count of SynapseClassName nodes than
    # the ordinary PSI templates at 25/50 ms. For PSI-on, keep the NextSeg
    # topology fixed and map every existing branch synapse to the verified
    # coefficient-specific implementation class. Validation requires that the
    # target class exists in the matched PSI source for Train and Test.
    nextseg_sources = {
        25: "SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9",
        50: "SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9",
        100: "SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9",
        480: "SelectivityBranch/EXP_br480_nextseginh_tiprmin",
    }
    psi_class_sources = {
        25: "SelectivityBranch/EXP_br_span25_packA_preinh_C1e9",
        50: "SelectivityBranch/EXP_br_span50_packA_preinh_C1e9",
        100: "SelectivityBranch/EXP_br_span100_packA_preinh_C1e9",
        480: "SelectivityBranch/EXP_br480_preinh250_tiprmin",
    }
    for wave, durations in (("W07", (25, 50)), ("W08", (100, 480))):
        for duration in durations:
            nextseg = nextseg_sources[duration]
            psi_classes = psi_class_sources[duration]
            template_name = f"branch{duration}_nextseg"
            templates[template_name] = {
                "source": nextseg,
                "preinh_source": nextseg,
                "paired_source": nextseg,
                "kind": "branch",
                "train_t": 900 if duration == 480 else (640 if duration >= 100 else 320),
            }
            for mode in (0, 1):
                for psi_enabled in (False, True):
                    cid = f"{wave}_BR{duration}_N{mode}_PSI{'25' if psi_enabled else 'off'}_NEXT"
                    description = (
                        f"Branch на {duration} мс: торможение следующего сегмента включено, "
                        f"пресинаптическое торможение {'включено с коэффициентом 2.5' if psi_enabled else 'выключено'}, "
                        f"режим нормализации {'структурный' if mode == 0 else 'структурно-параметрический'}."
                    )
                    if psi_enabled:
                        description += (
                            " В конфиге сохранена топология торможения следующего сегмента; "
                            "типы всех её синапсов сопоставлены с соответствующими классами PSI."
                        )
                    add(wave, cid, template_name,
                        description,
                        trainer="NNeuronTimeLearnerBranch", duration_ms=duration,
                        normalization_mode=mode, presynaptic_inhibition=psi_enabled,
                        presynaptic_coefficient=2.5 if psi_enabled else 0.0,
                        branch_nextseg=True, source_config=nextseg,
                        preinh_topology_source=nextseg,
                        preinh_class_source=psi_classes if psi_enabled else nextseg,
                        preserve_classes=not psi_enabled,
                        force_presynaptic_classes=psi_enabled)

    # Re-run each of the 49 unique historical configurations on the current source tree,
    # while copying the exact historical Bin inputs from the pinned 6a7ef63a snapshot.
    history = parse_history_table()
    pv_ns = runpy.run_path(str(BASE / "scripts" / "posttune_verify.py"), run_name="timelearner_matrix_builder")
    pv_cases: dict[str, dict[str, Any]] = pv_ns["CASES"]
    if set(history) != set(pv_cases):
        raise ValueError(f"history table and historical CASES disagree: table_only={sorted(set(history)-set(pv_cases))}, cases_only={sorted(set(pv_cases)-set(history))}")
    history_map: dict[str, Any] = {}
    hist_waves = [f"W{i:02d}" for i in range(9, 16)]
    hist_ids = list(pv_cases)
    for index, case_id in enumerate(hist_ids):
        wave = hist_waves[index // 7]
        old = pv_cases[case_id]
        source = source_rel(old["root"])
        kind = str(old["kind"])
        template_name = f"historical_{kind}"
        if template_name not in templates:
            templates[template_name] = {
                "source": source,
                "preinh_source": source,
                "paired_source": source,
                "kind": kind,
                "train_t": int(old["train_t"]),
            }
        duration = int(old["span_ms"])
        is_psi = (
            "preinh" in case_id
            or case_id in {"psi01_050", "psi14_260", "psi15_270", "psi21_100", "psi31_200", "psi33_300", "psi35_400"}
        )
        nextseg = "nextseg" in case_id
        posttune = case_id != "br25_off"
        tip_mode = {"br25_on": 1, "br25_off": 0, "asym25": 2, "br100_keep": 3, "br100_search": 4}.get(case_id, 1)
        add(wave, f"{wave}_HIST_{case_id}", template_name,
            f"Точная повторная проверка исторического случая {case_id}: {family_for(case_id, source)}, {duration} мс; исходный Train/Test из Bin@{HISTORICAL_BIN[:8]}.",
            trainer=trainer_for(kind), duration_ms=duration,
            pattern_family=family_for(case_id, source), normalization_mode=1,
            presynaptic_inhibition=is_psi, presynaptic_coefficient=2.5 if is_psi else 0.0,
            branch_nextseg=nextseg, posttrain_tuning=posttune, tipr_mode=tip_mode,
            source_config=source, source_mode="historical_exact", source_commit=HISTORICAL_BIN,
            worker_case=case_id, expect_tipr=old.get("expect_tipr", "canon"),
            expect_fires=old.get("expect_fires", "10000000"),
            skip_tipr_mid=old.get("skip_tipr_mid", True), train_t=int(old["train_t"]))
        history_map[case_id] = {
            "matrix_case_id": f"{wave}_HIST_{case_id}",
            "mapping": "exact source configuration; current-code rerun is a new observation",
            "source_config": source,
            "source_bin_commit": HISTORICAL_BIN,
            "historical_root_commit": HISTORICAL_ROOT,
            "historical_pulselib_commit": HISTORICAL_PULSE,
            "historical_console_sha256_prefix": HISTORICAL_CONSOLE,
            **history[case_id],
            "historical_run_bundle_sha256": "not found in Git for the 03/06/09 full49 runs",
        }
    for wave in hist_waves:
        wave_families = sorted({
            row["pattern_family"] for row in cases if row["wave"] == wave
        })
        waves[wave]["title"] = "Точная повторная проверка исторических конфигураций: " + ", ".join(wave_families)

    # PSI coefficient sweeps: Classic 0.5/2.7 and Branch 0.5/2.6/2.7.
    # The historical 2.6 case is also rerun exactly in W09-W15.
    coeff_templates = {
        0.5: "SelectivityPresynapticInhib/EXP01_preinh_050",
        2.6: "SelectivityPresynapticInhib/EXP14_preinh_260",
        2.7: "SelectivityPresynapticInhib/EXP15_preinh_270",
    }
    for wave, trainer, durations in (
        ("W16", "NNeuronTimeLearner", (25, 50)),
        ("W17", "NNeuronTimeLearner", (100, 480)),
        ("W18", "NNeuronTimeLearnerBranch", (25, 50)),
        ("W19", "NNeuronTimeLearnerBranch", (100, 480)),
    ):
        coeffs = (0.5, 2.7)
        for duration in durations:
            template_name = current_template(trainer, duration)
            for mode in (0, 1):
                for coeff in coeffs:
                    label = str(coeff).replace(".", "")
                    cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_N{mode}_PSI{label}"
                    add(wave, cid, template_name,
                        f"{trainer}: коэффициент пресинаптического торможения {coeff}, паттерн {duration} мс, NormalizationMode={mode}.",
                        trainer=trainer, duration_ms=duration, normalization_mode=mode,
                        presynaptic_inhibition=True, presynaptic_coefficient=coeff,
                        preinh_class_source=coeff_templates[coeff])

    for duration in (25, 50, 100, 480):
        template_name = current_template("NNeuronTimeLearnerBranch", duration)
        for mode in (0, 1):
            cid = f"W45_BR{duration}_N{mode}_PSI26"
            add("W45", cid, template_name,
                f"Branch: пресинаптическое торможение с коэффициентом 2.6, {duration} мс, NormalizationMode={mode}; совпадающая топология, NextSeg off.",
                trainer="NNeuronTimeLearnerBranch", duration_ms=duration,
                normalization_mode=mode, presynaptic_inhibition=True,
                presynaptic_coefficient=2.6,
                preinh_class_source=coeff_templates[2.6])

    # Five long-pattern PSI structures get a structural-mode counterpart.
    long_psi = ["psi31_200", "psi32_300", "psi33_300", "psi34_400", "psi35_400"]
    for case_id in long_psi:
        old = pv_cases[case_id]
        source = source_rel(old["root"])
        psi = case_id in {"psi31_200", "psi33_300", "psi35_400"}
        template_name = f"long_{case_id}"
        templates[template_name] = {"source": source, "preinh_source": source, "paired_source": source, "kind": "asym", "train_t": int(old["train_t"])}
        add("W20", f"W20_{case_id}_N0", template_name,
            f"Структурный режим на историческом длинном PSI-шаблоне {case_id}, {old['span_ms']} мс; исходный коэффициент и паттерн сохранены.",
            trainer="NNeuronTimeLearner", duration_ms=int(old["span_ms"]),
            pattern_family="PSI historical sweep", normalization_mode=0,
            presynaptic_inhibition=psi, presynaptic_coefficient=2.5 if psi else 0.0,
            source_config=source, train_t=int(old["train_t"]))

    # Rs/Rm upper-bound sweep, q=100 and 3000, with q=1000 as the base default.
    for wave, trainer in (("W21", "NNeuronTimeLearner"), ("W22", "NNeuronTimeLearnerBranch")):
        for duration in (25, 50, 100):
            template_name = current_template(trainer, duration)
            for q in (100.0, 3000.0):
                cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_N1_Q{int(q)}"
                add(wave, cid, template_name,
                    f"{trainer}: структурно-параметрическое обучение на {duration} мс с пределом Rs/Rm={int(q)}; контрольное штатное значение 1000 находится в W01-W04.",
                    trainer=trainer, duration_ms=duration, normalization_mode=1,
                    presynaptic_inhibition=False, max_rs_rm=q)

    # Initial Rs is deliberately varied only in parameter-training mode.
    for wave, trainer, duration in (
        ("W23", "NNeuronTimeLearner", 50), ("W24", "NNeuronTimeLearner", 480),
        ("W25", "NNeuronTimeLearnerBranch", 50), ("W26", "NNeuronTimeLearnerBranch", 480),
    ):
        template_name = current_template(trainer, duration)
        for psi in (False, True):
            for ratio in (1.0, 10.0, 1000.0):
                cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_PSI{'25' if psi else 'off'}_RS{int(ratio)}RM"
                add(wave, cid, template_name,
                    f"{trainer}: начальные TipSynapseResistance и SynapseResistanceBase={ratio:g}×ExcMembraneResistance до C++ reset, {duration} мс, PSI {'включено' if psi else 'выключено'}; NormalizationMode=1.",
                    trainer=trainer, duration_ms=duration, normalization_mode=1,
                    presynaptic_inhibition=psi, presynaptic_coefficient=2.5 if psi else 0.0,
                    initial_rs_to_rm=ratio)

    # D cases: one-factor controls, explicit membrane time constants and MaxLen escape.
    for wave, trainer, template_name in (
        ("W27", "NNeuronTimeLearner", "classic480"),
        ("W28", "NNeuronTimeLearnerBranch", "branch480"),
    ):
        variants = [
            ("BASE", {}, "исходная RC-модель и исходная оценка задержки"),
            ("DELAY5", {"xml_overrides": {"EstDelayPerSeg": "0.005"}}, "только EstDelayPerSeg=5 мс на сегмент"),
            ("RC5_DELAY5", {"relative_overrides": {"MembraneCapacity": 0.5}, "xml_overrides": {"EstDelayPerSeg": "0.005"}}, "RC=5 мс и EstDelayPerSeg=5 мс"),
            ("RC20_DELAY20", {"relative_overrides": {"MembraneCapacity": 2.0}, "xml_overrides": {"EstDelayPerSeg": "0.020"}}, "RC=20 мс и EstDelayPerSeg=20 мс"),
            ("MAXLEN150", {"xml_overrides": {"MaxDendriteLength": "150"}}, "MaxDendriteLength=150, остальные параметры исходные"),
        ]
        for suffix, overrides, description in variants:
            cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}480_D_{suffix}"
            add(wave, cid, template_name,
                f"D-диагностика для {trainer}: {description}; PSI off, NormalizationMode=1.",
                trainer=trainer, duration_ms=480, pattern_family="D long-pattern diagnostic",
                normalization_mode=1, presynaptic_inhibition=False,
                source_config=(templates[template_name]["source"] if suffix == "BASE" else templates[template_name]["source"]),
                preserve_classes=True, **overrides)

    # SyncTolerance: current, half, double; only time tolerance changes.
    for wave, trainer in (("W29", "NNeuronTimeLearner"), ("W30", "NNeuronTimeLearnerBranch")):
        for duration in (25, 480):
            template_name = current_template(trainer, duration)
            for factor, label in ((1.0, "CURRENT"), (0.5, "HALF"), (2.0, "DOUBLE")):
                cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_SYNC_{label}"
                add(wave, cid, template_name,
                    f"{trainer}: SyncTolerance {label.lower()} для паттерна {duration} мс; другие факторы фиксированы.",
                    trainer=trainer, duration_ms=duration, normalization_mode=1,
                    presynaptic_inhibition=False,
                    relative_overrides={"SyncTolerance": factor})

    # Peak-window margin: existing margin and a half-width window, without changing SyncTolerance.
    for wave, trainer in (("W31", "NNeuronTimeLearner"), ("W32", "NNeuronTimeLearnerBranch")):
        for duration in (25, 480):
            template_name = current_template(trainer, duration)
            for mode in (0, 1):
                for factor, label in ((1.0, "CURRENT"), (0.5, "HALF")):
                    cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_N{mode}_MARGIN_{label}"
                    add(wave, cid, template_name,
                        f"{trainer}: окно измерения пика {label.lower()}, {duration} мс, NormalizationMode={mode}; SyncTolerance не меняется.",
                        trainer=trainer, duration_ms=duration, normalization_mode=mode,
                        presynaptic_inhibition=False,
                        relative_overrides={"PeakMeasureMargin": factor})

    # Isolate the optional post-training calibration from C++ convergence.
    for wave, trainer in (("W33", "NNeuronTimeLearner"), ("W34", "NNeuronTimeLearnerBranch")):
        for duration in (25, 50):
            template_name = current_template(trainer, duration)
            for mode in (0, 1):
                for psi in (False, True):
                    cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}{duration}_N{mode}_PSI{'25' if psi else 'off'}_POST"
                    add(wave, cid, template_name,
                        f"{trainer}: PostTrain tuning включён после обучения, {duration} мс, NormalizationMode={mode}, PSI {'включено' if psi else 'выключено'}.",
                        trainer=trainer, duration_ms=duration, normalization_mode=mode,
                        presynaptic_inhibition=psi, presynaptic_coefficient=2.5 if psi else 0.0,
                        posttrain_tuning=True)

    # Explicit post-training TipR modes. Unsupported combinations are not silently added.
    for duration in (25, 480):
        template_name = current_template("NNeuronTimeLearner", duration)
        for mode, label in ((1, "CANON"), (2, "FLAT")):
            cid = f"W35_CL{duration}_N1_TIPR_{label}"
            add("W35", cid, template_name,
                f"Classic: PostTrain TipR режим {label.lower()} после структурно-параметрического обучения, {duration} мс, PSI off.",
                trainer="NNeuronTimeLearner", duration_ms=duration, normalization_mode=1,
                presynaptic_inhibition=False, posttrain_tuning=True, tipr_mode=mode)
    for duration in (25, 100):
        template_name = current_template("NNeuronTimeLearnerBranch", duration)
        for mode, label in ((1, "CANON"), (3, "KEEP"), (4, "SEARCH")):
            cid = f"W36_BR{duration}_N1_TIPR_{label}"
            add("W36", cid, template_name,
                f"Branch: PostTrain TipR режим {label.lower()} после структурно-параметрического обучения, {duration} мс, PSI off.",
                trainer="NNeuronTimeLearnerBranch", duration_ms=duration,
                normalization_mode=1, presynaptic_inhibition=False,
                posttrain_tuning=True, tipr_mode=mode)

    # Pack B/C comparisons, 25/100 ms, each trainer and structural mode.
    for wave, trainer in (("W37", "NNeuronTimeLearner"), ("W38", "NNeuronTimeLearnerBranch")):
        for duration in (25, 100):
            for pack in ("B", "C"):
                if trainer == "NNeuronTimeLearner":
                    src = f"SelectivityAsymRm/EXP_span{duration}ms_pack{pack}_gen"
                    pre = f"SelectivityAsymRm/EXP_span{duration}ms_pack{pack}_preinh"
                    kind = "asym"
                else:
                    src = f"SelectivityBranch/EXP_br_span{duration}_pack{pack}_gen_C1e9"
                    pre = f"SelectivityBranch/EXP_br_span{duration}_pack{pack}_preinh_C1e9"
                    kind = "branch"
                template_name = f"pack{pack}_{'classic' if kind == 'asym' else 'branch'}{duration}"
                templates[template_name] = {"source": src, "preinh_source": pre, "paired_source": pre, "kind": kind, "train_t": 640 if duration == 100 else 320}
                for mode in (0, 1):
                    cid = f"{wave}_{'CL' if kind == 'asym' else 'BR'}{duration}_PACK{pack}_N{mode}"
                    add(wave, cid, template_name,
                        f"{trainer}: проверка человечески маркированного Pack {pack} на {duration} мс, NormalizationMode={mode}, PSI off.",
                        trainer=trainer, duration_ms=duration, pattern_family=f"Pack {pack}",
                        normalization_mode=mode, presynaptic_inhibition=False)

    # Same four-pulse set, reversed order, with NextSeg disabled and PSI as a separate factor.
    for wave, norm in (("W39", 0), ("W40", 1)):
        for duration in (25, 50, 100, 480):
            template_name = current_template("NNeuronTimeLearnerBranch", duration)
            for psi in (False, True):
                cid = f"{wave}_BR{duration}_N{norm}_PSI{'25' if psi else 'off'}_REV"
                add(wave, cid, template_name,
                    f"Branch: те же четыре импульса в обратном порядке, {duration} мс, NormalizationMode={norm}, PSI {'включено' if psi else 'выключено'}, NextSeg off.",
                    trainer="NNeuronTimeLearnerBranch", duration_ms=duration,
                    normalization_mode=norm, presynaptic_inhibition=psi,
                    presynaptic_coefficient=2.5 if psi else 0.0,
                    reverse_pattern_order=True)

    # Replay the August FastResponse configurations with current C++ code. These
    # historical inputs form a distinct DissociationTC × MembraneCapacity family
    # and were not represented by the later Rm/Cm-only diagnostics. Each source
    # is pinned to the last Bin commit that changed its Train/Test inputs.
    fast_response_grid = [
        ("W46_HIST_FAST_D005_C1E9", "EXP00CtrlExp04", 0.005, 1.0e-9, "контрольный FastResponse с биологическими значениями D и C"),
        ("W46_HIST_FAST_D005_C5E10", "EXPD005C5e10", 0.005, 5.0e-10, "FastResponse: при D=0.005 уменьшена ёмкость до 5e-10 Ф"),
        ("W46_HIST_FAST_D002_C1E9", "EXPD002C1e9", 0.002, 1.0e-9, "FastResponse: при C=1e-9 Ф уменьшена постоянная диссоциации до 0.002 с"),
        ("W46_HIST_FAST_D002_C5E10", "EXPD002C5e10", 0.002, 5.0e-10, "FastResponse: D=0.002 с и C=5e-10 Ф"),
        ("W46_HIST_FAST_D002_C2_5E10", "EXPD002C25e11", 0.002, 2.5e-10, "FastResponse: D=0.002 с и C=2.5e-10 Ф"),
        ("W46_HIST_FAST_D001_C1E9", "EXPD001C1e9", 0.001, 1.0e-9, "FastResponse: при C=1e-9 Ф уменьшена постоянная диссоциации до 0.001 с"),
        ("W46_HIST_FAST_D001_C5E10", "EXPD001C5e10", 0.001, 5.0e-10, "FastResponse: D=0.001 с и C=5e-10 Ф"),
        ("W46_HIST_FAST_D001_C2_5E10", "EXPD001C25e11", 0.001, 2.5e-10, "FastResponse: D=0.001 с и C=2.5e-10 Ф"),
    ]
    for case_id, folder, dissociation_tc, capacity, description in fast_response_grid:
        source = f"SelectivityFastResponse/{folder}"
        template_name = f"fast_response_{folder}"
        templates[template_name] = {
            "source": source,
            "preinh_source": source,
            "paired_source": source,
            "kind": "asym",
            "train_t": 160,
        }
        add("W46", case_id, template_name,
            f"Точная повторная проверка исторического FastResponse: {description}; все остальные значения, включая паттерн и холодное состояние, копируются из проверенного источника.",
            trainer="NNeuronTimeLearner", duration_ms=480,
            pattern_family="FastResponse D×C", normalization_mode=1,
            presynaptic_inhibition=False, branch_nextseg=False,
            posttrain_tuning=False, source_config=source,
            source_mode="historical_exact", source_commit=latest_config_commit(source),
            historical_dissociation_tc_seconds=dissociation_tc,
            historical_membrane_capacity_farad=capacity,
            historical_tip_resistance_ohm=86_000_000.0, train_t=160)

    # PHASE10.3 made two manual TipR@Rmin copies of the weak-spike FastResponse
    # cases. Preserve those as independent conditions with the original inputs.
    for case_id, folder, base_case, description in (
        ("W47_HIST_FAST_D002_C1E9_TIPRMIN", "EXPD002C1e9_phase10_tiprmin", "W46_HIST_FAST_D002_C1E9", "PHASE10.3 TipR@Rmin copy of the D=0.002 s, C=1e-9 F case"),
        ("W47_HIST_FAST_D001_C1E9_TIPRMIN", "EXPD001C1e9_phase10_tiprmin", "W46_HIST_FAST_D001_C1E9", "PHASE10.3 TipR@Rmin copy of the D=0.001 s, C=1e-9 F case"),
    ):
        source = f"SelectivityFastResponse/{folder}"
        template_name = f"fast_response_{folder}"
        templates[template_name] = {
            "source": source,
            "preinh_source": source,
            "paired_source": source,
            "kind": "asym",
            "train_t": 160,
        }
        add("W47", case_id, template_name,
            f"Точная повторная проверка исторического случая: {description}; ручной TipR равен 20 МОм × 3 и 86 МОм на одном конце, ResistanceMin=20 МОм.",
            trainer="NNeuronTimeLearner", duration_ms=480,
            pattern_family="FastResponse D×C + manual TipR@Rmin", normalization_mode=1,
            presynaptic_inhibition=False, branch_nextseg=False,
            posttrain_tuning=False, source_config=source,
            source_mode="historical_exact", source_commit=latest_config_commit(source),
            historical_tip_resistance_pattern_ohm="20000000×3 + 86000000",
            historical_resistance_min_ohm=20_000_000.0,
            repeat_of=base_case, train_t=160)

    # Independently alter membrane R and C to quantify their combined time-constant effect.
    for wave, trainer in (("W41", "NNeuronTimeLearner"), ("W42", "NNeuronTimeLearnerBranch")):
        template_name = current_template(trainer, 50)
        for tag, factor, label in (
            ("ExcMembraneResistance", 0.5, "RM_HALF"),
            ("ExcMembraneResistance", 2.0, "RM_DOUBLE"),
            ("MembraneCapacity", 0.5, "CM_HALF"),
            ("MembraneCapacity", 2.0, "CM_DOUBLE"),
        ):
            cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}50_{label}"
            add(wave, cid, template_name,
                f"{trainer}: изменить только {tag} в {factor:g} раза, сохранив остальные факторы; длительность 50 мс, NormalizationMode=1.",
                trainer=trainer, duration_ms=50, normalization_mode=1,
                presynaptic_inhibition=False,
                relative_overrides={tag: factor})

    # Reproducibility repeats are separate run IDs but point to the same immutable factors.
    for wave, trainer, template_name, duration, source_case in (
        ("W43", "NNeuronTimeLearner", "classic50", 50, "W01_CL50_N1_PSI25"),
        ("W44", "NNeuronTimeLearnerBranch", "branch50", 50, "W03_BR50_N1_PSIoff"),
    ):
        for repeat in (1, 2):
            cid = f"{wave}_{'CL' if trainer == 'NNeuronTimeLearner' else 'BR'}50_REPEAT{repeat}"
            add(wave, cid, template_name,
                f"Повтор {repeat} контрольного случая {source_case} с теми же входами и параметрами; чистый reset и отдельный run ID.",
                trainer=trainer, duration_ms=duration, normalization_mode=1,
                presynaptic_inhibition=(trainer == "NNeuronTimeLearner"),
                presynaptic_coefficient=2.5 if trainer == "NNeuronTimeLearner" else 0.0,
                repeat_of=source_case, repeat_index=repeat)

    if len(cases) != 312:
        counts = Counter(c["wave"] for c in cases)
        raise ValueError(f"matrix must contain exactly 312 rows; got {len(cases)}; waves={dict(counts)}")
    seen_ids = [c["id"] for c in cases]
    if len(set(seen_ids)) != len(seen_ids):
        raise ValueError("duplicate case IDs in generated registry")
    counts = Counter(c["wave"] for c in cases)
    oversized = {wave: count for wave, count in counts.items() if count > 8}
    if oversized:
        raise ValueError(f"wave size exceeds 8: {oversized}")
    missing_hist = set(history) - set(history_map)
    if missing_hist:
        raise ValueError(f"historical entries are not mapped: {sorted(missing_hist)}")

    registry = {
        "schema": 2,
        "matrix_version": "2026-10-10-full312-history-nextseg-psi",
        "description": "312 cases on the current C++ trainer implementation. Eight cases add the requested NextSeg×PSI interaction; ten cases add missing historical FastResponse D×C and manual TipR@Rmin conditions. Full execution is not part of preparation.",
        "current_source_commits": {
            "root": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
            "Bin": subprocess.check_output(["git", "-C", str(BIN_ROOT), "rev-parse", "HEAD"], text=True).strip(),
            "PulseLib": subprocess.check_output(["git", "-C", str(ROOT / "Libraries" / "Nmsdk-PulseLib"), "rev-parse", "HEAD"], text=True).strip(),
        },
        "historical_full49_source": {"root": HISTORICAL_ROOT, "Bin": HISTORICAL_BIN, "PulseLib": HISTORICAL_PULSE, "Console_sha256_prefix": HISTORICAL_CONSOLE},
        "max_parallel_console_processes": 8,
        "queue_order": [
            *[f"W{i:02d}" for i in range(1, 9)],
            "W46", "W47",
            *[f"W{i:02d}" for i in range(9, 20)],
            "W45",
            *[f"W{i:02d}" for i in range(20, 45)],
        ],
        "wave_descriptions": waves,
        "templates": templates,
        "cases": cases,
        "history_coverage_file": "historical_coverage.json",
        "queue_policy": "Run no more than eight Console instances. Complete the current wave and save/commit its report. Any C++ refusal, failed quality, missed target, evaluator failure, or missing result pauses the queue before the next wave pending diagnosis. A zero process exit alone never counts as a metrics pass.",
    }
    coverage = {
        "schema": 1,
        "historical_unique_case_count": len(history_map),
        "all_historical_unique_conditions_mapped": set(history_map) == set(history),
        "historical_campaigns": {
            "2026-10-03": {"root": "c0b69efc0f61590a5cdbc49587ef20b4c54bdf3c", "Bin": "babdba99786f95b31ea1967052f3b16fab50acd5", "PulseLib": "b29b595a137b0bc492c4f2eeee100fac943e47ef", "Console": "e018c02430d905be…"},
            "2026-10-06": {"root": "59d2100c42620f1e462d5aabfc3e77077d52126f", "Bin": "6633b357d1d5e254c1f75f3d6d999f9597b38c97", "PulseLib": "b32d7158527beb8c16d25a99fb4f58172ee2ea59", "Console": "8589daff6d131c9b…"},
            "2026-10-09": {"root": HISTORICAL_ROOT, "Bin": HISTORICAL_BIN, "PulseLib": HISTORICAL_PULSE, "Console": HISTORICAL_CONSOLE},
        },
        "cases": history_map,
        "coverage_notes": [
            "The 49 legacy case IDs are unique historical source configurations. The Oct 3/6/9 repeated campaigns are attached as observations to the same condition, not counted as new conditions.",
            "The 03/06/09 full49 run bundles do not preserve per-run input SHA-256 in Git; the source Bin commit and config path are known, but exact worker-copy identity is not proven.",
            "Historical GoldTest scores apply to the historical stored weights and are not outcomes from the current-code rerun.",
            "The 09-Oct `br100_search` result was incomplete (rc=137); current C++ convergence remains historically unknown for that observation.",
            "Branch NextSeg×PSI is represented by dedicated W07/W08 Train/Test configs. The NextSeg topology is kept fixed while PSI synapse classes are mapped to coefficient-2.5 classes by synapse type; static source validation checks each mapping, but runtime behavior still requires the future C++ run.",
            "The 11 historical FastResponse Train/Test folders are represented by ten current-code reruns in W46/W47: eight effective D×C cells and two manual TipR@Rmin variants. EXPD005C25e11 is recorded as a duplicate effective condition because the historical UploadClass set C=5e-10 F, as documented in SelectivityFastResponse/REPORT.md.",
        ],
    }
    return registry, coverage


def validate_sources(registry: dict[str, Any]) -> None:
    runner_ns = runpy.run_path(str(BASE / "scripts" / "timelearner_matrix.py"), run_name="timelearner_source_validation")
    toggle = runner_ns["toggle_inhibition"]
    set_all_tags = runner_ns["set_all_tags"]
    apply_xml_factors = runner_ns["apply_xml_factors"]
    missing = []
    invalid = []
    for case in registry["cases"]:
        template = registry["templates"][case["template"]]
        source = case.get("source_config") or template.get("paired_source", template["preinh_source"])
        preinh = case.get("preinh_topology_source") or template["preinh_source"]
        class_source = case.get("preinh_class_source") or preinh
        if not (BASE / source).is_dir():
            missing.append((case["id"], source))
        if not (BASE / preinh).is_dir():
            missing.append((case["id"], preinh))
        if not (BASE / class_source).is_dir():
            missing.append((case["id"], class_source))
            continue
        if case.get("source_mode") == "historical_exact":
            continue
        if case.get("reverse_pattern_order"):
            for side in ("Train", "Test"):
                model = BASE / source / side / "Model_00.xml"
                content = model.read_text(encoding="utf-8") if model.is_file() else ""
                if not re.search(r'<MatrixData\b[^>]*Rows="4"[^>]*>', content):
                    invalid.append((case["id"], side, "Model_00.xml", "four-row MatrixData source not found"))
        membrane_resistance = None
        if (
            case.get("initial_rs_to_rm") is not None
            or case.get("initial_rs_trainable_to_rm") is not None
        ):
            for rel in ("Model_00.xml", "Parameters_00.xml"):
                p = BASE / source / "Train" / rel
                if not p.is_file():
                    continue
                values = runner_ns["tag_values"](p.read_text(encoding="utf-8"), "ExcMembraneResistance")
                if not values:
                    values = runner_ns["tag_values"](p.read_text(encoding="utf-8"), "RestingResistance")
                if values:
                    membrane_resistance = float(values[0].replace(",", "."))
                    break
        for side in ("Train", "Test"):
            for rel in ("Model_00.xml", "Parameters_00.xml"):
                path = BASE / source / side / rel
                companion = BASE / preinh / side / rel
                class_companion = BASE / class_source / side / rel
                if not path.is_file() or not companion.is_file() or not class_companion.is_file():
                    absent = path if not path.is_file() else companion if not companion.is_file() else class_companion
                    missing.append((case["id"], str(absent)))
                    continue
                raw = path.read_text(encoding="utf-8")
                paired = companion.read_text(encoding="utf-8")
                class_text = class_companion.read_text(encoding="utf-8")
                sibling = BASE / class_source / side / ("Parameters_00.xml" if rel == "Model_00.xml" else "Model_00.xml")
                if sibling.is_file():
                    class_text += "\n" + sibling.read_text(encoding="utf-8")
                try:
                    if not case.get("preserve_classes"):
                        raw = toggle(
                            raw, paired, bool(case.get("presynaptic_inhibition")),
                            float(case.get("presynaptic_coefficient", 2.5)),
                            class_template_text=class_text,
                            require_flags=(side == "Train"),
                            force_presynaptic_classes=bool(case.get("force_presynaptic_classes")),
                        )
                    raw = set_all_tags(raw, "NormalizationMode", str(case["normalization_mode"]))
                    raw = apply_xml_factors(raw, case, side=side, membrane_resistance=membrane_resistance)
                    if side == "Train" and case.get("max_rs_rm") is not None and int(case["normalization_mode"]) != 1:
                        raise ValueError("Rs/Rm ceiling sweep requires NormalizationMode=1")
                except Exception as exc:
                    invalid.append((case["id"], side, rel, str(exc)))
    if missing or invalid:
        raise ValueError(f"invalid matrix sources/factors; missing={missing[:12]}, invalid={invalid[:20]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true", help="write registry and all per-case Train/Test snapshots; does not run training")
    args = parser.parse_args()
    registry, coverage = build_registry()
    validate_sources(registry)
    MANIFEST.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HISTORY_COVERAGE.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.materialize:
        runner_ns = runpy.run_path(str(BASE / "scripts" / "timelearner_matrix.py"), run_name="timelearner_prepare_294")
        prepare_wave = runner_ns["prepare_wave"]
        for wave in registry["queue_order"]:
            # Only the expanded NextSeg waves changed case factors; all other
            # snapshots keep their inputs and refresh the manifest hash in place.
            prepare_wave(wave, refresh=(wave in {"W07", "W08"}))
        ready_rows = []
        for case in registry["cases"]:
            path = MATRIX / case["wave"] / "inputs" / case["id"]
            template = registry["templates"][case["template"]]
            source_relpath = case.get("source_config") or template.get("paired_source", template["preinh_source"])

            def source_interface_sha256(side: str) -> str | None:
                relpath = f"Configs/SpikeSamples/StructTrain/{source_relpath}/{side}/Interface.xml"
                if case.get("source_mode") == "historical_exact":
                    commit = case.get("source_commit")
                    if not commit:
                        return None
                    result = subprocess.run(
                        ["git", "-C", str(BIN_ROOT), "show", f"{commit}:{relpath}"],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    )
                    return sha256_bytes(result.stdout) if result.returncode == 0 else None
                source_interface = BASE / source_relpath / side / "Interface.xml"
                return sha256_bytes(source_interface.read_bytes()) if source_interface.is_file() else None

            def gui_summary(side: str) -> dict[str, Any]:
                interface = path / side / "Interface.xml"
                if not interface.is_file():
                    return {"interface": False, "graph_count": [], "chart_titles": [], "interface_sha256": None, "source_sha256": None, "matches_source": False}
                interface_sha = sha256_bytes(interface.read_bytes())
                source_sha = source_interface_sha256(side)
                try:
                    root = ET.parse(interface).getroot()
                except ET.ParseError as exc:
                    return {"interface": True, "graph_count": [], "chart_titles": [], "interface_sha256": interface_sha, "source_sha256": source_sha, "matches_source": interface_sha == source_sha, "parse_error": str(exc)}
                return {
                    "interface": True,
                    "graph_count": [int(x.text.strip()) for x in root.iter("GraphCount") if x.text and x.text.strip().isdigit()],
                    "chart_titles": [(x.text or "").strip() for x in root.iter("ChartTitle") if (x.text or "").strip()],
                    "interface_sha256": interface_sha,
                    "source_sha256": source_sha,
                    "matches_source": interface_sha == source_sha,
                }
            train_gui = gui_summary("Train")
            test_gui = gui_summary("Test")
            ready_rows.append({
                "id": case["id"], "wave": case["wave"],
                "train_project": (path / "Train" / "Project.ini").is_file(),
                "test_project": (path / "Test" / "Project.ini").is_file(),
                "train_gui": train_gui,
                "test_gui": test_gui,
                "input_manifest": (path / "matrix_input_manifest.json").is_file(),
                "train_path": f"TimeLearnerMatrix/{case['wave']}/inputs/{case['id']}/Train/Project.ini",
                "test_path": f"TimeLearnerMatrix/{case['wave']}/inputs/{case['id']}/Test/Project.ini",
            })
        missing = [x["id"] for x in ready_rows if not (
            x["train_project"] and x["test_project"] and x["input_manifest"]
            and x["train_gui"]["interface"] and x["test_gui"]["interface"]
            and x["train_gui"]["graph_count"] and x["test_gui"]["graph_count"]
            and x["train_gui"]["chart_titles"] and x["test_gui"]["chart_titles"]
            and x["train_gui"]["matches_source"] and x["test_gui"]["matches_source"]
        )]
        if missing:
            raise RuntimeError(f"missing per-case Train/Test files or GUI plots after materialization: {missing}")
        readiness = {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "case_count": len(ready_rows),
            "all_cases_have_train_test_and_gui": True,
            "full_matrix_execution_performed": False,
            "cases": ready_rows,
        }
        READINESS.write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "case_count": len(registry["cases"]),
        "wave_count": len(registry["queue_order"]),
        "max_wave_size": max(Counter(c["wave"] for c in registry["cases"]).values()),
        "historical_case_count": coverage["historical_unique_case_count"],
        "materialized": bool(args.materialize),
        "full_matrix_execution_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
