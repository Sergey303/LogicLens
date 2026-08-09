# ENG-201 — Python security and visibility boundary

This is a research prototype boundary, not a production sandbox claim.

## Program-side deny-by-default policy

The candidate program module is rejected if its AST contains imports, attribute-based dynamic access, filesystem/network/process primitives, reflection, dynamic evaluation, exception-message exfiltration or nondeterministic APIs. The prototype module intentionally uses no imports.

Forbidden examples include `open`, `eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`, `globals`, `locals`, `vars`, `input`, `breakpoint`, `os`, `sys`, `socket`, `subprocess`, `pathlib`, `requests`, `urllib`, `random`, `secrets`, `time` and `datetime`.

The frozen W0 sandbox profile also records one call, 100 ms wall/CPU budgets, 64 MiB memory, 4096 result bytes, and explicit network/filesystem/subprocess/shell denial. These are design constraints for later isolated execution; this package does not claim OS-level enforcement. The runtime rejects unknown capability handles or unexpected argument keys before execution.

## Qwen visibility

Qwen-visible payloads may contain only fields permitted by `QWEN_VISIBLE_PYTHON_INTERFACE.schema.json`.

They must not contain:

- Python source or bytecode;
- filenames or module paths;
- stack traces or exception representations;
- function implementation names (`strict_status`, `threshold_relation`, `interval_threshold`);
- AST dumps, hashes of source fragments or comments;
- hidden case IDs / expected labels.

Public opaque handles (`py_cap_01` etc.) are interface identifiers, not implementation names.

## Failure semantics

All failures are fail-closed and normalized to one of the public codes in `PYTHON_TOOL_API.schema.json`. Raw program results must contain exactly `status` and `value`, so a program cannot inject provenance into the trusted wrapper. Raw exceptions are retained only in evaluator-side diagnostics and are never copied into student prompts.

## Reproducibility

The module, API contract, mapper, cases, verifier and mutation plan are hash-frozen together. A candidate is invalid if clean deterministic reruns differ byte-for-byte after canonical JSON serialization.

## Security mutations

The mutation suite must prove rejection of at least: hidden lookup table, case-ID branch, wrong logic branch, arithmetic inversion, stale version, fabricated provenance, forbidden import, filesystem attempt, subprocess/shell attempt and Qwen-visible source leak.
