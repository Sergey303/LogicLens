from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


WEAK_WARNING = "overrides weak import from cli_runtime"


def run_request(
    swipl: str,
    package: Path,
    request: dict[str, Any],
) -> tuple[int, dict[str, Any], str]:
    package = package.resolve()
    entry = (package / "entry.pl").resolve()

    if not entry.is_file():
        raise RuntimeError(f"entry.pl does not exist: {entry}")

    completed = subprocess.run(
        [swipl, "--quiet", "-s", str(entry), "--"],
        cwd=str(package),
        input=json.dumps(request, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
        check=False,
    )

    if WEAK_WARNING in completed.stderr:
        raise RuntimeError(
            "clean overlay emitted the forbidden weak-import warning: "
            + completed.stderr
        )

    lines = [
        line
        for line in completed.stdout.splitlines()
        if line.strip()
    ]

    if len(lines) != 1:
        raise RuntimeError(
            "runtime must return exactly one JSON line: "
            f"stdout={completed.stdout!r}; "
            f"stderr={completed.stderr!r}"
        )

    value = json.loads(lines[0])

    if not isinstance(value, dict):
        raise RuntimeError("runtime response is not a JSON object")

    return completed.returncode, value, completed.stderr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swipl", required=True)
    parser.add_argument("--active", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    baseline_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-104-baseline-health",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }

    preview_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-104-preview-health",
        "command": "health",
        "epoch": 0,
        "revision": 1,
        "options": {},
    }

    baseline_code, baseline, baseline_stderr = run_request(
        args.swipl,
        args.active,
        baseline_request,
    )

    preview_code, preview, preview_stderr = run_request(
        args.swipl,
        args.preview,
        preview_request,
    )

    if baseline_code != 0 or baseline.get("status") != "ok":
        raise RuntimeError(f"baseline health failed: {baseline}")

    if preview_code != 0 or preview.get("status") != "ok":
        raise RuntimeError(f"preview health failed: {preview}")

    if preview.get("epoch") != 0 or preview.get("revision") != 1:
        raise RuntimeError("preview did not report revision 0.1")

    baseline_result = dict(baseline.get("result") or {})
    preview_result = dict(preview.get("result") or {})

    baseline_commands = list(
        baseline_result.get("availableCommands") or []
    )

    preview_commands = list(
        preview_result.get("availableCommands") or []
    )

    preview_result["availableCommands"] = [
        command
        for command in preview_commands
        if command != "derived-query"
    ]

    if baseline_result != preview_result:
        raise RuntimeError(
            "delegated baseline health result changed"
        )

    if preview_commands.count("derived-query") != 1:
        raise RuntimeError(
            "preview did not expose exactly one derived-query"
        )

    derived_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-104-derived",
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
        args.preview,
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
        raise RuntimeError(f"derived query failed: {derived}")

    row = rows[0]

    if row.get("entityId") != "urn:logiclens:person:alex":
        raise RuntimeError(f"unexpected entity: {row}")

    evidence = list(row.get("evidenceFactIds") or [])

    if (
        len(evidence) != 3
        or len(set(evidence)) != 3
        or evidence != sorted(evidence)
    ):
        raise RuntimeError(
            f"unexpected evidence FactIds: {evidence!r}"
        )

    stale_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-104-stale",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }

    stale_code, stale, stale_stderr = run_request(
        args.swipl,
        args.preview,
        stale_request,
    )

    if (
        stale_code != 1
        or (stale.get("error") or {}).get("code")
        != "stale_state"
    ):
        raise RuntimeError(
            f"stale state was not rejected: {stale}"
        )

    unknown_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-104-unknown",
        "command": "derived-query",
        "epoch": 0,
        "revision": 1,
        "options": {
            "predicate": "urn:logiclens:derived:unknown"
        },
    }

    unknown_code, unknown, unknown_stderr = run_request(
        args.swipl,
        args.preview,
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

    stderr_values = {
        "baselineHealth": baseline_stderr,
        "previewHealth": preview_stderr,
        "derivedQuery": derived_stderr,
        "staleState": stale_stderr,
        "unknownPredicate": unknown_stderr,
    }

    for name, value in stderr_values.items():
        if WEAK_WARNING in value:
            raise RuntimeError(
                f"{name} contains the forbidden warning"
            )

    report = {
        "schemaVersion": "0.1",
        "stage": "warning-free-activation-overlay-preview",
        "baselineHealth": baseline,
        "previewHealth": preview,
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
            "weakImportWarningAbsent": True,
        },
        "stderr": stderr_values,
        "intent": {
            "staging": "not-performed",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
    }

    args.output.resolve().write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("Warning-free runtime preview passed")
    print("Derived evidence: " + ", ".join(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
