"""Check changed handwritten files and the Markdown navigation tree."""
from __future__ import annotations

import argparse
from pathlib import Path

from repository_rules import (
    MAX_LINES,
    PARTIAL_DECLARATION,
    changed_files,
    git,
    is_generated,
    is_owned_text,
    reachable_markdown,
)


def parse_args() -> argparse.Namespace:
    """Parse repository guard command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--max-lines", type=int, default=MAX_LINES)
    return parser.parse_args()


def file_errors(root: Path, files: list[Path], max_lines: int) -> list[str]:
    """Return size and decomposition errors for selected files."""
    errors: list[str] = []
    for relative in files:
        path = root / relative
        if not is_owned_text(path) or is_generated(relative):
            continue
        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        if line_count > max_lines:
            errors.append(f"{relative}: {line_count} lines; maximum is {max_lines}")
        if relative.suffix.lower() == ".cs" and PARTIAL_DECLARATION.search(text):
            errors.append(f"{relative}: handwritten partial declarations are forbidden")
    return errors


def markdown_errors(root: Path, files: list[Path]) -> list[str]:
    """Return documentation graph errors for selected files."""
    errors: list[str] = []
    checked = {(root / path).resolve() for path in files if path.suffix.lower() == ".md"}
    reachable = reachable_markdown(root, errors, checked)
    for relative in files:
        if relative.suffix.lower() != ".md" or is_generated(relative):
            continue
        if (root / relative).resolve() not in reachable:
            errors.append(f"{relative}: Markdown file is not reachable from AGENTS.md")
    return errors


def main() -> int:
    """Run repository invariants for the requested file set."""
    args = parse_args()
    root = Path(git("rev-parse", "--show-toplevel")[0]).resolve()
    files = changed_files(args.base, staged=args.staged, all_files=args.all)
    errors = file_errors(root, files, args.max_lines)
    errors.extend(markdown_errors(root, files))

    if errors:
        print("Repository guard failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print(f"Repository guard passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
