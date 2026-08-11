# ENG-197 — Independent-review remediation matrix

Review source: `EpistemicCompilerLab/research-execution/ENG-197_INDEPENDENT_REVIEW_2026-08-11_SESSION-20260811T1952-PLUS07.md` / Linear independent **REVISE**.  
Producer state: **In Progress after re-review**. This matrix is producer remediation state, not reviewer acceptance.

## Current blockers from 2026-08-11 independent re-review

| Blocker | Required correction | Producer remediation | Current evidence state |
| --- | --- | --- | --- |
| B1 — container digest was attested after mutable-tag pull, not pinned before execution | freeze exact `postgres@sha256:...`; create service/container by digest; require exact equality in execution path; new candidate/run/handoff | `RUNTIME_DEPENDENCIES.json` now freezes `postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636`; workflow service uses that digest directly; local runner requires exact `ENG197_POSTGRES_IMAGE_DIGEST`; workflow itself is part of freeze closure | **IMPLEMENTED / NEW LOCAL REAL-DB EXECUTION PENDING** |
| B2 — local frozen runner regenerated manifest before checking it | execution runner must be check-only; regeneration must be separate producer freeze operation | `run-relational-postgres-smoke.ps1` now calls only `build_freeze_manifest.py --check` before dependency installation/DB access; manifest generation without `--check` is documented as a separate producer action | **IMPLEMENTED / NEW FREEZE + EXECUTION PENDING** |

## Previous blockers retained as closed design/execution constraints

| Previous blocker | Current status |
| --- | --- |
| PostgreSQL semantics not executed | **CLOSED substantively** by retained real PostgreSQL 18.4 evidence; must be re-executed on the new digest-pinned/check-only candidate because candidate bytes changed |
| M15 single endpoint not meaningful query selection | **CLOSED**: M15 remains `DEV_ONLY_SINGLE_ENDPOINT_SCHEMA_DIAGNOSTIC`; no routing/query-selection claim |
| strict-subset equivalence/losslessness | **CLOSED for declared subset**: outcome-blind fail-closed eligibility; no approximation; post-smoke exact differential |
| incomplete immutable hash closure | **CLOSED structurally, being refrozen**: closure now additionally binds the exact live-PostgreSQL workflow |
| pre-score simulated oracle rows | **CLOSED**: DB executor persists actual PostgreSQL-returned bytes before evaluator parsing |
| feasibility placeholders | **CLOSED for bounded TRAIN/DEV infrastructure observation**; still not final WP-007 capacity/profile evidence |

## Reviewer-visible invariants

- M16 result intentionally returns status/action/root evidence/source provenance, **not** the M6 full proof graph. `M16 vs M6` remains a conventional trusted-result-interface bundle contrast, not proof equivalence.
- Unsupported source features are rejected before split assignment; they are never approximated to keep M16 in the benchmark.
- PostgreSQL `18.4`, `server_version_num=180004`, Psycopg `3.3.4`, and the exact container RepoDigest are frozen for the re-review candidate.
- Mutable tag selection is prohibited for re-review execution identity.
- The execution workflow is hash-bound into the same freeze closure as contracts, generator, SQL, verifier, runners and evaluator fixtures.
- Execution must fail on manifest drift; it is not allowed to regenerate the manifest.
- reader-role attributes/memberships and direct write/create denials are checked live.
- `reference_oracle.py` participates only in the post-smoke differential report, never database execution or pre-score creation.

## Transition rule

Do **not** return ENG-197 to independent review merely because the two code fixes exist. A new producer handoff is eligible only after:

1. the intended remediation bytes are complete;
2. producer deliberately regenerates and commits the new exact freeze manifest as a separate freeze operation;
3. static `relational-comparator-tests` passes on that exact candidate checkout;
4. a disposable PostgreSQL container is created from the exact frozen `postgres@sha256:...` reference, never from a tag;
5. local real PostgreSQL smoke is `PASS` with exact digest equality enforced before the smoke path;
6. all four DB pre-score artifacts are retained;
7. subset-equivalence report is all-exact for frozen result fields;
8. measured feasibility fields are retained as bounded infrastructure observations only;
9. a new immutable producer handoff binds candidate SHA + freeze manifest + local evidence hashes;
10. no HOLDOUT/REPLICATION content was accessed.

After that, a **new distinct Independent Causal and Database Systems Reviewer** must issue `PASS / REVISE / PIVOT`. Producer does not self-accept. Until independent PASS, M16 is not recorded as an accepted eligible falsification comparator and ENG-199 remains blocked.
