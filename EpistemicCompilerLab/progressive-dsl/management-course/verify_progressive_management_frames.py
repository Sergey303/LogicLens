#!/usr/bin/env python3
"""Verify real DSL-A/B frames against frozen progressive case expectations."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

UTF8 = "utf-8"


class VerificationError(RuntimeError):
    pass


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logiclens-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--dsl-a-package", required=True, type=Path)
    parser.add_argument("--dsl-b-package", required=True, type=Path)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding=UTF8))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object expected: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise VerificationError(f"JSON object expected: {path}:{number}")
        rows.append(value)
    if not rows:
        raise VerificationError(f"empty case set: {path}")
    return rows


def run(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        text=True,
        encoding=UTF8,
        errors="strict",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise VerificationError(
            "command failed: "
            + " ".join(command)
            + f"\nstdout:\n{completed.stdout[-4000:]}"
            + f"\nstderr:\n{completed.stderr[-4000:]}"
        )


def evidence_ids(frame: dict[str, Any]) -> list[str]:
    evidence = frame.get("evidence")
    if not isinstance(evidence, dict):
        return []
    result: list[str] = []
    for stance in ("support", "oppose"):
        rows = evidence.get(stance)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, str):
                result.append(row)
            elif isinstance(row, dict) and isinstance(row.get("assertionId"), str):
                result.append(row["assertionId"])
    return sorted(set(result))


def proof_rule_ids(frame: dict[str, Any]) -> list[str]:
    proof = frame.get("proof")
    if not isinstance(proof, dict):
        return []
    nodes = proof.get("nodes")
    if not isinstance(nodes, list):
        return []
    return sorted(
        {
            node["ruleId"]
            for node in nodes
            if isinstance(node, dict)
            and node.get("kind") == "rule"
            and isinstance(node.get("ruleId"), str)
        }
    )


def query_frame(
    *,
    logiclens: Path,
    package: Path,
    case: dict[str, Any],
    level: str,
    swipl: str,
    root: Path,
) -> dict[str, Any]:
    target = case["goldQueries"][0]["target"]
    contracts = logiclens / "contracts"
    if level == "DSL-A":
        request = {
            "schemaVersion": "0.1",
            "operation": "strict-claim",
            "target": target,
        }
        tool = logiclens / "tools" / "capsule_query.py"
    else:
        request = {
            "schemaVersion": "0.1",
            "dslLevel": "DSL-B",
            "operation": "derived-strict-claim",
            "target": target,
        }
        tool = logiclens / "tools" / "capsule_query_dsl_b.py"
    request_path = root / level.lower() / f"{case['caseId']}.request.json"
    result_path = root / level.lower() / f"{case['caseId']}.result.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding=UTF8)
    run(
        [
            sys.executable,
            str(tool),
            "--contracts-root",
            str(contracts),
            "--package",
            str(package),
            "--request",
            str(request_path),
            "--swipl",
            swipl,
            "--pretty",
            "--output",
            str(result_path),
        ]
    )
    return load_json(result_path)


def compare_frame(
    *,
    case: dict[str, Any],
    level: str,
    frame: dict[str, Any],
) -> dict[str, Any]:
    expected = case["expectedByLevel"][level]
    actual = {
        "status": frame.get("status"),
        "action": frame.get("action"),
        "evidenceIds": evidence_ids(frame),
        "warnings": sorted(frame.get("warnings", [])),
        "ruleIds": proof_rule_ids(frame),
    }
    expected_normalized = {
        "status": expected.get("status"),
        "action": expected.get("action"),
        "evidenceIds": sorted(expected.get("evidenceIds", [])),
        "warnings": sorted(expected.get("warnings", [])),
        "ruleIds": sorted(expected.get("ruleIds", [])),
    }
    if level == "DSL-A":
        actual["ruleIds"] = []
        expected_normalized["ruleIds"] = []
    if actual != expected_normalized:
        raise VerificationError(
            f"frame mismatch for {case['caseId']} {level}: "
            f"expected={json.dumps(expected_normalized, ensure_ascii=False, sort_keys=True)} "
            f"actual={json.dumps(actual, ensure_ascii=False, sort_keys=True)}"
        )
    return {
        "caseId": case["caseId"],
        "level": level,
        **actual,
    }


def main() -> int:
    args = arguments()
    logiclens = args.logiclens_root.resolve()
    cases = load_jsonl(args.cases.resolve())
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="progressive-frame-verify-") as name:
        root = Path(name)
        for case in cases:
            for level, package in (
                ("DSL-A", args.dsl_a_package.resolve()),
                ("DSL-B", args.dsl_b_package.resolve()),
            ):
                frame = query_frame(
                    logiclens=logiclens,
                    package=package,
                    case=case,
                    level=level,
                    swipl=args.swipl,
                    root=root,
                )
                record = compare_frame(case=case, level=level, frame=frame)
                records.append(record)
                print(
                    f"{level} {case['caseId']}: "
                    f"{record['status']} evidence={len(record['evidenceIds'])} "
                    f"rules={len(record['ruleIds'])}"
                )

    result = {
        "schemaVersion": "0.1",
        "kind": "progressive-management-frame-preflight",
        "caseCount": len(cases),
        "frameCount": len(records),
        "records": records,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding=UTF8,
        )
    print("Progressive management frame preflight passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, subprocess.SubprocessError) as exc:
        print(f"Frame preflight failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
