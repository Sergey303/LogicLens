from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from capsule import canonical_json, declared_file, domain_hash, json_object, schema_check, sha256, validate_world
from .common import (
    REVIEW_DOMAIN, SAFE_DEPENDENCY, SourcePipelineError, load_assertion_proposal,
    load_fragments, load_semantics, load_workspace, normalize_quote, write_workspace,
)

def import_assertion_proposal(
    *,
    world_root: Path,
    proposal_root: Path,
    candidate_path: Path,
    schemas: dict[str, dict[str, Any]],
    contracts_root: Path,
) -> dict[str, Any]:
    root, workspace = load_workspace(proposal_root, schemas, required_stage="prepared")
    candidate = json_object(candidate_path, "assertion proposal candidate")
    schema_check(candidate, schemas["proposal"], "assertion proposal candidate")
    if candidate["proposalId"] != workspace["proposalId"] or candidate["sourceId"] != workspace["sourceId"]:
        raise SourcePipelineError("assertion proposal identity mismatch")
    world = validate_world(world_root, contracts_root)
    semantics = load_semantics(world)
    fragments = {item["fragmentId"]: item for item in load_fragments(root, workspace, schemas)}
    validate_assertion_candidates(candidate["assertions"], semantics, fragments)
    assertion_ids = [item["assertionId"] for item in candidate["assertions"]]
    if len(assertion_ids) != len(set(assertion_ids)):
        raise SourcePipelineError("duplicate assertion proposal ID")
    relative = "assertions/assertions-proposal.json"
    (root / "assertions").mkdir(exist_ok=False)
    content = canonical_json(candidate)
    (root / relative).write_bytes(content)
    workspace["stage"] = "proposed"
    workspace["artifacts"]["assertionProposal"] = {
        "path": relative,
        "count": len(candidate["assertions"]),
        "hash": sha256(content),
    }
    return write_workspace(root, workspace, schemas)


def validate_assertion_candidates(
    assertions: list[dict[str, Any]],
    semantics: dict[str, Any],
    fragments: dict[str, dict[str, Any]],
) -> None:
    predicates = {item["id"]: item for item in semantics["predicates"]}
    typed_ids = semantics["typedIds"]
    for assertion in assertions:
        target = assertion["target"]
        predicate = predicates.get(target["predicate"])
        if predicate is None:
            raise SourcePipelineError(
                f"{assertion['assertionId']} uses unknown predicate {target['predicate']}"
            )
        arguments = target["arguments"]
        if len(arguments) != len(predicate["arguments"]):
            raise SourcePipelineError(f"{assertion['assertionId']} argument count mismatch")
        for value, declaration in zip(arguments, predicate["arguments"], strict=True):
            allowed = typed_ids.get(declaration["type"], set())
            if value not in allowed:
                raise SourcePipelineError(
                    f"{assertion['assertionId']} unknown {declaration['type']} ID: {value}"
                )
        if not SAFE_DEPENDENCY.fullmatch(assertion["dependencyGroup"]):
            raise SourcePipelineError(f"{assertion['assertionId']} has unsafe dependency group")
        for fragment_id in assertion["grounding"]:
            if fragment_id not in fragments:
                raise SourcePipelineError(
                    f"{assertion['assertionId']} references unknown fragment {fragment_id}"
                )


def import_grounding_review(
    *,
    proposal_root: Path,
    review_path: Path,
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    root, workspace = load_workspace(proposal_root, schemas, required_stage="proposed")
    proposal = load_assertion_proposal(root, workspace, schemas)
    review = json_object(review_path, "source-grounding review")
    schema_check(review, schemas["review"], "source-grounding review")
    if review["proposalId"] != workspace["proposalId"]:
        raise SourcePipelineError("review proposal identity mismatch")
    by_id = {item["assertionId"]: item for item in proposal["assertions"]}
    decisions = review["decisions"]
    decision_ids = [item["assertionId"] for item in decisions]
    if len(decision_ids) != len(set(decision_ids)) or set(decision_ids) != set(by_id):
        raise SourcePipelineError("review must contain exactly one decision per assertion")
    fragments = {item["fragmentId"]: item for item in load_fragments(root, workspace, schemas)}
    for decision in decisions:
        assertion = by_id[decision["assertionId"]]
        if decision["decision"] == "accept":
            if decision["grounding"] not in {"direct", "paraphrase"}:
                raise SourcePipelineError(
                    f"accepted assertion {decision['assertionId']} must be direct or paraphrase"
                )
            if not decision["evidenceQuotes"]:
                raise SourcePipelineError(
                    f"accepted assertion {decision['assertionId']} requires an evidence quote"
                )
            allowed_fragments = set(assertion["grounding"])
            for evidence in decision["evidenceQuotes"]:
                fragment_id = evidence["fragmentId"]
                if fragment_id not in allowed_fragments:
                    raise SourcePipelineError(
                        f"review quote for {decision['assertionId']} is outside candidate grounding"
                    )
                fragment = fragments.get(fragment_id)
                if fragment is None or normalize_quote(evidence["quote"]) not in normalize_quote(fragment["text"]):
                    raise SourcePipelineError(
                        f"review quote for {decision['assertionId']} is not present in {fragment_id}"
                    )
        elif decision["decision"] == "revise" and not decision.get("replacement"):
            raise SourcePipelineError(
                f"revise decision for {decision['assertionId']} requires replacement"
            )
    review_class = "human-reviewed" if review["reviewer"]["kind"] == "human" else "provisional"
    payload = deepcopy(review)
    payload["reviewClass"] = review_class
    payload["reviewHash"] = domain_hash(REVIEW_DOMAIN, payload)
    schema_check(payload, schemas["review"], "canonical source-grounding review")
    relative = "review/source-grounding-review.json"
    (root / "review").mkdir(exist_ok=False)
    content = canonical_json(payload)
    (root / relative).write_bytes(content)
    workspace["stage"] = "reviewed"
    workspace["artifacts"]["review"] = {
        "path": relative,
        "class": review_class,
        "hash": sha256(content),
        "reviewHash": payload["reviewHash"],
    }
    return write_workspace(root, workspace, schemas)
