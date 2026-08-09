# ENG-201 — Codex→Python executable-program comparator

Status: **producer candidate, TRAIN/DEV-only; independent review required**.

This package freezes a general executable-Python comparator for WP-004 without treating Python/program synthesis as novel.

- **M21**: deterministic outcome-blind mapper chooses capability+arguments, frozen Python executes, Qwen sees only typed result/provenance.
- **M22**: Qwen chooses capability+arguments from the same frozen public API, the same Python executes, Qwen sees the same result schema. DEV-only by default.

The committed program is a synthetic producer-authored exemplar. It is not represented as an empirical Codex-generated artifact and supports no teacher-effect claim.

## Files

- `PYTHON_PROGRAM_CONTRACT.md`
- `PYTHON_TOOL_API.schema.json`
- `QWEN_VISIBLE_PYTHON_INTERFACE.schema.json`
- `PYTHON_SANDBOX_PROFILE.json`
- `PYTHON_RUNTIME_LOCK.json`
- `QWEN_VISIBLE_PYTHON_REQUEST.schema.json`
- `PYTHON_SECURITY_BOUNDARY.md`
- `PYTHON_MUTATION_PLAN.yaml`
- `prototype/program.py`
- `prototype/tool_api.json`
- `prototype/cases.train_dev.json`
- `prototype/runner.py`
- `prototype/verify.py`
- `ENG-201_FREEZE_MANIFEST.json`

## Local deterministic check

From this directory:

```text
python prototype/verify.py
```

The verifier checks the exact CPython/dependency/resource lock, the synthetic cases twice for byte-stable outputs, typed API and pre/post Qwen visibility, statically rejects forbidden program capabilities, and executes the named mutation suite.

No HOLDOUT or REPLICATION content is used or required.
