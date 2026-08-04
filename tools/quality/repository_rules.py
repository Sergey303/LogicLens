"""Reusable rules for the repository quality guard."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

MAX_LINES = 150
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
PARTIAL_DECLARATION = re.compile(r"\bpartial\s+(?:class|record|struct|interface)\b")
TEXT_SUFFIXES = {
    ".cs",
    ".csproj",
    ".css",
    ".html",
    ".json",
    ".jsonl",
    ".md",
    ".pl",
    ".props",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".xml",
    ".yaml",
    ".yml",
}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "artifacts",
    "bin",
    "coverage",
    "dist",
    "node_modules",
    "obj",
    "packages",
    "verification-results",
}
GENERATED_PARTS = {"generated", "migrations"}
GENERATED_SUFFIXES = (
    ".designer.cs",
    ".g.cs",
    ".generated.cs",
    ".generated.py",
    ".min.css",
    ".min.js",
)


def git(*args: str) -> list[str]:
    """Run Git and return non-empty output lines."""
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def changed_files(
    base: str | None,
    *,
    staged: bool,
    all_files: bool,
) -> list[Path]:
    """Return the selected tracked file set."""
    if all_files:
        names = git("ls-files")
    elif staged:
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    else:
        if base is None:
            base = git("rev-parse", "HEAD^")[0]
        names = git("diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD")
    return sorted({Path(name) for name in names})


def is_generated(path: Path) -> bool:
    """Return whether a path is recognized generated output."""
    lowered = tuple(part.lower() for part in path.parts)
    return any(part in GENERATED_PARTS for part in lowered) or path.name.lower().endswith(
        GENERATED_SUFFIXES,
    )


def is_owned_text(path: Path) -> bool:
    """Return whether the path is repository-owned UTF-8 text."""
    if not path.is_file() or any(part.lower() in EXCLUDED_PARTS for part in path.parts):
        return False
    allowed_names = {"AGENTS.md", ".editorconfig"}
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in allowed_names:
        return False
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return True


def markdown_targets(
    path: Path,
    root: Path,
    errors: list[str],
    *,
    report: bool,
) -> set[Path]:
    """Return valid local Markdown targets and record broken links."""
    targets: set[Path] = set()
    text = path.read_text(encoding="utf-8")
    for raw in MARKDOWN_LINK.findall(text):
        target = raw.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0].strip()
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            continue
        resolved = (path.parent / target).resolve()
        if root not in resolved.parents and resolved != root:
            if report:
                errors.append(f"Markdown link escapes repository: {path} -> {target}")
            continue
        if not resolved.exists():
            if report:
                errors.append(f"Broken Markdown link: {path} -> {target}")
            continue
        if resolved.suffix.lower() == ".md":
            targets.add(resolved)
    return targets


def reachable_markdown(root: Path, errors: list[str], checked: set[Path]) -> set[Path]:
    """Traverse the Markdown graph starting at root AGENTS.md."""
    start = root / "AGENTS.md"
    if not start.is_file():
        errors.append("AGENTS.md is required at repository root")
        return set()
    seen: set[Path] = set()
    pending = [start.resolve()]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(
            markdown_targets(current, root, errors, report=current in checked) - seen,
        )
    return seen
