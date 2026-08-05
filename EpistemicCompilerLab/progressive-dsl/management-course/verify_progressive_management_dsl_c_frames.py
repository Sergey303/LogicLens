#!/usr/bin/env python3
"""Verify frozen DSL-C expectations against real packaged observation frames."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

UTF8 = "utf-8"


class FrameVerificationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logiclens-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--dsl-c-package", required=True, type=Path)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise FrameVerificationError(f"{path}:{number}: object expected")
        rows.append(value)
    if not rows:
        raise FrameVerificationError(f"empty cases file: {path}")
    return rows


def run(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        text=True,
        encoding=UTF8,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise FrameVerificationError(
            f"command failed: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout[-4000:]}\n"
            f"stderr:\n{completed.stderr[-4000:]}"
        )


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding=UTF8,
        newline="\n",
    )


def request_from_case(case: dict[str, Any]) -> dict[str, Any]:
    queries = case.get("goldQueries")
    if not isinstance(queries, list) or len(queries) != 1:
        raise FrameVerificationError(
            f"{case.get('caseId')}: exactly one gold query is required"
        )
    query = queries[0]
    request: dict[str, Any] = {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-C",
        "operation": query["operation"],
        "target": query["target"],
    }
    if query["operation"] == "numeric-comparison":
        request["comparison"] = query["comparison"]
    return request


def exact_list(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise FrameVerificationError("string array expected")
    return sorted(value)


def main() -> int:
    args = parse_args()
    logiclens = args.logiclens_root.resolve()
    cases_path = args.cases.resolve()
    package = args.dsl_c_package.resolve()
    output = args.output.resolve()
    query_tool = logiclens / "tools" / "capsule_query_dsl_c.py"
    contracts = logiclens / "contracts"
    cases = load_jsonl(cases_path)
    work = output.parent / f"{output.stem}-frames"
    if work.exists():
        raise FrameVerificationError(f"preflight work directory exists: {work}")
    work.mkdir(parents=True)

    records: list[dict[str, Any]] = []
    for case in cases:
        case_id = case["caseId"]
        request = request_from_case(case)
        request_path = work / f"{case_id}.request.json"
        result_path = work / f"{case_id}.result.json"
        write_json(request_path, request)
        run(
            [
                sys.executable,
                str(query_tool),
                "--contracts-root",
                str(contracts),
                "--package",
                str(package),
                "--request",
                str(request_path),
                "--swipl",
                args.swipl,
                "--pretty",
                "--output",
                str(result_path),
            ]
        )
        frame = json.loads(result_path.read_text(encoding=UTF8))
        expected = case["expectedByLevel"]["DSL-C"]

        if frame.get("status") != expected.get("status"):
            raise FrameVerificationError(
                f"{case_id}: status expected={expected.get('status')} "
                f"actual={frame.get('status')}"
            )
        if frame.get("action") != expected.get("action"):
            raise FrameVerificationError(
                f"{case_id}: action expected={expected.get('action')} "
                f"actual={frame.get('action')}"
            )
        if exact_list(frame.get("warnings")) != exact_list(expected.get("warnings", [])):
            raise FrameVerificationError(
                f"{case_id}: warnings mismatch "
                f"expected={expected.get('warnings', [])} "
                f"actual={frame.get('warnings')}"
            )

        expected_observation = expected.get("observation")
        actual_observation = frame.get("observation")
        if expected_observation is None:
            if actual_observation is not None:
                raise FrameVerificationError(
                    f"{case_id}: observation must be null"
                )
        else:
            if not isinstance(actual_observation, dict):
                raise FrameVerificationError(
                    f"{case_id}: observation object expected"
                )
            if actual_observation.get("target") != expected_observation.get("target"):
                raise FrameVerificationError(
                    f"{case_id}: observation target mismatch"
                )

        runtime = frame.get("runtime")
        if not isinstance(runtime, dict):
            raise FrameVerificationError(f"{case_id}: runtime object missing")
        if runtime.get("verifiedAgainstPackagedObservations") is not True:
            raise FrameVerificationError(
                f"{case_id}: packaged observation verification missing"
            )
        if runtime.get("verifiedAgainstPrologKernel") is not True:
            raise FrameVerificationError(
                f"{case_id}: Prolog kernel verification missing"
            )

        records.append(
            {
                "caseId": case_id,
                "status": frame["status"],
                "action": frame["action"],
                "observationId": (
                    None
                    if actual_observation is None
                    else actual_observation["observationId"]
                ),
                "modelKind": (
                    "missing"
                    if actual_observation is None
                    else actual_observation["model"]["kind"]
                ),
                "warnings": frame["warnings"],
                "queryHash": frame["queryHash"],
                "packageHash": frame["package"]["packageHash"],
            }
        )

    summary = {
        "schemaVersion": "0.1",
        "kind": "progressive-management-dsl-c-frame-preflight",
        "caseCount": len(cases),
        "verified": True,
        "records": records,
    }
    write_json(output, summary)
    print("Progressive management DSL-C real-frame preflight passed")
    print(f"Cases: {len(cases)}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FrameVerificationError, OSError, subprocess.SubprocessError) as exc:
        print(f"DSL-C frame preflight failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
