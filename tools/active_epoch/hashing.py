from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .contract import UTF8


class BuildError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, separators=(",", ": "))
        + "\n"
    ).encode(UTF8)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read generated manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"generated manifest is not an object: {path}")
    return value


def sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def aggregate_hash(
    domain: bytes,
    version: int,
    files: Iterable[tuple[PurePosixPath, bytes]],
) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(bytes((version,)))
    for path, content in sorted(files, key=lambda item: str(item[0])):
        append_field(digest, str(path).encode(UTF8))
        append_field(digest, content)
    return "sha256:" + digest.hexdigest()


def append_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big", signed=False))
    digest.update(value)


def required_string(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise BuildError(f"generated manifest field {key!r} is missing or invalid")
    return result
