# ENG-197 — Independent-review remediation matrix

Review source: `ENG-197_INDEPENDENT_REVIEW_2026-08-07.md` / Linear independent **REVISE**.  
Producer state: **In Progress**. This matrix is not reviewer acceptance.

| Blocker | Required correction | Producer remediation | Current evidence state |
| --- | --- | --- | --- |
| B1 — PostgreSQL never executed | real clean PostgreSQL build/run, four states, recursive closure, permission negatives, runtime identity | `LIVE_POSTGRES_SMOKE_CONTRACT.md`, `RUNTIME_DEPENDENCIES.json`, `prototype/live_postgres_smoke.py`, local launcher | **PENDING EXECUTION** — no live PostgreSQL report yet |
| B2 — M15 single endpoint is not meaningful query selection | expand to multiple semantically distinct endpoints or narrow M15 | `M15_IDENTIFIER_VISIBILITY_CONTRACT.md`; M15 is DEV-only typed-call/schema diagnostic; M16 is the only potential ENG-197 WP-004 candidate | **DESIGN CLOSED; reviewer confirmation pending** |
| B3 — strict-subset equivalence/losslessness not proven | define exact subset and reject unsupported cases; differential evidence | `RELATIONAL_STRICT_SUBSET_MAPPING.md`, `RELATIONAL_SUBSET_CONTRACT.json`, fail-closed `subset_eligibility.py`, post-smoke `build_subset_equivalence_report.py` | **DESIGN CLOSED / DIFFERENTIAL PENDING EXECUTION** |
| B4 — incomplete immutable hash closure | bind scientific, runtime, visibility, evaluator, security, generator, launcher and verifier artifacts | `prototype/build_freeze_manifest.py` covers 30+ files including runner/launcher and post-smoke differential | **MANIFEST BUILDER READY; frozen manifest pending exact execution checkout** |
| B5 — pre-score path used simulated oracle rows | execute parameterized PostgreSQL and persist actual DB-returned bytes before expected outcomes | `prototype/db_executor.py`; live smoke Phase 1 persists `pre-score/*.json`, Phase 2 opens evaluator outcomes; live path cannot import `reference_oracle.py` | **IMPLEMENTED / LIVE BYTES PENDING EXECUTION** |
| B6 — feasibility placeholders | measure DB build, latency, DB storage and pass exact evidence to WP-006/WP-007 | `FEASIBILITY_INPUT.json` binds required metrics to `eng197-live-postgres-report.json`; live smoke records ns/bytes and M16 subset eligibility must feed powered paired N | **PENDING EXECUTION** |

## Additional reviewer-visible corrections

- M16 result intentionally returns status/action/root evidence/source provenance, **not** the M6 full proof graph. `M16 vs M6` is therefore documented as a conventional trusted-result-interface bundle contrast, not proof equivalence.
- Unsupported source features are rejected before split assignment; they are never approximated to keep M16 in the benchmark.
- PostgreSQL 18.4 and Psycopg 3.3.4 are pinned for this remediation candidate.
- reader-role attributes/memberships and direct write/create denials are checked live.
- generated SQL is executed statement-by-statement with a frozen splitter that respects single-quoted and dollar-quoted blocks.
- `reference_oracle.py` participates only in the post-smoke differential report, never database execution or pre-score creation.

## Transition rule

Do **not** move ENG-197 to `In Review` merely because the implementation exists. Producer handoff becomes eligible only after:

1. static `relational-comparator-tests` passes on the exact candidate checkout;
2. live PostgreSQL smoke is `PASS` under the frozen runtime;
3. all four DB pre-score artifacts are retained;
4. subset-equivalence report is all-exact for frozen result fields;
5. freeze manifest from that exact checkout is retained;
6. measured feasibility fields are available in the live report;
7. no HOLDOUT/REPLICATION content was accessed.

After that, a distinct Independent Causal and Database Systems Reviewer must issue `PASS / REVISE / PIVOT`; producer does not self-accept.
