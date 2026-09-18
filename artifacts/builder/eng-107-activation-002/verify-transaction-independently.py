from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"not a JSON object: {path}")
    return value


def canonical_json(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            separators=(",", ": "),
        )
        + "\n"
    ).encode("utf-8")


def record_hash(
    domain: bytes,
    value: dict[str, Any],
    field: str,
) -> str:
    payload = dict(value)
    payload.pop(field, None)

    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(bytes((1,)))
    digest.update(canonical_json(payload))

    return "sha256:" + digest.hexdigest()


def require_hash(
    domain: bytes,
    value: dict[str, Any],
    field: str,
    context: str,
) -> str:
    expected = value.get(field)
    computed = record_hash(domain, value, field)

    if expected != computed:
        raise RuntimeError(
            f"{context} hash differs: "
            f"expected={expected}; computed={computed}"
        )

    return computed


def run_request(
    swipl: str,
    package: Path,
    request: dict[str, Any],
) -> tuple[int, dict[str, Any], str]:
    package = package.resolve()
    entry = (package / "entry.pl").resolve()

    if not entry.is_file():
        raise RuntimeError(f"entry.pl is missing: {entry}")

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

    lines = [
        line
        for line in completed.stdout.splitlines()
        if line.strip()
    ]

    if len(lines) != 1:
        raise RuntimeError(
            "runtime must return one JSON line: "
            f"stdout={completed.stdout!r}; "
            f"stderr={completed.stderr!r}"
        )

    response = json.loads(lines[0])

    if not isinstance(response, dict):
        raise RuntimeError("runtime response is not an object")

    return completed.returncode, response, completed.stderr


def selected_package(
    deployment: Path,
    pointer: dict[str, Any],
) -> Path:
    relative = pointer.get("packagePath")

    if (
        not isinstance(relative, str)
        or not relative.startswith("packages/")
        or ".." in relative.replace("\\", "/").split("/")
    ):
        raise RuntimeError("unsafe packagePath")

    package = (deployment / relative).resolve()
    packages = (deployment / "packages").resolve()

    if package.parent != packages or not package.is_dir():
        raise RuntimeError(
            f"selected package is invalid: {package}"
        )

    return package


def verify_real_runtime(
    swipl: str,
    deployment: Path,
    pointer: dict[str, Any],
) -> dict[str, Any]:
    package = selected_package(deployment, pointer)

    health_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-107-independent-health",
        "command": "health",
        "epoch": 0,
        "revision": 1,
        "options": {},
    }

    code, health, health_stderr = run_request(
        swipl,
        package,
        health_request,
    )

    if (
        code != 0
        or health.get("status") != "ok"
        or health.get("epoch") != 0
        or health.get("revision") != 1
    ):
        raise RuntimeError(
            f"selected 0.1 health failed: {health}"
        )

    commands = list(
        (health.get("result") or {}).get(
            "availableCommands"
        )
        or []
    )

    if commands.count("derived-query") != 1:
        raise RuntimeError(
            "selected 0.1 does not expose exactly one derived-query"
        )

    derived_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-107-independent-derived",
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

    code, derived, derived_stderr = run_request(
        swipl,
        package,
        derived_request,
    )

    rows = list(
        (derived.get("result") or {}).get("rows") or []
    )

    if (
        code != 0
        or derived.get("status") != "ok"
        or len(rows) != 1
        or rows[0].get("entityId")
        != "urn:logiclens:person:alex"
    ):
        raise RuntimeError(
            f"selected 0.1 derived-query failed: {derived}"
        )

    evidence = list(rows[0].get("evidenceFactIds") or [])

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
        "requestId": "eng-107-independent-stale",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }

    code, stale, stale_stderr = run_request(
        swipl,
        package,
        stale_request,
    )

    if (
        code != 1
        or (stale.get("error") or {}).get("code")
        != "stale_state"
    ):
        raise RuntimeError(
            f"selected 0.1 accepted stale state: {stale}"
        )

    unknown_request = {
        "protocolVersion": "0.1",
        "requestId": "eng-107-independent-unknown",
        "command": "derived-query",
        "epoch": 0,
        "revision": 1,
        "options": {
            "predicate": "urn:logiclens:derived:unknown"
        },
    }

    code, unknown, unknown_stderr = run_request(
        swipl,
        package,
        unknown_request,
    )

    if (
        code != 1
        or (unknown.get("error") or {}).get("code")
        != "unknown_predicate"
    ):
        raise RuntimeError(
            "selected 0.1 accepted unknown predicate: "
            f"{unknown}"
        )

    forbidden_warning = "overrides weak import from cli_runtime"

    for value in (
        health_stderr,
        derived_stderr,
        stale_stderr,
        unknown_stderr,
    ):
        if forbidden_warning in value:
            raise RuntimeError(
                "forbidden weak-import warning returned"
            )

    return {
        "packagePath": str(package),
        "health": health,
        "derivedQuery": derived,
        "staleState": stale,
        "unknownPredicate": unknown,
        "evidenceFactIds": evidence,
    }


def verify_rollback_runtime(
    swipl: str,
    deployment: Path,
    pointer: dict[str, Any],
) -> dict[str, Any]:
    package = selected_package(deployment, pointer)

    request = {
        "protocolVersion": "0.1",
        "requestId": "eng-107-independent-rollback-health",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }

    code, response, stderr = run_request(
        swipl,
        package,
        request,
    )

    if (
        code != 0
        or response.get("status") != "ok"
        or response.get("epoch") != 0
        or response.get("revision") != 0
    ):
        raise RuntimeError(
            f"rollback runtime health failed: {response}"
        )

    return {
        "packagePath": str(package),
        "health": response,
        "stderr": stderr,
    }


def verify_deployment_records(
    deployment: Path,
    transaction_id: str,
    external_attestation: Path,
) -> dict[str, Any]:
    pointer = read_json(deployment / "current.json")

    journal_path = (
        deployment
        / "transactions"
        / f"{transaction_id}.journal.json"
    )

    attestation_path = (
        deployment
        / "transactions"
        / f"{transaction_id}.attestation.json"
    )

    journal = read_json(journal_path)
    attestation = read_json(attestation_path)
    copied_attestation = read_json(external_attestation)

    if attestation != copied_attestation:
        raise RuntimeError(
            "copied attestation differs from deployment attestation"
        )

    return {
        "pointer": pointer,
        "journal": journal,
        "attestation": attestation,
        "pointerHash": require_hash(
            b"LogicLensActivePointer\0",
            pointer,
            "pointerHash",
            "pointer",
        ),
        "journalHash": require_hash(
            b"LogicLensActivationJournal\0",
            journal,
            "journalHash",
            "journal",
        ),
        "transactionHash": require_hash(
            b"LogicLensActivationTransaction\0",
            attestation,
            "transactionHash",
            "attestation",
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swipl", required=True)
    parser.add_argument(
        "--deployment",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--transaction-id",
        required=True,
    )
    parser.add_argument(
        "--attestation",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--fault-deployment",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--fault-transaction-id",
        required=True,
    )
    parser.add_argument(
        "--fault-attestation",
        required=True,
        type=Path,
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    real = verify_deployment_records(
        args.deployment.resolve(),
        args.transaction_id,
        args.attestation.resolve(),
    )

    fault = verify_deployment_records(
        args.fault_deployment.resolve(),
        args.fault_transaction_id,
        args.fault_attestation.resolve(),
    )

    if real["attestation"].get("outcome") != "committed":
        raise RuntimeError("real transaction is not committed")

    if real["journal"].get("state") != "committed":
        raise RuntimeError("real journal is not committed")

    if (
        real["pointer"].get("epoch") != 0
        or real["pointer"].get("revision") != 1
        or real["pointer"].get("generation") != 1
    ):
        raise RuntimeError("real pointer is not generation-1 revision 0.1")

    if fault["attestation"].get("outcome") != "rolled-back":
        raise RuntimeError("fault transaction is not rolled-back")

    if fault["journal"].get("state") != "rolled-back":
        raise RuntimeError("fault journal is not rolled-back")

    if (
        fault["pointer"].get("epoch") != 0
        or fault["pointer"].get("revision") != 0
        or fault["pointer"].get("generation") != 0
    ):
        raise RuntimeError("fault pointer was not restored to 0.0")

    runtime = verify_real_runtime(
        args.swipl,
        args.deployment.resolve(),
        real["pointer"],
    )

    rollback_runtime = verify_rollback_runtime(
        args.swipl,
        args.fault_deployment.resolve(),
        fault["pointer"],
    )

    report = {
        "schemaVersion": "0.1",
        "stage": "activation-transaction-independent-verification",
        "committed": {
            "pointerHash": real["pointerHash"],
            "journalHash": real["journalHash"],
            "transactionHash": real["transactionHash"],
            "runtime": runtime,
        },
        "faultInjection": {
            "pointerHash": fault["pointerHash"],
            "journalHash": fault["journalHash"],
            "transactionHash": fault["transactionHash"],
            "rollbackRuntime": rollback_runtime,
        },
        "checks": {
            "committedPointerVerified": True,
            "committedJournalVerified": True,
            "committedAttestationVerified": True,
            "selectedRuntimeHealthPassed": True,
            "selectedDerivedQueryPassed": True,
            "selectedStaleStateRejected": True,
            "selectedUnknownPredicateRejected": True,
            "faultPointerRestored": True,
            "faultJournalRolledBack": True,
            "faultAttestationVerified": True,
            "rollbackRuntimeHealthPassed": True,
        },
    }

    args.output.resolve().write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        "Independent committed transaction hash: " +
        real["transactionHash"]
    )
    print(
        "Independent rollback transaction hash: " +
        fault["transactionHash"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
