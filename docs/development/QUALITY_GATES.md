# Quality gates

Status: active for new and modified handwritten files.

## Goals

- keep changes reviewable;
- prevent line-ending drift between Windows and Linux;
- keep generated output replaceable;
- prevent orphan Markdown decisions;
- make Python quality failures deterministic in CI.

## Repository guard

The cross-platform guard checks the changed or staged file set:

```powershell
python .\tools\quality\repository_guard.py --staged
```

It rejects:

- handwritten files over 150 physical lines;
- handwritten C# `partial` declarations;
- broken local Markdown links reachable from `AGENTS.md`;
- changed Markdown files not reachable from `AGENTS.md`.

Generated output, migrations, build products, artifacts, and binary assets are excluded.
The limit applies to existing long files when they are substantially modified; extract a coherent
module before extending them.

## Python lint

Python 3.12 is the target. Ruff uses `select = ["ALL"]` with only formatter-conflict exceptions and
narrow per-path exceptions declared in `pyproject.toml`.

For staged Python files in PowerShell:

```powershell
$files = git diff --cached --name-only --diff-filter=ACMR -- '*.py'
if ($files) {
    ruff check $files
    ruff format --check $files
}
```

Formatting is explicit; CI never rewrites files.

## Generated modules

A generator change must be reviewed as three separate concerns when practical:

1. schema or template;
2. generated output;
3. handwritten adapter or behavior.

Generated projects expose public contracts but do not own domain decisions. Handwritten code does
not patch generated files after generation.

## Markdown navigation

`AGENTS.md` is the root of the documentation graph. New architecture, status, runbook, and service
Markdown must be linked into that graph in the same commit.

Links to removed historical paths should be written as prose, not as fake repository paths.

## CI

`.github/workflows/quality.yml` compares the pull request or push against its base commit, runs the
repository guard, then runs Ruff check and format verification on changed Python files only.
Existing untouched debt does not make unrelated work red.
