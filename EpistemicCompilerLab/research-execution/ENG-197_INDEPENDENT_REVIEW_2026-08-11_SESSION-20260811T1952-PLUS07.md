# ENG-197 — Distinct Independent Causal and Database Systems Review

**Verdict: REVISE**

Review session identity: `ChatGPT GPT-5.6 Sol / Distinct Independent Causal and Database Systems Reviewer / 2026-08-11T19:52+07:00`.

## Conflict and access statement

This is a distinct reviewer session. This session did not produce, remediate, or execute the frozen candidate and did not create the producer handoff. Producer and prior conflicted-review conclusions were not accepted as evidence. Linear history was read only as orientation; every acceptance finding below was independently checked against immutable GitHub commit content, the retained GitHub Actions run/job, and the downloaded retained artifact.

No HOLDOUT or REPLICATION data was accessed or used.

## Reviewed identity

- Linear: `ENG-197`
- scientific/runtime candidate: `f703f958dd720ce9bdaeaf26ed4d8eafc0c638ac`
- producer handoff commit: `3b3ffa5ce2bed1e0638231e64dc23e9c88158849`
- handoff: `EpistemicCompilerLab/research-execution/handoffs/ENG-197-LIVE-POSTGRES-2026-08-11.json`
- producer PR: `#81`
- retained run: `31483902560`
- retained job: `93754801806`
- retained artifact: `9098310980`

`f703f958... -> 3b3ffa5...` is exactly one commit and changes only the handoff JSON. The retained artifact metadata binds `head_sha=f703f958...`. Candidate identity therefore passes.

## Independent acceptance checks

### 1. Freeze closure — PASS for retained CI execution

The candidate contains a self-excluded manifest with exactly 34 files. The manifest binds the implementation-neutral contract, call/result schemas, source, query registry, evaluator expectations, generator, generated package and package manifest, adapter, DB executor, strict-subset eligibility, live smoke, post-smoke differential, verifier, runtime/dependency contract, feasibility input, security artifacts, and PowerShell runners.

The retained job executed static verification and then `build_freeze_manifest.py --check` before the database smoke; the log records `PASS ENG-197 freeze manifest: 34 files` before PostgreSQL execution.

### 2. Real PostgreSQL execution — PASS except for blocker B1 below

The retained job did execute a real PostgreSQL service, not the Python reference oracle. `db_executor.py` performs the constant parameterized call `cursor.execute(query, params)` and does not import the reference oracle. `live_postgres_smoke.py` likewise does not import it; the reference comparison occurs only in the separate post-smoke differential.

Observed runtime evidence:

- PostgreSQL base release `18.4`;
- `server_version_num=180004`;
- raw server version `18.4 (Debian 18.4-1.pgdg13+1)`;
- `psycopg=3.3.4`;
- observed image RepoDigest `postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636`.

### 3. Pre-score boundary and retained bytes — PASS

The live path executes and persists every DB result first, then parses evaluator expectations. Four retained records have:

- `stage=pre_score_db_result`;
- `execution_owner=postgresql`;
- canonical `result_bytes_utf8`;
- `result_sha256`;
- `score=null`.

I independently downloaded artifact `9098310980`. It contains exactly seven files: live report, subset-equivalence report, CI attestation, and four `pre-score/*.json` files. Recomputed artifact ZIP SHA-256 is `8c18ad4496fba0386224d21a6f787875518368b9022186638141fc11e31b563d`, matching GitHub metadata and handoff. Recomputed live report SHA-256 is `23553d49c2c81104a59e899e7aca15199079df8c5d93cab1ad618e82c9e7f0e2`; subset-equivalence SHA-256 is `73ad5f52cb47df4133841abd6351f6341243ae64783bbc716a7d3e01c3f8c588`. All four pre-score file SHA-256 values independently match the handoff.

### 4. Four-state semantics, recursive closure, provenance — PASS for the frozen strict subset

The SQL function owns retrieval, recursive positive closure, status and action. It implements:

- positive only -> `supported` / `accept`;
- negative only -> `refuted` / `reject`;
- positive + negative -> `conflicting` / `review`;
- neither -> `unknown` / `review`.

`proto-01` exercises recursive positive closure from root assertion `a-001` through the unary strict implication to the queried proposition and returns root evidence `[a-001]` with source provenance `[src-spec-001]`.

The post-smoke differential is exact 4/4 for `status/action/root-evidence/source-provenance` and explicitly sets `proof_graph_equivalence_claimed=false`.

### 5. Strict relational subset — PASS

`eng197.relational-subset.v1` declares `decision_timing=before_split_assignment_outcome_blind`. `subset_eligibility.py` accepts source structure only and has no evaluator/model-output/status/action input. Unknown structures and unsupported dependency, multi-premise, negative-premise, negative-head, polarity-transform, priority/exception, NAF, arithmetic and lossy-provenance cases fail closed rather than being approximated.

M16 does not expose the full M6 proof graph. Equality is limited to status, action, root evidence and source provenance. `M16 vs M6` therefore remains a trusted-result-interface bundle contrast, not proof-equivalence.

### 6. Security — PASS for the exercised reader path

The adapter exposes no free SQL and rejects undeclared endpoints and extra arguments. SQL text is constant and arguments are parameter-bound.

The live role attestation verifies `relational_cmp_reader` is NOLOGIN, non-superuser, without CREATEDB, CREATEROLE, REPLICATION, BYPASSRLS, and with zero inherited memberships. Under `SET ROLE relational_cmp_reader`, real INSERT/UPDATE/DELETE/CREATE TABLE attempts fail with PostgreSQL insufficient-privilege errors; the PostgreSQL service log independently contains those failures.

### 7. M15 — PASS as DEV-only only

The frozen catalogue exposes exactly one semantic endpoint, `resolve_claim`. Therefore M15 cannot support a query/endpoint-selection estimand. The frozen visibility contract correctly limits it to `DEV_ONLY_SINGLE_ENDPOINT_SCHEMA_DIAGNOSTIC` / typed-call construction and schema/guide usability. It must not be used as evidence of endpoint selection.

### 8. M16 causal status — scientifically adequate, but final acceptance blocked by runtime freeze defect

The comparator is scientifically aligned with the causal question: it is a pure relational, conventional trusted-execution result interface with frozen outcome-blind call selection. SQL owns closure/status/action, so M16 is not M14/B* eligible. The strict-subset contract prevents unfair semantic approximation.

Absent the runtime/freeze blockers below, the evidence is sufficient for M16 to be an eligible candidate falsification comparator. Because ENG-197 acceptance is not complete, this review does **not** record `M16 = accepted eligible falsification comparator` yet.

### 9. Feasibility — PASS as bounded TRAIN/DEV evidence only

Final retained-run measurements are real DB-path observations:

- DB build: `19,656,318 ns`;
- DB call latency min/median/max: `815,403 / 938,614 / 1,657,447 ns`;
- relation/index bytes: `147,456`;
- generated package: `7,878 bytes`.

These are infrastructure observations, not production-capacity estimates. The four smoke cases are semantic/infrastructure conformance cases, not additional benchmark N and not WP-006 power evidence. ENG-158/WP-006 and ENG-188/WP-007 still own powered eligible-scenario counts, source-family diversity, accepted hardware-profile distributions, tokens/context and annotation/adjudication cost.

## Substantive blockers

### B1 — the container image is digest-attested after pull, not actually digest-pinned before execution

This is the decisive acceptance blocker.

The frozen GitHub workflow declares the service as `image: postgres:18.4`. The retained log shows `docker pull postgres:18.4`, then records the RepoDigest returned for whatever image that mutable tag resolved to on that run. Only after the service exists does the workflow export `ENG197_POSTGRES_IMAGE_DIGEST`.

`RUNTIME_DEPENDENCIES.json` freezes PostgreSQL version and `server_version_num`, but contains no expected/frozen image digest. `live_postgres_smoke.py` labels execution `container_digest_pinned` merely when a digest-shaped environment value is present; it does not compare that value with a frozen expected digest. The CI evidence assertion likewise checks only `startswith('postgres@sha256:')`, not equality to a precommitted digest.

Therefore the retained execution has strong **digest attestation**, but it is not a **digest-pinned execution** in the reproducibility/governance sense required by this review. The handoff's `execution_identity=container_digest_pinned` overstates the actual runtime lock.

Minimal remediation:

1. freeze `postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636` (or a deliberately chosen replacement digest) in the runtime contract;
2. start the CI PostgreSQL service by exact digest, not mutable `postgres:18.4` tag;
3. make the smoke and CI evidence contract require exact equality with the frozen digest;
4. regenerate the freeze manifest, rerun the full retained evidence on the new candidate, and produce a new immutable handoff.

### B2 — the frozen local PostgreSQL runner rewrites the freeze manifest before checking it

`EpistemicCompilerLab/scripts/run-relational-postgres-smoke.ps1` calls `build_freeze_manifest.py` without `--check`, which rewrites the committed manifest from the current worktree, and only then calls `--check`. Thus a locally modified frozen file can be normalized into a new manifest immediately before DB execution instead of failing closed on drift.

This does **not** invalidate run `31483902560`, because that GitHub Actions path ran `--check` directly without first rewriting the manifest. It does, however, violate the frozen reviewer/reproduction runner's fail-closed freeze semantics.

Minimal remediation: remove manifest generation from the execution runner; execution should only run `build_freeze_manifest.py --check`. Keep manifest generation as a separate explicit producer-only freeze operation.

## Final verdict

**REVISE** — not PIVOT.

The comparator itself remains scientifically appropriate and answers the intended causal question. No semantic redesign is required. The blockers are bounded reproducibility/freeze defects: true pre-execution container digest pinning and fail-closed local manifest verification.

Until a new candidate closes B1/B2 and is independently re-reviewed:

- `M15 = DEV-only`;
- M16 remains a scientifically valid **candidate** falsification comparator but is **not yet accepted**;
- no automatic confirmatory inclusion is authorized;
- ENG-156 / WP-006 / WP-007 still separately own scope, power and feasibility;
- ENG-199 remains blocked by ENG-197 and must not be started on the basis of this review;
- HOLDOUT/REPLICATION remain unauthorized and unaccessed.
