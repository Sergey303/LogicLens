from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from capsule import (
    CapsuleError, canonical_json, declared_file, domain_hash, json_lines,
    json_object, normalized_text, schema_check, sha256, text_value, validate_world,
)

UTF8 = "utf-8"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_EXTRACTION_TEXT = 160_000
MAX_FRAGMENT_CHARS = 6_000
WORKSPACE_DOMAIN = b"LogicLensSourceProposalWorkspace\0"
SNAPSHOT_DOMAIN = b"LogicLensSourceSnapshot\0"
REVIEW_DOMAIN = b"LogicLensSourceGroundingReview\0"
PACKAGE_DOMAIN = b"LogicLensSourceProposalPackage\0"
GROUP_DOMAIN = b"LogicLensSourceProposalGroup\0"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_DEPENDENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
ALLOWED_MEDIA_TYPES = {
    "text/plain", "text/markdown", "text/html", "text/xml",
    "application/json", "application/xml", "application/xhtml+xml",
}
SCHEMAS = {
    "snapshot": "source-snapshot-v0.schema.json",
    "fragment": "source-fragment-v0.schema.json",
    "workspace": "source-proposal-workspace-v0.schema.json",
    "proposal": "assertion-proposal-v0.schema.json",
    "review": "source-grounding-review-v0.schema.json",
    "package": "source-proposal-package-v0.schema.json",
}

class SourcePipelineError(RuntimeError):
    pass

def load_schemas(root: Path) -> dict[str, dict[str, Any]]:
    return {
        name: json_object(root / filename, f"{name} schema")
        for name, filename in SCHEMAS.items()
    }


def load_workspace(
    root_path: Path,
    schemas: dict[str, dict[str, Any]],
    *,
    required_stage: str,
) -> tuple[Path, dict[str, Any]]:
    root = root_path.resolve()
    workspace = json_object(root / "proposal.json", "source proposal workspace")
    schema_check(workspace, schemas["workspace"], "source proposal workspace")
    validate_workspace_hash(workspace)
    if workspace["stage"] != required_stage:
        raise SourcePipelineError(
            f"source proposal stage must be {required_stage}, got {workspace['stage']}"
        )
    return root, workspace


def write_workspace(
    root: Path,
    workspace: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    payload = deepcopy(workspace)
    payload.pop("workspaceHash", None)
    payload["workspaceHash"] = domain_hash(WORKSPACE_DOMAIN, payload)
    schema_check(payload, schemas["workspace"], "source proposal workspace")
    (root / "proposal.json").write_bytes(canonical_json(payload))
    return payload


def validate_workspace_hash(workspace: dict[str, Any]) -> None:
    payload = deepcopy(workspace)
    supplied = payload.pop("workspaceHash", None)
    if supplied != domain_hash(WORKSPACE_DOMAIN, payload):
        raise SourcePipelineError("source proposal workspace hash mismatch")


def validate_review_hash(review: dict[str, Any]) -> None:
    payload = deepcopy(review)
    supplied = payload.pop("reviewHash", None)
    if supplied != domain_hash(REVIEW_DOMAIN, payload):
        raise SourcePipelineError("source-grounding review hash mismatch")


def load_fragments(
    root: Path,
    workspace: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact = workspace["artifacts"]["fragments"]
    path = declared_file(root, artifact["path"], "fragments")
    if sha256(path.read_bytes()) != artifact["hash"]:
        raise SourcePipelineError("fragment artifact hash mismatch")
    fragments = json_lines(path, "fragments")
    seen: set[str] = set()
    snapshot_hash = workspace["artifacts"]["snapshot"]["hash"]
    for index, fragment in enumerate(fragments, 1):
        schema_check(fragment, schemas["fragment"], f"fragment:{index}")
        fragment_id = fragment["fragmentId"]
        if fragment_id in seen:
            raise SourcePipelineError(f"duplicate fragment ID: {fragment_id}")
        seen.add(fragment_id)
        if (
            fragment["proposalId"] != workspace["proposalId"]
            or fragment["sourceId"] != workspace["sourceId"]
            or fragment["snapshotHash"] != snapshot_hash
        ):
            raise SourcePipelineError(f"fragment identity mismatch: {fragment_id}")
        if fragment["lineEnd"] < fragment["lineStart"]:
            raise SourcePipelineError(f"fragment line range is invalid: {fragment_id}")
        if fragment["textHash"] != sha256(normalized_text(fragment["text"])):
            raise SourcePipelineError(f"fragment text hash mismatch: {fragment_id}")
    return fragments


def load_assertion_proposal(
    root: Path,
    workspace: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    artifact = workspace["artifacts"]["assertionProposal"]
    path = declared_file(root, artifact["path"], "assertion proposal")
    if sha256(path.read_bytes()) != artifact["hash"]:
        raise SourcePipelineError("assertion proposal artifact hash mismatch")
    proposal = json_object(path, "assertion proposal")
    schema_check(proposal, schemas["proposal"], "assertion proposal")
    return proposal


def load_semantics(world: dict[str, Any]) -> dict[str, Any]:
    root = world["root"]
    semantic_paths = world["manifest"]["semantic"]
    predicates_doc = json_object(root / semantic_paths["predicates"], "semantic predicates")
    roles_doc = json_object(root / semantic_paths["roles"], "semantic roles")
    vocabulary_doc = json_object(root / semantic_paths["vocabulary"], "semantic vocabulary")
    predicates = predicates_doc.get("predicates")
    roles = roles_doc.get("roles")
    concepts = vocabulary_doc.get("concepts")
    if not isinstance(predicates, list) or not isinstance(roles, list) or not isinstance(concepts, list):
        raise SourcePipelineError("semantic registry shape is invalid")
    typed: dict[str, set[str]] = {"role": {item["id"] for item in roles}}
    for concept in concepts:
        typed.setdefault(concept["kind"], set()).add(concept["id"])
    return {
        "predicates": predicates,
        "roles": roles,
        "concepts": concepts,
        "typedIds": typed,
    }


def copy_workspace_artifact(
    workspace_root: Path,
    relative: str,
    files_root: Path,
    category: str,
    records: list[dict[str, str]],
    groups: dict[str, list[tuple[str, str]]],
) -> None:
    source = declared_file(workspace_root, relative, "workspace artifact")
    destination = files_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_bytes()
    destination.write_bytes(content)
    file_hash = sha256(content)
    records.append({"path": relative, "sha256": file_hash})
    groups[category].append((relative, file_hash))


def group_hash(records: Iterable[tuple[str, str]]) -> str:
    digest = hashlib.sha256(GROUP_DOMAIN)
    for path, file_hash in sorted(records):
        digest.update(path.encode(UTF8) + b"\0" + file_hash.encode("ascii") + b"\0")
    return "sha256:" + digest.hexdigest()


def prepare_empty_directory(path: Path) -> Path:
    root = path.resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise SourcePipelineError(f"output must be absent or empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    return root


def read_limited(path: Path, maximum: int) -> bytes:
    size = path.stat().st_size
    if size > maximum:
        raise SourcePipelineError(f"source exceeds maximum size: {size} > {maximum}")
    return path.read_bytes()


def media_type_for_path(path: Path) -> str:
    return {
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".html": "text/html",
        ".htm": "text/html",
        ".json": "application/json",
        ".xml": "application/xml",
    }.get(path.suffix.lower(), "text/plain")


def normalize_quote(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slug(value: str) -> str:
    lowered = value.casefold()
    cleaned = re.sub(r"[^a-z0-9а-яё]+", "-", lowered, flags=re.I).strip("-")
    return cleaned[:64] or "section"
