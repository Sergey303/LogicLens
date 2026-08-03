from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from capsule import canonical_json, domain_hash, json_object, schema_check, sha256
from .common import SourcePipelineError, load_fragments, load_workspace, normalize_quote, prepare_empty_directory
from .pdf_common import PDF_SEED_DOMAIN


def resolve_pdf_seed(
    *,
    proposal_root: Path,
    seed_path: Path,
    output: Path,
    schemas: dict[str, dict[str, Any]],
    pdf_schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    root, workspace = load_workspace(proposal_root, schemas, required_stage="fragmented")
    seed = json_object(seed_path, "PDF proposal seed")
    schema_check(seed, pdf_schemas["seed"], "PDF proposal seed")
    if seed["proposalId"] != workspace["proposalId"] or seed["sourceId"] != workspace["sourceId"]:
        raise SourcePipelineError("PDF proposal seed identity mismatch")
    fragments = load_fragments(root, workspace, schemas)
    by_page: dict[int, list[dict[str, Any]]] = {}
    for fragment in fragments:
        by_page.setdefault(fragment.get("pageNumber", 0), []).append(fragment)

    candidate_assertions: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for item in seed["assertions"]:
        grounding: list[str] = []
        evidence_quotes: list[dict[str, str]] = []
        for evidence in item["evidence"]:
            quote_normalized = normalize_quote(evidence["quote"])
            matches = [
                fragment
                for fragment in by_page.get(evidence["pageNumber"], [])
                if quote_normalized in normalize_quote(fragment["text"])
            ]
            if len(matches) != 1:
                raise SourcePipelineError(
                    f"seed evidence for {item['assertionId']} must match exactly one fragment; "
                    f"page={evidence['pageNumber']}, matches={len(matches)}"
                )
            fragment_id = matches[0]["fragmentId"]
            grounding.append(fragment_id)
            evidence_quotes.append({"fragmentId": fragment_id, "quote": evidence["quote"]})
        candidate_assertions.append(
            {
                "assertionId": item["assertionId"],
                "target": deepcopy(item["target"]),
                "stance": item["stance"],
                "grounding": sorted(set(grounding)),
                "dependencyGroup": item["dependencyGroup"],
                "scope": deepcopy(item.get("scope", {})),
                "generalisability": item["generalisability"],
                **({"note": item["note"]} if item.get("note") else {}),
            }
        )
        decisions.append(
            {
                "assertionId": item["assertionId"],
                "decision": "accept",
                "grounding": item.get("groundingClass", "direct"),
                "evidenceQuotes": evidence_quotes,
                "note": item["reviewNote"],
            }
        )

    candidate = {
        "schemaVersion": "0.1",
        "proposalId": seed["proposalId"],
        "sourceId": seed["sourceId"],
        "provider": {
            "kind": "deterministic",
            "name": "LogicLens PDF seed resolver",
            "runId": seed["seedId"],
        },
        "assertions": candidate_assertions,
        "abstentions": deepcopy(seed.get("abstentions", [])),
    }
    review = {
        "schemaVersion": "0.1",
        "reviewId": f"review-{seed['seedId']}",
        "proposalId": seed["proposalId"],
        "reviewer": {"kind": "agent", "id": "logiclens-pdf-seed-resolver"},
        "decisions": decisions,
    }
    schema_check(candidate, schemas["proposal"], "resolved PDF assertion proposal")
    schema_check(review, schemas["review"], "resolved PDF grounding review")
    destination = prepare_empty_directory(output)
    (destination / "assertion-candidate.json").write_bytes(canonical_json(candidate))
    (destination / "grounding-review.json").write_bytes(canonical_json(review))
    resolution = {
        "schemaVersion": "0.1",
        "seedId": seed["seedId"],
        "proposalId": seed["proposalId"],
        "sourceId": seed["sourceId"],
        "seedHash": domain_hash(PDF_SEED_DOMAIN, seed),
        "candidateHash": sha256(canonical_json(candidate)),
        "reviewHash": sha256(canonical_json(review)),
    }
    (destination / "resolution.json").write_bytes(canonical_json(resolution))
    return candidate, review
