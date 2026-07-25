from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import PurePosixPath


UTF8 = "utf-8"
SCHEMA_VERSION = "0.1"
MAX_FILES = 32
MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024

ALLOWED_UI_COMPONENTS = frozenset(
    {
        "Property",
        "TextBlock",
        "RawProlog",
        "Diagnostic",
    }
)

_PATH_POLICIES: tuple[tuple[str, str], ...] = (
    ("rules/candidate_*.pl", "rule"),
    ("tests/candidate_*_tests.pl", "test"),
    ("ui/*.json", "ui"),
)


class CandidateError(RuntimeError):
    """Raised when a candidate violates the reviewed contract."""


def validate_relative_path(raw_path: str) -> PurePosixPath:
    if not isinstance(raw_path, str) or not raw_path:
        raise CandidateError("candidate file path must be a non-empty string")

    path = PurePosixPath(raw_path)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
        or "\\" in raw_path
    ):
        raise CandidateError(f"unsafe candidate file path: {raw_path!r}")

    return path


def expected_kind(path: PurePosixPath) -> str:
    text = str(path)
    for pattern, kind in _PATH_POLICIES:
        if fnmatchcase(text, pattern):
            return kind
    raise CandidateError(f"candidate file path is not allowlisted: {text}")


def validate_kind(path: PurePosixPath, declared_kind: str) -> None:
    actual_kind = expected_kind(path)
    if declared_kind != actual_kind:
        raise CandidateError(
            f"candidate file kind mismatch for {path}: "
            f"expected {actual_kind!r}, actual {declared_kind!r}"
        )
