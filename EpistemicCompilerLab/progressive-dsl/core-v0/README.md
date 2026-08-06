# Synthetic Epistemic semantic kernel v0

This directory contains a **domain-neutral synthetic semantic kernel** for isolated smoke checks of four already-tested semantic ideas:

- strict support / refutation / unknown / conflict separation;
- declared logical-head derivation from `all` / `any` bodies;
- deterministic numeric normalization and interval abstention;
- exact dependency-aware opinion fusion compatible with DSL-D2 policy.

It is deliberately **not**:

- a test on CTO-course data;
- a verified capsule/package runtime;
- a replacement for `tools/capsule_query.py`, `capsule_query_dsl_b.py` or `capsule_query_dsl_c.py`;
- confirmatory evidence for WP-003 / ENG-155;
- permission to bypass source assertions, package hashes, provenance or SWI-Prolog verification.

Real course-owned consumer tests live in `Sergey303/CTO-Practical-Simulation` and must pin an exact LogicLens commit.

## Frozen contract

`manifest-v0.json` pins SHA-256 values for:

- the runtime;
- JSON Schema;
- 13 synthetic cases;
- complete expected result frames.

Every evidence-bearing input carries an explicit dependency group and provenance reference. Duplicate semantic IDs, malformed rationals, missing provenance and incompatible dimensions fail closed.

The acceptance path invokes `opinion-d2/runtime.py::build_frame()` without `skip_prolog`, so the D2 cases are independently checked by SWI-Prolog. The local `--skip-prolog` option exists only for syntax/debug work and prints that the run is not acceptance evidence.

## Run

From any PowerShell location:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' synthetic-kernel-tests
```

The previous `progressive-core-tests` action remains as a compatibility alias but refers to the same synthetic-kernel contract.
