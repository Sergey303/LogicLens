from __future__ import annotations

import shutil
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

from capsule import atom, canonical_json, declared_file, domain_hash, json_object, normalized_text, prolog_value, schema_check, sha256
from .common import (
    PACKAGE_DOMAIN, SourcePipelineError, copy_workspace_artifact, group_hash,
    load_assertion_proposal, load_workspace, validate_review_hash,
)

def execute_gate(
    *,
    proposal_root: Path,
    output: Path,
    swipl: str,
    timeout_seconds: int,
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    root, workspace = load_workspace(proposal_root, schemas, required_stage="reviewed")
    proposal = load_assertion_proposal(root, workspace, schemas)
    review = json_object(
        declared_file(root, workspace["artifacts"]["review"]["path"], "review"),
        "source-grounding review",
    )
    validate_review_hash(review)
    decisions = {item["assertionId"]: item for item in review["decisions"]}
    if any(item["decision"] == "revise" for item in decisions.values()):
        raise SourcePipelineError("source proposal has unresolved revise decisions")
    accepted = [
        assertion
        for assertion in proposal["assertions"]
        if decisions[assertion["assertionId"]]["decision"] == "accept"
    ]
    if not accepted:
        raise SourcePipelineError("source proposal has no accepted assertions")
    output_resolved = output.resolve()
    if output_resolved.exists() and (not output_resolved.is_dir() or any(output_resolved.iterdir())):
        raise SourcePipelineError(f"gate output must be absent or empty: {output_resolved}")
    output_resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=output_resolved.name + ".tmp-", dir=output_resolved.parent))
    try:
        files_root = temporary / "files"
        records: list[dict[str, str]] = []
        groups: dict[str, list[tuple[str, str]]] = {
            name: []
            for name in ("snapshot", "fragments", "proposal", "review", "generated", "extraction")
        }
        copy_workspace_artifact(root, workspace["artifacts"]["snapshot"]["metadataPath"], files_root, "snapshot", records, groups)
        copy_workspace_artifact(root, workspace["artifacts"]["snapshot"]["sourcePath"], files_root, "snapshot", records, groups)
        copy_workspace_artifact(root, workspace["artifacts"]["fragments"]["path"], files_root, "fragments", records, groups)
        copy_workspace_artifact(root, workspace["artifacts"]["extractionRequest"]["path"], files_root, "extraction", records, groups)
        copy_workspace_artifact(root, workspace["artifacts"]["extractionRequest"]["promptPath"], files_root, "extraction", records, groups)
        copy_workspace_artifact(root, workspace["artifacts"]["assertionProposal"]["path"], files_root, "proposal", records, groups)
        copy_workspace_artifact(root, workspace["artifacts"]["review"]["path"], files_root, "review", records, groups)
        prepared = [prepared_assertion(item, workspace["sourceId"]) for item in accepted]
        generated_dir = files_root / "generated"
        generated_dir.mkdir(parents=True)
        generated_files = {
            "generated/approved-assertions.jsonl": b"".join(canonical_json(item) for item in prepared),
            "generated/source_proposal.pl": normalized_text(generate_prolog(prepared)),
            "generated/source_proposal_tests.pl": normalized_text(generate_prolog_tests(prepared, workspace["proposalId"])),
        }
        for relative, content in generated_files.items():
            destination = files_root / relative
            destination.write_bytes(content)
            file_hash = sha256(content)
            records.append({"path": relative, "sha256": file_hash})
            groups["generated"].append((relative, file_hash))
        test_count = count_expected_tests(prepared) + 1
        run_swipl_gate(generated_dir, swipl, timeout_seconds)
        gate_report = {
            "schemaVersion": "0.1",
            "status": "passed",
            "engine": "SWI-Prolog",
            "testCount": test_count,
            "acceptedAssertions": len(prepared),
            "reviewClass": review["reviewClass"],
        }
        gate_relative = "generated/gate-report.json"
        gate_content = canonical_json(gate_report)
        (files_root / gate_relative).write_bytes(gate_content)
        gate_hash = sha256(gate_content)
        records.append({"path": gate_relative, "sha256": gate_hash})
        groups["generated"].append((gate_relative, gate_hash))
        records.sort(key=lambda item: item["path"])
        package: dict[str, Any] = {
            "schemaVersion": "0.1",
            "proposalId": workspace["proposalId"],
            "worldId": workspace["worldId"],
            "capsuleId": workspace["capsuleId"],
            "sourceId": workspace["sourceId"],
            "reviewClass": review["reviewClass"],
            "activation": "not-performed",
            "workspaceHash": workspace["workspaceHash"],
            "reviewHash": review["reviewHash"],
            "files": records,
            "groups": {name: group_hash(items) for name, items in sorted(groups.items())},
            "gate": gate_report,
        }
        package["packageHash"] = domain_hash(PACKAGE_DOMAIN, package)
        schema_check(package, schemas["package"], "source proposal package")
        (temporary / "source-proposal-package.json").write_bytes(canonical_json(package))
        lock = {
            "schemaVersion": "0.1",
            "proposalId": workspace["proposalId"],
            "workspaceHash": workspace["workspaceHash"],
            "reviewHash": review["reviewHash"],
            "packageHash": package["packageHash"],
            "groups": package["groups"],
        }
        (temporary / "source-proposal.lock.json").write_bytes(canonical_json(lock))
        if output_resolved.exists():
            output_resolved.rmdir()
        temporary.replace(output_resolved)
        return package
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_package(
    *,
    package_root: Path,
    swipl: str | None,
    timeout_seconds: int,
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    root = package_root.resolve()
    package = json_object(root / "source-proposal-package.json", "source proposal package")
    schema_check(package, schemas["package"], "source proposal package")
    supplied_hash = package["packageHash"]
    payload = dict(package)
    payload.pop("packageHash", None)
    if supplied_hash != domain_hash(PACKAGE_DOMAIN, payload):
        raise SourcePipelineError("source proposal package hash mismatch")
    lock = json_object(root / "source-proposal.lock.json", "source proposal lock")
    if lock.get("packageHash") != supplied_hash or lock.get("workspaceHash") != package["workspaceHash"]:
        raise SourcePipelineError("source proposal lock mismatch")
    expected: set[str] = set()
    files_root = root / "files"
    for record in package["files"]:
        relative = record["path"]
        if relative in expected:
            raise SourcePipelineError(f"duplicate package path: {relative}")
        expected.add(relative)
        path = declared_file(files_root, relative, "source proposal package file")
        if sha256(path.read_bytes()) != record["sha256"]:
            raise SourcePipelineError(f"source proposal package file hash mismatch: {relative}")
    actual = {path.relative_to(files_root).as_posix() for path in files_root.rglob("*") if path.is_file()}
    if actual != expected:
        raise SourcePipelineError(
            f"source proposal package file set mismatch; extra={sorted(actual-expected)}, "
            f"missing={sorted(expected-actual)}"
        )
    review = json_object(files_root / "review/source-grounding-review.json", "packaged review")
    validate_review_hash(review)
    if review["reviewHash"] != package["reviewHash"]:
        raise SourcePipelineError("packaged review hash mismatch")
    if swipl:
        run_swipl_gate(files_root / "generated", swipl, timeout_seconds)
    return package


def run_swipl_gate(generated_dir: Path, executable: str, timeout_seconds: int) -> None:
    if timeout_seconds < 1 or timeout_seconds > 300:
        raise SourcePipelineError("SWI-Prolog timeout must be 1..300 seconds")
    resolved = shutil.which(executable) if not any(separator in executable for separator in ("/", "\\")) else executable
    if not resolved:
        raise SourcePipelineError(f"SWI-Prolog executable not found: {executable}")
    try:
        result = subprocess.run(
            [resolved, "-q", "-s", "source_proposal_tests.pl", "-g", "run_tests,halt", "-t", "halt(1)"],
            cwd=generated_dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourcePipelineError(f"SWI-Prolog execution gate failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise SourcePipelineError(f"SWI-Prolog execution gate failed: {detail}")


def prepared_assertion(assertion: dict[str, Any], source_id: str) -> dict[str, Any]:
    return {
        "assertionId": assertion["assertionId"],
        "target": deepcopy(assertion["target"]),
        "stance": assertion["stance"],
        "provenance": assertion["grounding"],
        "dependencyGroup": assertion["dependencyGroup"],
        "scope": deepcopy(assertion.get("scope", {})),
        "generalisability": assertion["generalisability"],
        **({"note": assertion["note"]} if assertion.get("note") else {}),
    }


def generate_prolog(rows: list[dict[str, Any]]) -> str:
    lines = [
        ":- module(source_proposal, [source_assertion/6, claim_status/2, claim_evidence/3]).",
        "",
        "% Generated only from source-grounding-reviewed assertions.",
        "% Absence remains unknown and is never compiled as opposition.",
        "",
    ]
    for row in sorted(rows, key=lambda item: item["assertionId"]):
        target = row["target"]
        proposition = atom(target["predicate"]) + "(" + ", ".join(
            prolog_value(value) for value in target["arguments"]
        ) + ")"
        provenance = "[" + ", ".join(atom(value) for value in row["provenance"]) + "]"
        lines.append(
            "source_assertion("
            + ", ".join(
                (
                    atom(row["assertionId"]),
                    proposition,
                    atom(row["stance"]),
                    atom(row["dependencyGroup"]),
                    provenance,
                    atom(row["generalisability"]),
                )
            )
            + ")."
        )
    lines.extend(
        [
            "",
            "positive_evidence(Proposition, Id) :- source_assertion(Id, Proposition, support, _, _, _).",
            "negative_evidence(Proposition, Id) :- source_assertion(Id, Proposition, oppose, _, _, _).",
            "",
            "claim_status(Proposition, conflicting) :- positive_evidence(Proposition, _), negative_evidence(Proposition, _), !.",
            "claim_status(Proposition, supported) :- positive_evidence(Proposition, _), \\+ negative_evidence(Proposition, _), !.",
            "claim_status(Proposition, refuted) :- negative_evidence(Proposition, _), \\+ positive_evidence(Proposition, _), !.",
            "claim_status(Proposition, unknown) :- \\+ positive_evidence(Proposition, _), \\+ negative_evidence(Proposition, _).",
            "",
            "claim_evidence(Proposition, supported, Evidence) :- findall(Id, positive_evidence(Proposition, Id), Evidence).",
            "claim_evidence(Proposition, refuted, Evidence) :- findall(Id, negative_evidence(Proposition, Id), Evidence).",
            "claim_evidence(Proposition, conflicting, Evidence) :- findall(Id, source_assertion(Id, Proposition, _, _, _, _), Evidence).",
            "claim_evidence(_, unknown, []).",
        ]
    )
    return "\n".join(lines) + "\n"


def generate_prolog_tests(rows: list[dict[str, Any]], proposal_id: str) -> str:
    grouped: dict[tuple[str, tuple[Any, ...]], set[str]] = {}
    for row in rows:
        target = row["target"]
        key = (target["predicate"], tuple(target["arguments"]))
        grouped.setdefault(key, set()).add(row["stance"])
    lines = [
        ":- begin_tests(source_proposal_gate).",
        ":- use_module('./source_proposal.pl').",
        "",
    ]
    for index, ((predicate, arguments), stances) in enumerate(sorted(grouped.items()), 1):
        status = "conflicting" if stances == {"support", "oppose"} else (
            "supported" if "support" in stances else "refuted"
        )
        proposition = atom(predicate) + "(" + ", ".join(prolog_value(value) for value in arguments) + ")"
        lines.append(
            f"test(reviewed_status_{index:03d}) :- source_proposal:claim_status({proposition}, {status})."
        )
    lines.append(
        "test(open_world_unknown) :- source_proposal:claim_status("
        + atom("unknown_probe")
        + "("
        + atom(proposal_id)
        + "), unknown)."
    )
    lines.extend(["", ":- end_tests(source_proposal_gate).", ""])
    return "\n".join(lines)


def count_expected_tests(rows: list[dict[str, Any]]) -> int:
    return len({(row["target"]["predicate"], tuple(row["target"]["arguments"])) for row in rows})


