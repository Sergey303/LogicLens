#!/usr/bin/env python3
"""Check changed handwritten files and the Markdown navigation tree."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

MAX_LINES = 150
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
PARTIAL_DECLARATION = re.compile(r"\bpartial\s+(?:class|record|struct|interface)\b")
TEXT_SUFFIXES = {
    ".cs", ".csproj", ".css", ".html", ".json", ".jsonl", ".md", ".pl",
    ".props", ".ps1", ".py", ".sh", ".toml", ".ts", ".tsx", ".xml",
    ".yaml", ".yml",
}
EXCLUDED_PARTS = {
    ".git", ".venv", "artifacts", "bin", "coverage", "dist", "node_modules",
    "obj", "packages", "verification-results",
}
GENERATED_PARTS = {"generated", "migrations"}
GENERATED_SUFFIXES = (
    ".designer.cs", ".g.cs", ".generated.cs", ".generated.py", ".min.css", ".min.js",
)


def git(*args: str) -> list[str]:
    """Run Git and return non-empty output lines."""
    result = subprocess.run(
        ["git", *args], check=True, text=True, capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def changed_files(base: str | None, staged: bool, all_files: bool) -> list[Path]:
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
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"AGENTS.md", ".editorconfig"}:
        return False
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return True


def markdown_targets(path: Path, root: Path, errors: list[str]) -> set[Path]:
    """Return valid local Markdown targets and record broken links."""
    targets: set[Path] = set()
    text = path.read_text(encoding="utf-8")
    for raw in MARKDOWN_LINK.findall(text):
        target = raw.split("#", 1)[0].split("?", 1)[0].strip()
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            continue
        resolved = (path.parent / target).resolve()
        if root not in resolved.parents and resolved != root:
            errors.append(f"Markdown link escapes repository: {path} -> {target}")
            continue
        if not resolved.exists():
            errors.append(f"Broken Markdown link: {path} -> {target}")
            continue
        if resolved.suffix.lower() == ".md":
            targets.add(resolved)
    return targets


def reachable_markdown(root: Path, errors: list[str]) -> set[Path]:
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
        pending.extend(markdown_targets(current, root, errors) - seen)
    return seen


def main() -> int:
    """Run repository invariants for the requested file set."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--max-lines", type=int, default=MAX_LINES)
    args = parser.parse_args()

    root = Path(git("rev-parse", "--show-toplevel")[0]).resolve()
    files = changed_files(args.base, args.staged, args.all)
    errors: list[str] = []

    for relative in files:
        path = root / relative
        if not is_owned_text(path) or is_generated(relative):
            continue
        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        if line_count > args.max_lines:
            errors.append(f"{relative}: {line_count} lines; maximum is {args.max_lines}")
        if relative.suffix.lower() == ".cs" and PARTIAL_DECLARATION.search(text):
            errors.append(f"{relative}: handwritten partial declarations are forbidden")

    reachable = reachable_markdown(root, errors)
    for relative in files:
        if relative.suffix.lower() != ".md" or is_generated(relative):
            continue
        absolute = (root / relative).resolve()
        if absolute not in reachable:
            errors.append(f"{relative}: Markdown file is not reachable from AGENTS.md")

    if errors:
        print("Repository guard failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print(f"Repository guard passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
