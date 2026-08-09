# ENG-197 — Pure relational comparator contract

Status: **remediation producer candidate; TRAIN/DEV only; live PostgreSQL evidence still required; independent review required**  
Parent: `WP-004 / ENG-156`  
Scientific label: **pure relational trusted-execution comparator**

## Current adjudication

- **M16 Relational Result Interface:** may become a WP-004 falsification candidate only after the frozen live PostgreSQL smoke, lossless-subset checks, complete freeze closure and independent reviewer PASS.
- **M15 Relational Query Agent:** **DEV-only** in the current single-endpoint design. It may diagnose typed-call construction/schema following, but must not be reported as endpoint/tool-selection evidence. See `M15_IDENTIFIER_VISIBILITY_CONTRACT.md`.

Neither mode is automatically authorized for HOLDOUT.

## What the relational comparator tests

The builder deterministically compiles the frozen normalized source package into PostgreSQL DDL/data, one declared parameterized read-only function, a typed catalogue and a conventional result interface. PostgreSQL owns retrieval, unary positive recursive closure, four-state status and frozen status→action mapping. Qwen owns final rendering; M15 additionally constructs the typed call in DEV.

This is intentionally a **conventional relational trusted-result alternative**, not a reimplementation of every M6 feature.

## Lossless subset boundary

`RELATIONAL_SUBSET_CONTRACT.json` and `RELATIONAL_STRICT_SUBSET_MAPPING.md` define the only scenarios eligible for M16:

- exact scope/version;
- explicit positive/negative assertions;
- direct negative evidence for the queried proposition;
- unary positive strict implication chains;
- no multi-premise rules, dependency fusion, negative rule heads/premises, polarity transforms, priorities/exceptions, negation-as-failure or arithmetic semantic rules;
- complete root evidence and source provenance without truncation.

Eligibility is structural and outcome-blind **before split assignment**. Unsupported/unknown structures are rejected, never approximated. WP-006 must power M16 on the paired eligible count rather than the whole benchmark.

M16 returns status, action, root evidence and source provenance. It does **not** expose the full M6 proof graph. Therefore `M16 vs M6` is a trusted-result-interface bundle contrast, not proof-interface equivalence.

## Real database boundary

The original producer prototype validated SQL text and compared expected semantics with `reference_oracle.py`; that is no longer sufficient acceptance evidence.

`LIVE_POSTGRES_SMOKE_CONTRACT.md` now requires a real PostgreSQL execution path:

1. exact frozen runtime from `RUNTIME_DEPENDENCIES.json`;
2. clean rebuild of committed schema/seed/permissions;
3. actual M16 calls through `prototype/db_executor.py` using parameter binding;
4. persistence of canonical **database-returned** result bytes before evaluator expectations are read;
5. supported/refuted/conflicting/unknown and recursive-closure checks;
6. read-only-role permission negatives;
7. measured build time, DB latency, relation/index storage and artifact hashes.

`reference_oracle.py` remains a test-only independent semantic reference and cannot substitute for the live database path.

## Runtime freeze

Current remediation runtime:

- PostgreSQL `18.4`;
- `psycopg[binary]==3.3.4`;
- disposable database name beginning `eng197_`.

A native exact-version run records that it is not image-bit-identical. A container run must additionally record its image digest.

## Main artifacts

Scientific/boundary:

- `contract.json`;
- `M15_IDENTIFIER_VISIBILITY_CONTRACT.md`;
- `RELATIONAL_STRICT_SUBSET_MAPPING.md`;
- `RELATIONAL_SUBSET_CONTRACT.json`;
- `LIVE_POSTGRES_SMOKE_CONTRACT.md`;
- `RUNTIME_DEPENDENCIES.json`;
- `call.schema.json`, `result.schema.json`;
- `FEASIBILITY_INPUT.json`.

Executable/audit:

- `prototype/generate_package.py`;
- `prototype/adapter.py`;
- `prototype/db_executor.py`;
- `prototype/subset_eligibility.py`;
- `prototype/live_postgres_smoke.py`;
- `prototype/reference_oracle.py` — test reference only;
- `prototype/verify.py`;
- `prototype/build_freeze_manifest.py`;
- `prototype/generated/*`;
- `ENG-197_FREEZE_MANIFEST.json` — generated/frozen from the exact candidate checkout before smoke;
- `scripts/run-relational-comparator-tests.ps1`;
- `scripts/run-relational-postgres-smoke.ps1`.

## Typed interface and security

The declared endpoint is `resolve_claim(proposition_id, scope_id, version)`. The adapter owns a constant parameterized query; model-provided SQL, endpoint substitution, DDL/DML and undeclared fields have no representation in the call schema.

Runtime failures remain layered as identifier preparation, typed-call construction, adapter validation, DB execution, result transport and rendering. Zero/multiple rows fail closed; no result is truncated or repaired.

The live smoke executes the declared path under `relational_cmp_reader` and requires direct INSERT/UPDATE/DELETE/CREATE attempts to fail.

## Local execution

Static producer checks:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' relational-comparator-tests
```

Live PostgreSQL evidence:

```powershell
$env:ENG197_POSTGRES_DSN = 'postgresql://USER:PASSWORD@localhost:5432/eng197_smoke'
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' relational-postgres-smoke
```

The live command installs the exact driver requirement, rebuilds/checks the full freeze closure and writes evidence to `artifacts/eng-197/postgres-smoke/` by default. Credentials are never committed.

## STOP / PIVOT

- If a scenario is outside the frozen relational subset, it is M16-ineligible; do not simplify it.
- If M16 cannot pass real PostgreSQL execution/security evidence, reject it from WP-004.
- If the accepted benchmark cannot provide a powered paired eligible M16 subset, keep M16 DEV-only.
- If M16 matches M6 at lower cost, narrow claims that the custom Prolog/full-frame path is necessary.
- If a future multi-endpoint M15 is desired, version it before HOLDOUT with independent routing ground truth.
- No HOLDOUT/REPLICATION access is authorized by this package.
