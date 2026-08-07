# ENG-197 — Pure relational comparator contract

Status: **producer candidate, TRAIN/DEV prototype only; independent review required**  
Parent: `WP-004 / ENG-156`  
Scientific label: **pure relational trusted-execution comparator**  
Implementation vehicle: PostgreSQL package generated deterministically from the same frozen source contract. AppForge may later replace the small generator without changing this contract.

## INPUTS

- the same normalized source assertions, scope, version and provenance available to matched modes;
- strict positive implication edges required by the frozen task subset;
- a typed question-to-call contract;
- immutable fixed-weight Qwen profile supplied by the parent run protocol;
- no HOLDOUT or REPLICATION content in this prototype.

## ACTION

The builder deterministically compiles the normalized source package into PostgreSQL DDL, seed/load SQL, one read-only typed query function, a typed catalogue, a frozen Qwen guide and a package manifest. M15 lets Qwen select and populate the typed call. M16 uses a frozen outcome-blind registry to select the same call before Qwen runs.

PostgreSQL owns retrieval, positive recursive closure, four-state epistemic status and the frozen decision action. Qwen never receives unrestricted SQL. Qwen owns natural-language rendering only; M15 additionally owns query formation.

## MACHINE-CHECKABLE OUTPUTS

- `contract.json` — implementation-neutral scientific and security contract;
- `call.schema.json` and `result.schema.json` — typed interface schemas;
- `prototype/source.prototype.json` — synthetic TRAIN/DEV-only normalized source;
- `prototype/query-registry.prototype.json` — M16 outcome-blind call registry;
- `prototype/evaluator/expected.prototype.json` — evaluator-only expected statuses, never generator-visible;
- `prototype/generate_package.py` — deterministic package generator;
- `prototype/adapter.py` — typed-call/result transport validator, not a semantic service;
- `prototype/reference_oracle.py` — test-only independent reference semantics;
- `prototype/generated/` — byte-frozen generated package and hashes;
- `prototype/verify.py` — deterministic rebuild, leakage, security and contract checks;
- `../handoffs/ENG-197.json` — immutable producer handoff after publication.

## Semantic ownership

| Responsibility | M15 | M16 |
| --- | --- | --- |
| source normalization | frozen upstream contract | frozen upstream contract |
| query formation | Qwen | frozen outcome-blind registry |
| typed call validation | adapter | adapter |
| retrieval | PostgreSQL | PostgreSQL |
| recursive closure | PostgreSQL | PostgreSQL |
| status computation | PostgreSQL | PostgreSQL |
| decision action | PostgreSQL | PostgreSQL |
| result transport | adapter | adapter |
| natural-language rendering | Qwen | Qwen |

Because SQL computes status and action, M15/M16 are **trusted-execution comparators**. They are never eligible for M14/B* selection. The comparison with M6 therefore asks whether the explicit epistemic decision-frame interface adds value over a conventional relational trusted runtime, not whether executable semantics exist at all.

## Typed interface

The confirmatory path exposes only declared catalogue endpoints. The prototype endpoint is `resolve_claim(proposition_id, scope_id, version)`. The adapter compiles it to a parameterized function call; model-provided SQL text, endpoint substitution, DDL/DML and undeclared functions have no representation in the call schema.

The function returns exactly one typed summary row with `status_code`, `action_code`, evidence and provenance. The prototype maximum-row policy is therefore one row. Any zero/multiple-row transport anomaly fails the run; it is never truncated or repaired.

## Failure attribution

Failures are frozen into separate layers: `query_formation`, `adapter_validation`, `db_execution`, `result_transport`, and `rendering`. A wrong M15 endpoint/argument choice is not counted as a database failure. A valid call with DB failure is not counted as a renderer failure. Raw typed calls and canonical result bytes are recorded before any scorer fields can be added.

## Leakage boundary

The generator sees only normalized source content. Evaluator case IDs, questions and expected statuses live in `prototype/evaluator/` and are not imported by the generator. Generated names, comments, guide text and seed data contain no per-case expected status or answer. Generic status vocabulary is part of the declared runtime semantics and is not a case-specific answer leak.

## Security boundary

- no unrestricted SQL field exists;
- only catalogue endpoint names are accepted;
- calls use positional parameter binding;
- source seed literals are escaped during trusted build;
- runtime function is `STABLE` and read-only;
- no network/filesystem primitive is exposed;
- build SQL revokes public access and grants only schema usage, table select and function execute to a no-login reader role;
- DB snapshot and generated procedures are hash-frozen for a run block.

## Required contrasts and pivots

- `M15 vs M16`: cost of Qwen query formation/tool use;
- `M16 vs M6`: pure relational trusted result interface versus explicit epistemic decision frame;
- `M15 vs no-guide`: DEV-only interface-teaching ablation unless WP-006/WP-007 authorize otherwise;
- `M16 vs M14`: execution-bundle diagnostic only, never a claim that M16 is a non-compiled baseline;
- later `M16 vs M17`: pure SQL versus SQL→Prolog hybrid ownership.

If M16 is non-inferior to M6, claims that Prolog or the full custom frame is necessary must be removed. If M15 is weak and M16 strong, query formation is the bottleneck. If the guide alone explains the gain, report bounded interface teaching. If this conventional package matches M6 at lower cost, the engineering recommendation prefers the simpler package.

## FORBIDDEN ACTIONS

- adding M15/M16 to confirmatory execution before independent WP-004 adjudication;
- reading HOLDOUT/REPLICATION content during this producer task;
- free SQL or write credentials in the model path;
- hidden Python/Prolog semantic execution in M15/M16;
- outcome-dependent endpoint selection, result truncation or repair;
- encoding expected case status/answer in source IDs, schema names, guide or seed values;
- calling AppForge itself the treatment.

## PASS GATE

Producer evidence passes only when `python prototype/verify.py` succeeds from this directory, the committed generated package byte-matches a clean deterministic rebuild, evaluator-only expected fields do not leak into generated artifacts, and the producer handoff records hashes plus the absence of HOLDOUT/REPLICATION access. Independent reviewer acceptance remains separate.

## STOP / PIVOT

STOP if the relational subset requires hidden bespoke semantic code, if a source assertion/provenance item cannot be represented losslessly, if row limits would require truncation, or if any generated artifact contains evaluator case IDs/questions. PIVOT to M16-only or reject the comparator if query formation is infeasible; narrow the paper if M16 matches/exceeds M6.
