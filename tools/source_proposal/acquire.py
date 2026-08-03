from __future__ import annotations

import ipaddress
import re
import socket
import urllib.parse
import urllib.request
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from capsule import canonical_json, declared_file, domain_hash, json_object, normalized_text, schema_check, sha256, text_value, validate_world
from .common import (
    ALLOWED_MEDIA_TYPES, MAX_EXTRACTION_TEXT, MAX_FRAGMENT_CHARS, MAX_SOURCE_BYTES,
    SAFE_ID, SNAPSHOT_DOMAIN, SourcePipelineError, load_fragments, load_semantics,
    load_workspace, media_type_for_path, prepare_empty_directory, read_limited,
    slug, write_workspace,
)

class MarkdownHTMLExtractor(HTMLParser):
    """Extract deterministic Markdown-like text from ordinary HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._heading_level: int | None = None
        self._buffer: list[str] = []
        self._blocks: list[str] = []
        self._block_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in {"script", "style", "noscript", "svg"}:
            self._skip += 1
            return
        if self._skip:
            return
        if lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush()
            self._heading_level = int(lower[1])
            self._block_tag = lower
        elif lower in {"p", "li", "pre", "blockquote", "dt", "dd"}:
            self._flush()
            self._block_tag = lower
        elif lower == "br":
            self._buffer.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"script", "style", "noscript", "svg"}:
            if self._skip:
                self._skip -= 1
            return
        if self._skip:
            return
        if lower == self._block_tag:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._buffer.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def text(self) -> str:
        self.close()
        return "\n\n".join(block for block in self._blocks if block).strip() + "\n"

    def _flush(self) -> None:
        if not self._buffer:
            self._block_tag = None
            self._heading_level = None
            return
        raw = "".join(self._buffer)
        cleaned = re.sub(r"[ \t\f\v]+", " ", raw)
        cleaned = re.sub(r" *\n *", "\n", cleaned).strip()
        if cleaned:
            if self._heading_level is not None:
                cleaned = "#" * self._heading_level + " " + cleaned
            elif self._block_tag == "li":
                cleaned = "- " + cleaned
            self._blocks.append(cleaned)
        self._buffer.clear()
        self._block_tag = None
        self._heading_level = None


def snapshot_source(
    *,
    world_root: Path,
    capsule_id: str,
    source_id: str,
    proposal_id: str,
    output: Path,
    repository_root: Path | None,
    allow_network: bool,
    max_bytes: int,
    schemas: dict[str, dict[str, Any]],
    contracts_root: Path,
) -> dict[str, Any]:
    if not SAFE_ID.fullmatch(proposal_id):
        raise SourcePipelineError("proposal ID is not a safe identifier")
    if max_bytes < 1 or max_bytes > 64 * 1024 * 1024:
        raise SourcePipelineError("max bytes must be between 1 and 67108864")
    world = validate_world(world_root, contracts_root)
    capsule = world["capsules"].get(capsule_id)
    if capsule is None:
        raise SourcePipelineError(f"unknown capsule: {capsule_id}")
    source = next((item for item in capsule["sources"]["sources"] if item["id"] == source_id), None)
    if source is None:
        raise SourcePipelineError(f"unknown source: {source_id}")
    root = prepare_empty_directory(output)
    text, acquisition = acquire_source(
        source=source,
        capsule_root=capsule["root"],
        repository_root=repository_root,
        allow_network=allow_network,
        max_bytes=max_bytes,
    )
    snapshot_dir = root / "snapshot"
    snapshot_dir.mkdir(parents=True)
    source_suffix = ".md" if acquisition["mediaType"] == "text/markdown" else ".txt"
    source_relative = f"snapshot/source{source_suffix}"
    source_bytes = normalized_text(text)
    (root / source_relative).write_bytes(source_bytes)
    source_manifest_hash = sha256(canonical_json(capsule["sources"]))
    snapshot: dict[str, Any] = {
        "schemaVersion": "0.1",
        "proposalId": proposal_id,
        "worldId": world["manifest"]["worldId"],
        "capsuleId": capsule_id,
        "sourceId": source_id,
        "sourceKind": source["kind"],
        "title": source["title"],
        "locator": source["locator"],
        "license": deepcopy(source["license"]),
        "snapshotPolicy": source["snapshotPolicy"],
        "sourceManifestHash": source_manifest_hash,
        "acquisition": acquisition,
        "artifact": {
            "path": source_relative,
            "encoding": "utf-8",
            "mediaType": acquisition["mediaType"],
            "bytes": len(source_bytes),
            "contentHash": sha256(source_bytes),
        },
    }
    snapshot["snapshotHash"] = domain_hash(SNAPSHOT_DOMAIN, snapshot)
    schema_check(snapshot, schemas["snapshot"], "source snapshot")
    snapshot_relative = "snapshot/snapshot.json"
    (root / snapshot_relative).write_bytes(canonical_json(snapshot))
    workspace: dict[str, Any] = {
        "schemaVersion": "0.1",
        "proposalId": proposal_id,
        "worldId": world["manifest"]["worldId"],
        "capsuleId": capsule_id,
        "sourceId": source_id,
        "stage": "snapshot",
        "artifacts": {
            "snapshot": {
                "metadataPath": snapshot_relative,
                "sourcePath": source_relative,
                "hash": snapshot["snapshotHash"],
            }
        },
    }
    return write_workspace(root, workspace, schemas)


def acquire_source(
    *,
    source: dict[str, Any],
    capsule_root: Path,
    repository_root: Path | None,
    allow_network: bool,
    max_bytes: int,
) -> tuple[str, dict[str, Any]]:
    policy = source["snapshotPolicy"]
    kind = source["kind"]
    if kind == "local-file":
        path = declared_file(capsule_root, source["locator"], "local source")
        content = read_limited(path, max_bytes)
        return decode_text(content, media_type_for_path(path)), {
            "mode": "local-file",
            "mediaType": media_type_for_path(path),
            "sourceBytes": len(content),
        }
    if kind == "repository-file":
        repository_path = source.get("repositoryPath")
        if not isinstance(repository_path, str):
            raise SourcePipelineError("repository-file requires repositoryPath")
        if repository_root is None:
            raise SourcePipelineError("repository-file requires --repository-root")
        path = declared_file(repository_root.resolve(), repository_path, "repository source")
        content = read_limited(path, max_bytes)
        return decode_text(content, media_type_for_path(path)), {
            "mode": "repository-file",
            "mediaType": media_type_for_path(path),
            "sourceBytes": len(content),
            "repositoryPath": repository_path,
        }
    if policy == "link-only":
        raise SourcePipelineError("link-only source cannot be snapshotted")
    if source["license"]["status"] == "restricted":
        raise SourcePipelineError("restricted source cannot be snapshotted")
    if not allow_network:
        raise SourcePipelineError("network snapshot requires --allow-network")
    return acquire_network_text(source["locator"], max_bytes)


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        validate_public_https_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire_network_text(url: str, max_bytes: int) -> tuple[str, dict[str, Any]]:
    validate_public_https_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "LogicLensSourcePipeline/0.1",
            "Accept": "text/html,text/plain,text/markdown,application/json,application/xml;q=0.8",
            "Accept-Encoding": "identity",
        },
    )
    try:
        opener = urllib.request.build_opener(SafeRedirectHandler())
        with opener.open(request, timeout=30) as response:
            final_url = response.geturl()
            validate_public_https_url(final_url)
            media_type = response.headers.get_content_type().lower()
            if media_type not in ALLOWED_MEDIA_TYPES:
                raise SourcePipelineError(f"unsupported network media type: {media_type}")
            content = response.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise SourcePipelineError("network source exceeds maximum size")
            charset = response.headers.get_content_charset() or "utf-8"
    except (OSError, urllib.error.URLError, UnicodeError) as exc:
        raise SourcePipelineError(f"cannot fetch source: {exc}") from exc
    text = decode_text(content, media_type, charset)
    return text, {
        "mode": "network",
        "mediaType": "text/markdown" if media_type in {"text/html", "application/xhtml+xml"} else media_type,
        "sourceMediaType": media_type,
        "sourceBytes": len(content),
        "finalUrl": final_url,
    }


def validate_public_https_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise SourcePipelineError("network source must be a credential-free HTTPS URL")
    if parsed.port not in {None, 443}:
        raise SourcePipelineError("network source must use HTTPS port 443")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourcePipelineError(f"cannot resolve source host: {exc}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise SourcePipelineError(f"source host resolves to non-public address: {ip}")


def decode_text(content: bytes, media_type: str, charset: str = "utf-8") -> str:
    try:
        text = content.decode(charset)
    except (LookupError, UnicodeDecodeError) as exc:
        raise SourcePipelineError(f"source is not valid {charset} text: {exc}") from exc
    if media_type in {"text/html", "application/xhtml+xml"}:
        parser = MarkdownHTMLExtractor()
        parser.feed(text)
        return parser.text()
    return text.replace("\r\n", "\n").replace("\r", "\n")


def fragment_workspace(root_path: Path, schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    root, workspace = load_workspace(root_path, schemas, required_stage="snapshot")
    snapshot = json_object(
        declared_file(root, workspace["artifacts"]["snapshot"]["metadataPath"], "snapshot metadata"),
        "snapshot metadata",
    )
    schema_check(snapshot, schemas["snapshot"], "source snapshot")
    source_path = declared_file(root, snapshot["artifact"]["path"], "snapshot source")
    if sha256(source_path.read_bytes()) != snapshot["artifact"]["contentHash"]:
        raise SourcePipelineError("snapshot source hash mismatch")
    text = text_value(source_path, "snapshot source")
    fragments = build_fragments(text, snapshot)
    fragment_dir = root / "fragments"
    fragment_dir.mkdir(exist_ok=False)
    relative = "fragments/fragments.jsonl"
    content = b"".join(canonical_json(fragment) for fragment in fragments)
    (root / relative).write_bytes(content)
    workspace["stage"] = "fragmented"
    workspace["artifacts"]["fragments"] = {
        "path": relative,
        "count": len(fragments),
        "hash": sha256(content),
    }
    return write_workspace(root, workspace, schemas)


def build_fragments(text: str, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    lines = text.splitlines()
    sections: list[tuple[list[str], int, int, str]] = []
    heading_path: list[str] = []
    start = 1
    buffer: list[str] = []

    def flush(end_line: int) -> None:
        nonlocal start, buffer
        content = "\n".join(buffer).strip()
        if content:
            sections.append((list(heading_path), start, end_line, content))
        buffer = []

    for number, line in enumerate(lines, 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            flush(number - 1)
            level = len(match.group(1))
            heading = match.group(2).strip()
            heading_path[:] = heading_path[: level - 1]
            heading_path.append(heading)
            start = number
            buffer = [line]
        else:
            if not buffer:
                start = number
            buffer.append(line)
    flush(len(lines))
    if not sections and text.strip():
        sections = [([], 1, max(1, len(lines)), text.strip())]

    result: list[dict[str, Any]] = []
    ordinal = 0
    for headings, line_start, line_end, content in sections:
        for chunk in split_fragment(content, MAX_FRAGMENT_CHARS):
            ordinal += 1
            label = headings[-1] if headings else "introduction"
            fragment_id = f"{snapshot['sourceId']}#f-{ordinal:04d}-{slug(label)}"
            fragment: dict[str, Any] = {
                "schemaVersion": "0.1",
                "fragmentId": fragment_id,
                "proposalId": snapshot["proposalId"],
                "sourceId": snapshot["sourceId"],
                "snapshotHash": snapshot["snapshotHash"],
                "ordinal": ordinal,
                "headingPath": headings,
                "lineStart": line_start,
                "lineEnd": line_end,
                "text": chunk,
                "textHash": sha256(normalized_text(chunk)),
            }
            result.append(fragment)
    return result


def split_fragment(text: str, maximum: int) -> list[str]:
    if len(text) <= maximum:
        return [text]
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else current + "\n\n" + paragraph
        if len(candidate) <= maximum:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= maximum:
            current = paragraph
            continue
        for offset in range(0, len(paragraph), maximum):
            chunks.append(paragraph[offset : offset + maximum])
        current = ""
    if current:
        chunks.append(current)
    return chunks


def prepare_extraction(
    *,
    world_root: Path,
    proposal_root: Path,
    prompt_path: Path,
    schemas: dict[str, dict[str, Any]],
    contracts_root: Path,
) -> dict[str, Any]:
    root, workspace = load_workspace(proposal_root, schemas, required_stage="fragmented")
    world = validate_world(world_root, contracts_root)
    if world["manifest"]["worldId"] != workspace["worldId"]:
        raise SourcePipelineError("workspace world does not match supplied world")
    fragments = load_fragments(root, workspace, schemas)
    total = sum(len(fragment["text"]) for fragment in fragments)
    if total > MAX_EXTRACTION_TEXT:
        raise SourcePipelineError("fragment text exceeds extraction request limit")
    semantics = load_semantics(world)
    prompt = text_value(prompt_path, "source assertion proposer prompt")
    extraction_dir = root / "extraction"
    extraction_dir.mkdir(exist_ok=False)
    prompt_relative = "extraction/prompt.md"
    request_relative = "extraction/extraction-request.json"
    (root / prompt_relative).write_bytes(normalized_text(prompt))
    request = {
        "schemaVersion": "0.1",
        "proposalId": workspace["proposalId"],
        "worldId": workspace["worldId"],
        "capsuleId": workspace["capsuleId"],
        "sourceId": workspace["sourceId"],
        "instructions": {
            "outputContract": "assertion-proposal-v0",
            "openWorld": True,
            "absenceIsOpposition": False,
            "allowInferenceAsAssertion": False,
            "requireFragmentGrounding": True,
            "requireDependencyGroup": True,
        },
        "semanticModel": {
            "predicates": semantics["predicates"],
            "roles": semantics["roles"],
            "concepts": semantics["concepts"],
        },
        "fragments": fragments,
    }
    request_bytes = canonical_json(request)
    (root / request_relative).write_bytes(request_bytes)
    workspace["stage"] = "prepared"
    workspace["artifacts"]["extractionRequest"] = {
        "path": request_relative,
        "hash": sha256(request_bytes),
        "promptPath": prompt_relative,
        "promptHash": sha256(normalized_text(prompt)),
    }
    return write_workspace(root, workspace, schemas)
