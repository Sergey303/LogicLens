from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def run_request(
    swipl: str,
    package: Path,
    request: dict[str, Any],
) -> tuple[int, dict[str, Any], str]:
    package = package.resolve()
    entry = (package / "entry.pl").resolve()

    if not package.is_dir():
        raise RuntimeError(
            f"runtime package does not exist: {package}"
        )

    if not entry.is_file():
        raise RuntimeError(
            f"runtime entry does not exist: {entry}"
        )

    completed = subprocess.run(
        [
            swipl,
            "--quiet",
            "-s",
            str(entry),
            "--",
        ],
        cwd=str(package),
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
        check=False,
    )

    lines = [
        line
        for line in completed.stdout.splitlines()
        if line.strip()
    ]

    if len(lines) != 1:
        raise RuntimeError(
            "runtime must return exactly one JSON line: "
            f"entry={entry!s}; "
            f"cwd={package!s}; "
            f"stdout={completed.stdout!r}; "
            f"stderr={completed.stderr!r}"
        )

    response = json.loads(lines[0])

    if not isinstance(response, dict):
        raise RuntimeError(
            "runtime response is not a JSON object"
        )

    return completed.returncode, response, completed.stderr


def normalized_health_result(
    response: dict[str, Any],
    *,
    remove_derived: bool,
) -> dict[str, Any]:
    result = dict(response.get("result") or {})
    commands = list(result.get("availableCommands") or [])

    if remove_derived:
        commands = [
            command
            for command in commands
            if command != "derived-query"
        ]

    result["availableCommands"] = commands
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swipl", required=True)
    parser.add_argument("--active", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    active = args.active.resolve()
    preview = args.preview.resolve()
    output = args.output.resolve()

    baseline_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-98-overlay-002-baseline-health",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }

    preview_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-98-overlay-002-preview-health",
        "command": "health",
        "epoch": 0,
        "revision": 1,
        "options": {},
    }

    baseline_code, baseline, baseline_stderr = run_request(
        args.swipl,
        active,
        baseline_request,
    )

    preview_code, preview_response, preview_stderr = run_request(
        args.swipl,
        preview,
        preview_request,
    )

    if baseline_code != 0 or baseline.get("status") != "ok":
        raise RuntimeError(
            f"baseline health failed: {baseline}"
        )

    if (
        preview_code != 0
        or preview_response.get("status") != "ok"
    ):
        raise RuntimeError(
            f"preview health failed: {preview_response}"
        )

    if (
        preview_response.get("epoch") != 0
        or preview_response.get("revision") != 1
    ):
        raise RuntimeError(
            "preview health did not report epoch 0 revision 1"
        )

    baseline_result = normalized_health_result(
        baseline,
        remove_derived=False,
    )

    preview_result = normalized_health_result(
        preview_response,
        remove_derived=True,
    )

    if baseline_result != preview_result:
        raise RuntimeError(
            "delegated baseline health result changed: "
            f"baseline={baseline_result!r}; "
            f"preview={preview_result!r}"
        )

    preview_commands = list(
        (preview_response.get("result") or {}).get(
            "availableCommands"
        ) or []
    )

    if preview_commands.count("derived-query") != 1:
        raise RuntimeError(
            "preview health did not expose exactly one derived-query"
        )

    derived_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-98-overlay-002-derived",
        "command": "derived-query",
        "epoch": 0,
        "revision": 1,
        "options": {
            "predicate": (
                "urn:logiclens:derived:"
                "researcher-at-iis"
            )
        },
    }

    derived_code, derived, derived_stderr = run_request(
        args.swipl,
        preview,
        derived_request,
    )

    rows = list(
        (derived.get("result") or {}).get("rows") or []
    )

    if (
        derived_code != 0
        or derived.get("status") != "ok"
        or len(rows) != 1
    ):
        raise RuntimeError(
            f"derived-query failed: {derived}"
        )

    row = rows[0]

    if row.get("entityId") != "urn:logiclens:person:alex":
        raise RuntimeError(
            f"unexpected derived entity: {row}"
        )

    evidence = list(row.get("evidenceFactIds") or [])

    if (
        len(evidence) != 3
        or len(set(evidence)) != 3
        or evidence != sorted(evidence)
        or not all(
            isinstance(value, str) and value
            for value in evidence
        )
    ):
        raise RuntimeError(
            f"unexpected derived evidence: {evidence!r}"
        )

    stale_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-98-overlay-002-stale",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }

    stale_code, stale, stale_stderr = run_request(
        args.swipl,
        preview,
        stale_request,
    )

    if (
        stale_code != 1
        or (stale.get("error") or {}).get("code")
        != "stale_state"
    ):
        raise RuntimeError(
            f"stale revision was not rejected: {stale}"
        )

    unknown_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-98-overlay-002-unknown",
        "command": "derived-query",
        "epoch": 0,
        "revision": 1,
        "options": {
            "predicate": "urn:logiclens:derived:unknown"
        },
    }

    unknown_code, unknown, unknown_stderr = run_request(
        args.swipl,
        preview,
        unknown_request,
    )

    if (
        unknown_code != 1
        or (unknown.get("error") or {}).get("code")
        != "unknown_predicate"
    ):
        raise RuntimeError(
            f"unknown predicate was not rejected: {unknown}"
        )

    report = {
        "schemaVersion": "0.1",
        "stage": "activation-overlay-runtime-preview",
        "baselineHealth": baseline,
        "previewHealth": preview_response,
        "derivedQuery": derived,
        "staleState": stale,
        "unknownPredicate": unknown,
        "checks": {
            "baselineHealthPassed": True,
            "previewReportsRevisionOne": True,
            "baselineHealthResultPreserved": True,
            "derivedQueryPassed": True,
            "staleStateRejected": True,
            "unknownPredicateRejected": True,
        },
        "paths": {
            "active": str(active),
            "preview": str(preview),
            "previewEntry": str(
                (preview / "entry.pl").resolve()
            ),
        },
        "stderr": {
            "baselineHealth": baseline_stderr,
            "previewHealth": preview_stderr,
            "derivedQuery": derived_stderr,
            "staleState": stale_stderr,
            "unknownPredicate": unknown_stderr,
        },
        "intent": {
            "staging": "not-performed",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("Runtime preview passed")
    print(
        "Derived evidence: " +
        ", ".join(evidence)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
