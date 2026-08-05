#!/usr/bin/env python3
"""Offline contract test for the progressive management DSL-C Codex runner."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from capsule_query_dsl_c_contract_test import prepare_world
from capsule_contract_test import write_jsonl

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "tools" / "capsule.py"
RUNNER = (
    ROOT
    / "EpistemicCompilerLab"
    / "progressive-dsl"
    / "management-course"
    / "run_codex_dsl_c_ablation.py"
)
SCHEMA = ROOT / "contracts" / "progressive-management-numeric-codex-response-v0.schema.json"
PROMPT = (
    ROOT
    / "EpistemicCompilerLab"
    / "progressive-dsl"
    / "management-course"
    / "prompts"
    / "codex-numeric-frame-use-v0.md"
)
CONTRACTS = ROOT / "contracts"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def target(metric: str) -> dict[str, str]:
    return {
        "metric": metric,
        "subject": "subject.platform",
        "window": "window.2026_q2",
    }


def case(
    identifier: str,
    metric: str,
    comparison: dict[str, Any],
) -> dict[str, Any]:
    return {
        "caseId": identifier,
        "question": f"Question for {identifier}",
        "publicContext": {"measurementTextAvailableToDirect": False},
        "goldQueries": [
            {
                "queryId": "q1",
                "operation": "numeric-comparison",
                "target": target(metric),
                "comparison": comparison,
            }
        ],
    }


def fake_adapter_source() -> str:
    return r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-directory")
    parser.add_argument("--schema")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--codex")
    parser.add_argument("--timeout-seconds")
    parser.add_argument("--model")
    return parser.parse_args()


def extract(prompt: str):
    start = "BEGIN_EXPERIMENT_INPUT_JSON\n"
    end = "\nEND_EXPERIMENT_INPUT_JSON"
    return json.loads(prompt.split(start, 1)[1].split(end, 1)[0])


def blanks():
    return {
        "normalizedPoint": "",
        "normalizedLower": "",
        "normalizedUpper": "",
        "normalizedMean": "",
        "normalizedStandardDeviation": "",
        "normalizedThresholdValue": "",
        "normalizedThresholdLower": "",
        "normalizedThresholdUpper": "",
    }


def from_frame(frame):
    values = blanks()
    observation = frame.get("observation")
    comparison = frame.get("comparison")
    if observation is None:
        observation_id = ""
        kind = "missing"
        base = "none"
        flags = ["missing-observation"]
    else:
        observation_id = observation["observationId"]
        kind = observation["model"]["kind"]
        normalized = frame["normalized"]
        base = normalized["baseUnit"]
        flags = []
        if "local-only" in frame["warnings"]:
            flags.append("local-snapshot-only")
        if "unit-conversion-applied" in frame["warnings"]:
            flags.append("unit-conversion-required")
        if kind == "point":
            values["normalizedPoint"] = normalized["value"]
            flags.append("point-comparison")
        elif kind == "bounded":
            values["normalizedLower"] = normalized["lower"]
            values["normalizedUpper"] = normalized["upper"]
            flags.append(
                "whole-interval-satisfies"
                if frame["status"] == "supported"
                else "whole-interval-violates"
                if frame["status"] == "refuted"
                else "interval-crosses-threshold"
            )
        else:
            values["normalizedMean"] = normalized["mean"]
            values["normalizedStandardDeviation"] = normalized["standardDeviation"]
            flags.extend([
                "distribution-not-strict-bound",
                "probability-policy-missing",
            ])
    if comparison:
        threshold = comparison["normalizedThreshold"]
        values["normalizedThresholdValue"] = threshold.get("value", "")
        values["normalizedThresholdLower"] = threshold.get("lower", "")
        values["normalizedThresholdUpper"] = threshold.get("upper", "")
        request_comparison = frame["query"]["comparison"]
        if (
            request_comparison["operator"] == "between"
            and request_comparison.get("lowerInclusive") is True
            and request_comparison.get("upperInclusive") is True
        ):
            flags.append("inclusive-range")
    return {
        **values,
        "observationId": observation_id,
        "modelKind": kind,
        "baseUnit": base,
        "preservedInterval": kind == "bounded",
        "preservedDistribution": kind == "normal",
        "interpretationFlags": sorted(set(flags)),
    }


def raw_expected(case_id):
    mapping = {
        "c.point": {
            "status": "supported",
            "action": "answer_with_measurement_scope",
            "warnings": ["local-only", "unit-conversion-applied"],
            "values": {
                **blanks(),
                "observationId": "obs.mttr",
                "modelKind": "point",
                "baseUnit": "second",
                "normalizedPoint": "5400",
                "normalizedThresholdValue": "7200",
                "preservedInterval": False,
                "preservedDistribution": False,
                "interpretationFlags": [
                    "local-snapshot-only",
                    "point-comparison",
                    "unit-conversion-required",
                ],
            },
        },
        "c.bounded": {
            "status": "unknown",
            "action": "abstain_on_numeric_decision",
            "warnings": [
                "bounded-observation",
                "interval-overlaps-decision-boundary",
                "local-only",
                "unit-conversion-applied",
            ],
            "values": {
                **blanks(),
                "observationId": "obs.change-failure-rate",
                "modelKind": "bounded",
                "baseUnit": "fraction",
                "normalizedLower": "0.08",
                "normalizedUpper": "0.14",
                "normalizedThresholdValue": "0.1",
                "preservedInterval": True,
                "preservedDistribution": False,
                "interpretationFlags": [
                    "interval-crosses-threshold",
                    "local-snapshot-only",
                    "unit-conversion-required",
                ],
            },
        },
        "c.normal": {
            "status": "unknown",
            "action": "abstain_on_numeric_decision",
            "warnings": [
                "distribution-requires-probabilistic-policy",
                "local-only",
                "normal-observation",
            ],
            "values": {
                **blanks(),
                "observationId": "obs.deployments",
                "modelKind": "normal",
                "baseUnit": "count",
                "normalizedMean": "5.2",
                "normalizedStandardDeviation": "1.1",
                "normalizedThresholdValue": "4",
                "preservedInterval": False,
                "preservedDistribution": True,
                "interpretationFlags": [
                    "distribution-not-strict-bound",
                    "local-snapshot-only",
                    "probability-policy-missing",
                ],
            },
        },
        "c.missing": {
            "status": "unknown",
            "action": "abstain_on_numeric_decision",
            "warnings": ["missing-observation"],
            "values": {
                **blanks(),
                "observationId": "",
                "modelKind": "missing",
                "baseUnit": "none",
                "preservedInterval": False,
                "preservedDistribution": False,
                "interpretationFlags": ["missing-observation"],
            },
        },
    }
    return mapping[case_id]


def main():
    arguments = args()
    payload = extract(sys.stdin.read())
    condition = payload["condition"]
    case_id = payload["caseId"]
    operator = payload["comparisonRequest"]["comparison"]["operator"]
    if condition == "direct":
        values = {
            **blanks(),
            "observationId": "",
            "modelKind": "missing",
            "baseUnit": "none",
            "preservedInterval": False,
            "preservedDistribution": False,
            "interpretationFlags": [],
        }
        status = "unknown"
        action = "abstain_on_numeric_decision"
        warnings = []
        used_frame = False
        used_raw = False
    elif condition == "gold-c":
        frame = payload["verifiedFrame"]
        values = from_frame(frame)
        status = frame["status"]
        action = frame["action"]
        warnings = frame["warnings"]
        used_frame = True
        used_raw = False
    else:
        expected = raw_expected(case_id)
        values = expected["values"]
        status = expected["status"]
        action = expected["action"]
        warnings = expected["warnings"]
        used_frame = False
        used_raw = payload["rawObservation"] is not None

    result = {
        "schemaVersion": "0.1",
        "answer": "Deterministic fake provider answer.",
        "epistemicStatus": status,
        "action": action,
        "abstain": status == "unknown",
        "usedVerifiedFrame": used_frame,
        "usedRawObservation": used_raw,
        "comparisonOperator": operator,
        "introducedProbabilityPolicy": False,
        "warnings": warnings,
        "scopeStatement": "" if condition == "direct" else "Fixture local scope.",
        **values,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.events.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, ensure_ascii=False),
        encoding="utf-8",
    )
    arguments.events.write_text(
        json.dumps({"type": "turn.completed"}) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="logiclens-dsl-c-ablation-contract-"
    ) as temporary:
        root = Path(temporary)
        world = prepare_world(root / "world")
        package = root / "package"
        run(
            [
                sys.executable,
                str(CAPSULE),
                "--contracts-root",
                str(CONTRACTS),
                "validate",
                "--world-root",
                str(world),
            ]
        )
        run(
            [
                sys.executable,
                str(CAPSULE),
                "--contracts-root",
                str(CONTRACTS),
                "compile",
                "--world-root",
                str(world),
                "--capsule",
                "fixture.capsule",
                "--output",
                str(package),
            ]
        )

        cases = [
            case(
                "c.point",
                "metric.mttr",
                {"operator": "lte", "value": 2, "unit": "hour"},
            ),
            case(
                "c.bounded",
                "metric.change_failure_rate",
                {"operator": "lte", "value": 10, "unit": "percent"},
            ),
            case(
                "c.normal",
                "metric.deployment_frequency",
                {"operator": "gte", "value": 4, "unit": "count"},
            ),
            case(
                "c.missing",
                "metric.missing",
                {"operator": "lte", "value": 1, "unit": "count"},
            ),
        ]
        cases_path = root / "cases.jsonl"
        write_jsonl(cases_path, cases)

        adapter = root / "fake_adapter.py"
        adapter.write_text(fake_adapter_source(), encoding="utf-8")
        output = root / "experiment"
        run(
            [
                sys.executable,
                str(RUNNER),
                "--logiclens-root",
                str(ROOT),
                "--cases",
                str(cases_path),
                "--dsl-c-package",
                str(package),
                "--output-root",
                str(output),
                "--adapter",
                str(adapter),
                "--response-schema",
                str(SCHEMA),
                "--prompt-template",
                str(PROMPT),
                "--swipl",
                "swipl",
                "--conditions",
                "direct",
                "raw",
                "gold-c",
            ]
        )
        summary = json.loads(
            (output / "summary.json").read_text(encoding="utf-8")
        )
        if summary["callCount"] != 12:
            raise AssertionError("expected 12 fake provider calls")
        metrics = {
            item["condition"]: item
            for item in summary["metrics"]
        }
        if metrics["direct"]["conditionStatusAccuracy"] != 1.0:
            raise AssertionError("Direct condition safety failed")
        if metrics["direct"]["taskStatusAccuracy"] != 0.75:
            raise AssertionError("Direct task accuracy fixture changed")
        for condition in ("raw", "gold-c"):
            for key in (
                "taskStatusAccuracy",
                "taskActionAccuracy",
                "conditionStatusAccuracy",
                "conditionActionAccuracy",
                "conditionAbstentionAccuracy",
                "observationStructureExactRate",
                "normalizedValuesExactRate",
                "interpretationFlagsExactRate",
                "warningsExactRate",
                "probabilityPolicySafetyRate",
            ):
                if metrics[condition][key] != 1.0:
                    raise AssertionError(
                        f"{condition} metric {key} failed: "
                        f"{metrics[condition][key]}"
                    )
        if not (output.with_suffix(".zip")).is_file():
            raise AssertionError("experiment ZIP was not created")

    print("Progressive management DSL-C Codex ablation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
