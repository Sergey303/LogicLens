"""Generate the pinned Document Evidence .NET client from its OpenAPI contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

from read_plan_openapi_contract import validate_read_plan_security

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "services" / "document-evidence"
OPENAPI = SERVICE / "openapi" / "document-evidence-v1.json"
TEMPLATES = SERVICE / "codegen" / "client-templates"
CLIENT = SERVICE / "src" / "DocumentEvidence.Client"
OUTPUTS = (
    "DocumentEvidenceClientException.Generated.cs",
    "DocumentEvidenceClientTransport.Generated.cs",
    "DocumentEvidenceClient.Generated.cs",
    "NonDisposingReadStream.Generated.cs",
    "ResponseOwnedReadStream.Generated.cs",
)
EXPECTED_OPERATIONS = {
    "/api/v1/workspaces/{workspaceId}/documents/{documentId}/revisions": (
        "put",
        "uploadRevision",
    ),
    "/api/v1/workspaces/{workspaceId}/documents/{documentId}": (
        "get",
        "getDocument",
    ),
    "/api/v1/workspaces/{workspaceId}/revisions/{revisionId}/fragments": (
        "get",
        "listFragments",
    ),
    "/api/v1/workspaces/{workspaceId}/revisions/{revisionId}/read-plans": (
        "post",
        "issueReadPlan",
    ),
    "/api/v1/read-plans/content": ("get", "openReadPlan"),
}
EXPECTED_SCHEMAS = {
    "DocumentFragment",
    "DocumentMetadata",
    "Error",
    "FragmentAnchor",
    "ReadPlan",
    "UploadRevision",
}


def sha256(content: bytes) -> str:
    """Return a lowercase SHA-256 digest."""
    return hashlib.sha256(content).hexdigest()


def mapping(value: object, label: str) -> dict[str, object]:
    """Require one JSON object and return it with a precise type."""
    if not isinstance(value, dict):
        message = f"OpenAPI field must be an object: {label}"
        raise ValueError(message)
    return cast("dict[str, object]", value)


def validate_openapi(content: bytes) -> None:
    """Fail closed when the supported OpenAPI surface drifts."""
    raw: object = json.loads(content)
    spec = mapping(raw, "root")
    validate_read_plan_security(spec)
    info = mapping(spec.get("info"), "info")
    if info.get("version") != "1.0.0":
        message = "Document Evidence OpenAPI version must remain 1.0.0."
        raise ValueError(message)
    paths = mapping(spec.get("paths"), "paths")
    for path, (method, operation_id) in EXPECTED_OPERATIONS.items():
        operation = mapping(mapping(paths.get(path), path).get(method), f"{method} {path}")
        if operation.get("operationId") != operation_id:
            message = f"Unexpected operationId for {method} {path}."
            raise ValueError(message)
    components = mapping(spec.get("components"), "components")
    schemas = mapping(components.get("schemas"), "components.schemas")
    missing = EXPECTED_SCHEMAS - schemas.keys()
    if missing:
        message = f"OpenAPI schemas required by the client are missing: {sorted(missing)}"
        raise ValueError(message)


def render() -> dict[Path, bytes]:
    """Render every generated output from its reviewed template."""
    rendered: dict[Path, bytes] = {}
    for name in OUTPUTS:
        template = TEMPLATES / f"{name}.txt"
        rendered[CLIENT / name] = template.read_bytes()
    return rendered


def receipt(spec_content: bytes, rendered: dict[Path, bytes]) -> dict[str, object]:
    """Build a deterministic generation receipt for logs and evidence."""
    outputs = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(content),
        }
        for path, content in sorted(rendered.items())
    ]
    return {
        "formatVersion": 1,
        "generator": Path(__file__).relative_to(ROOT).as_posix(),
        "openApi": OPENAPI.relative_to(ROOT).as_posix(),
        "openApiSha256": sha256(spec_content),
        "outputs": outputs,
    }


def apply(rendered: dict[Path, bytes], *, check: bool) -> None:
    """Write outputs or verify that committed bytes already match."""
    mismatches = [
        path
        for path, content in rendered.items()
        if not path.is_file() or path.read_bytes() != content
    ]
    if check and mismatches:
        names = ", ".join(path.relative_to(ROOT).as_posix() for path in mismatches)
        message = f"Generated Document Evidence client is stale: {names}"
        raise RuntimeError(message)
    if not check:
        for path, content in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def main() -> int:
    """Validate OpenAPI, generate or check the client, and print its receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    spec_content = OPENAPI.read_bytes()
    validate_openapi(spec_content)
    rendered = render()
    apply(rendered, check=args.check)
    print(json.dumps(receipt(spec_content, rendered), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
