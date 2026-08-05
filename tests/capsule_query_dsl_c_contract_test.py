#!/usr/bin/env python3
"""Contract tests for typed observation DSL-C queries."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from capsule_contract_test import build_fixture, write_json, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "tools" / "capsule.py"
QUERY = ROOT / "tools" / "capsule_query_dsl_c.py"
CONTRACTS = ROOT / "contracts"


def run(
    command: list[str],
    *,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_success and completed.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    if not expect_success and completed.returncode == 0:
        raise AssertionError(
            f"command unexpectedly succeeded: {' '.join(command)}"
        )
    return completed


def observations() -> list[dict[str, Any]]:
    common = {
        "schemaVersion": "0.1",
        "provenance": ["fixture-source#measurement"],
        "generalisability": "local",
        "scope": {"organisation": "Fixture", "window": "2026-Q2"},
    }
    return [
        {
            **common,
            "observationId": "obs.mttr",
            "target": {
                "metric": "metric.mttr",
                "subject": "subject.platform",
                "window": "window.2026_q2",
            },
            "model": {"kind": "point", "value": 90, "unit": "minute"},
            "dependencyGroup": "measurement.incident-system",
        },
        {
            **common,
            "observationId": "obs.change-failure-rate",
            "target": {
                "metric": "metric.change_failure_rate",
                "subject": "subject.platform",
                "window": "window.2026_q2",
            },
            "model": {
                "kind": "bounded",
                "lower": 8,
                "upper": 14,
                "unit": "percent",
                "lowerInclusive": True,
                "upperInclusive": True,
            },
            "dependencyGroup": "measurement.deployment-system",
        },
        {
            **common,
            "observationId": "obs.availability",
            "target": {
                "metric": "metric.availability",
                "subject": "subject.platform",
                "window": "window.2026_q2",
            },
            "model": {
                "kind": "bounded",
                "lower": 99.91,
                "upper": 99.96,
                "unit": "percent",
                "lowerInclusive": True,
                "upperInclusive": True,
            },
            "dependencyGroup": "measurement.monitoring-system",
        },
        {
            **common,
            "observationId": "obs.deployments",
            "target": {
                "metric": "metric.deployment_frequency",
                "subject": "subject.platform",
                "window": "window.2026_q2",
            },
            "model": {
                "kind": "normal",
                "mean": 5.2,
                "standardDeviation": 1.1,
                "unit": "count",
            },
            "dependencyGroup": "measurement.deployment-system",
        },
        {
            **common,
            "observationId": "obs.incidents",
            "target": {
                "metric": "metric.incident_count",
                "subject": "subject.platform",
                "window": "window.2026_q2",
            },
            "model": {"kind": "point", "value": 3, "unit": "count"},
            "dependencyGroup": "measurement.incident-system",
        },
    ]


def prepare_world(root: Path, rows: list[dict[str, Any]] | None = None) -> Path:
    world = build_fixture(root)
    write_json(
        world / "semantic" / "vocabulary.json",
        {
            "schemaVersion": "0.1",
            "concepts": [
                *[
                    {
                        "id": identifier,
                        "kind": "management_metric",
                    }
                    for identifier in (
                        "metric.mttr",
                        "metric.change_failure_rate",
                        "metric.availability",
                        "metric.deployment_frequency",
                        "metric.incident_count",
                        "metric.missing",
                    )
                ],
                {
                    "id": "subject.platform",
                    "kind": "measurement_subject",
                },
                {
                    "id": "window.2026_q2",
                    "kind": "time_window",
                },
            ],
        },
    )
    capsule_path = world / "capsules" / "fixture" / "capsule.json"
    capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
    capsule["preparedFiles"].append(
        {
            "path": "prepared/observations.jsonl",
            "kind": "observations",
        }
    )
    write_json(capsule_path, capsule)
    write_jsonl(
        world / "capsules" / "fixture" / "prepared" / "observations.jsonl",
        observations() if rows is None else rows,
    )
    return world


def compile_package(world: Path, package: Path) -> None:
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


def request(
    package: Path,
    payload: dict[str, Any],
    *,
    expect_success: bool = True,
) -> dict[str, Any] | subprocess.CompletedProcess[str]:
    request_path = package.parent / "request.json"
    request_path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    completed = run(
        [
            sys.executable,
            str(QUERY),
            "--contracts-root",
            str(CONTRACTS),
            "--package",
            str(package),
            "--request",
            str(request_path),
            "--swipl",
            "swipl",
        ],
        expect_success=expect_success,
    )
    if not expect_success:
        return completed
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise AssertionError("DSL-C result must be an object")
    return value


def target(metric: str) -> dict[str, str]:
    return {
        "metric": metric,
        "subject": "subject.platform",
        "window": "window.2026_q2",
    }


def query_payload(
    metric: str,
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-C",
        "operation": (
            "observation" if comparison is None else "numeric-comparison"
        ),
        "target": target(metric),
    }
    if comparison is not None:
        value["comparison"] = comparison
    return value


def assert_status(
    package: Path,
    metric: str,
    comparison: dict[str, Any],
    expected: str,
) -> dict[str, Any]:
    result = request(package, query_payload(metric, comparison))
    assert isinstance(result, dict)
    if result["status"] != expected:
        raise AssertionError(
            f"{metric}: expected {expected}, got {result['status']}"
        )
    if not result["runtime"]["verifiedAgainstPrologKernel"]:
        raise AssertionError("result was not cross-verified")
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="logiclens-dsl-c-test-") as temporary:
        root = Path(temporary)
        world = prepare_world(root / "primary")
        package = root / "package"
        compile_package(world, package)

        observed = request(package, query_payload("metric.mttr"))
        assert isinstance(observed, dict)
        if observed["status"] != "observed":
            raise AssertionError("observation operation did not return observed")
        if observed["normalized"]["value"] != "5400":
            raise AssertionError("minute-to-second conversion is incorrect")

        refuted = assert_status(
            package,
            "metric.mttr",
            {"operator": "lte", "value": 1, "unit": "hour"},
            "refuted",
        )
        if refuted["comparison"]["normalizedThreshold"]["value"] != "3600":
            raise AssertionError("hour threshold normalization is incorrect")

        overlap = assert_status(
            package,
            "metric.change_failure_rate",
            {"operator": "lte", "value": 10, "unit": "percent"},
            "unknown",
        )
        if "interval-overlaps-decision-boundary" not in overlap["warnings"]:
            raise AssertionError("overlap warning is missing")

        availability = assert_status(
            package,
            "metric.availability",
            {"operator": "gte", "value": 0.999, "unit": "fraction"},
            "supported",
        )
        if availability["normalized"]["lower"] != "0.9991":
            raise AssertionError("percent-to-fraction conversion is incorrect")

        normal = assert_status(
            package,
            "metric.deployment_frequency",
            {"operator": "gte", "value": 4, "unit": "count"},
            "unknown",
        )
        if (
            "distribution-requires-probabilistic-policy"
            not in normal["warnings"]
        ):
            raise AssertionError("normal-policy warning is missing")

        between = assert_status(
            package,
            "metric.incident_count",
            {
                "operator": "between",
                "lower": 0,
                "upper": 5,
                "unit": "count",
                "lowerInclusive": True,
                "upperInclusive": True,
            },
            "supported",
        )
        if between["comparison"]["operator"] != "between":
            raise AssertionError("between comparison was not preserved")

        missing = assert_status(
            package,
            "metric.missing",
            {"operator": "lte", "value": 1, "unit": "count"},
            "unknown",
        )
        if missing["observation"] is not None:
            raise AssertionError("missing observation must remain null")

        request(
            package,
            query_payload(
                "metric.incident_count",
                {"operator": "lte", "value": 1, "unit": "hour"},
            ),
            expect_success=False,
        )
        undeclared = query_payload(
            "metric.not_declared",
            {"operator": "lte", "value": 1, "unit": "count"},
        )
        request(package, undeclared, expect_success=False)

        deterministic_payload = query_payload(
            "metric.change_failure_rate",
            {"operator": "lte", "value": 10, "unit": "percent"},
        )
        first = request(package, deterministic_payload)
        second = request(package, deterministic_payload)
        if first != second:
            raise AssertionError("DSL-C query output is not deterministic")

        duplicate_rows = observations()
        duplicate = dict(duplicate_rows[0])
        duplicate["observationId"] = "obs.mttr.duplicate"
        duplicate_rows.append(duplicate)
        duplicate_world = prepare_world(
            root / "duplicate",
            rows=duplicate_rows,
        )
        duplicate_package = root / "duplicate-package"
        compile_package(duplicate_world, duplicate_package)
        request(
            duplicate_package,
            query_payload("metric.mttr"),
            expect_success=False,
        )

        packaged_observations = (
            package
            / "files"
            / "capsule"
            / "prepared"
            / "observations.jsonl"
        )
        packaged_observations.write_text(
            packaged_observations.read_text(encoding="utf-8")
            + "\n",
            encoding="utf-8",
        )
        request(
            package,
            query_payload("metric.mttr"),
            expect_success=False,
        )

    print("Typed observation DSL-C query contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
