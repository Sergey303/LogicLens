# ENG-197 — Live PostgreSQL smoke contract

Status: **mandatory before producer handoff to re-review**. This is TRAIN/DEV synthetic execution evidence, not a behavioral Qwen result.

## Runtime

The remediation candidate is frozen by `RUNTIME_DEPENDENCIES.json`:

- PostgreSQL server exactly `18.4` (`server_version_num = 180004`);
- container execution for re-review exactly `postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636`;
- mutable image tags such as `postgres:18.4` are **not execution identities** and are prohibited for re-review evidence;
- `psycopg[binary]==3.3.4`;
- database name must start with `eng197_`.

The image digest is selected **before container creation**. Recording whatever digest happened to be pulled from a mutable tag is digest attestation, not a frozen execution pin, and is insufficient for this remediation round.

The database-name guard exists because the smoke deliberately rebuilds the `relational_cmp` schema. Do not point it at a general development or production database.

## Freeze boundary

Execution is strictly check-only with respect to `ENG-197_FREEZE_MANIFEST.json`.

Before dependency installation or database access, `run-relational-postgres-smoke.ps1` executes:

```text
build_freeze_manifest.py --check
```

and fails on any mismatch. The execution runner **must never regenerate the manifest**.

Manifest generation without `--check` is a separate producer freeze operation performed intentionally before a candidate is handed off. This prevents a modified frozen file from self-authorizing itself by manufacturing a new manifest at execution time.

The frozen closure includes the exact PostgreSQL execution workflow itself, so the pre-execution image reference is hash-bound to the candidate.

## Required sequence

1. Require exact byte equality with the already-frozen manifest; do not regenerate it.
2. Require `ENG197_POSTGRES_IMAGE_DIGEST` to equal the frozen `required_container_image_digest`.
3. Start/connect to a disposable database whose name begins `eng197_` using the exact pre-selected image digest.
4. Verify PostgreSQL release pins before modifying schema.
5. Acquire the ENG-197 advisory lock for the duration of the run.
6. `DROP SCHEMA IF EXISTS relational_cmp CASCADE` and rebuild from committed `generated/schema.sql`, `generated/seed.sql`, `generated/permissions.sql`.
7. Attest `relational_cmp_reader`: no login, superuser, CREATEDB, CREATEROLE, replication, BYPASSRLS or inherited role membership. An unsafe pre-existing role makes the run FAIL; the smoke does not silently rewrite server-global role state.
8. Switch to the frozen read-only role for the model/runtime execution path.
9. Execute every M16 registry call through `prototype/db_executor.py` and its constant parameterized SQL path.
10. Persist the actual canonical PostgreSQL row bytes and hashes to `pre-score/*.json` **before** evaluator expectations are semantically parsed.
11. Only after all DB artifacts exist, open evaluator-only TRAIN/DEV expectations and compare status/action.
12. Require exact coverage of `supported`, `refuted`, `conflicting`, `unknown`; `proto-01` must additionally prove recursive positive closure from `a-001` through `r-001` to `p-allowed` with the correct root evidence/provenance.
13. Run adapter and database permission negatives.
14. Record measured build time, per-call latency, generated package bytes and database relation/index bytes.
15. Emit `eng197-live-postgres-report.json` and retain every pre-score record.
16. **After the smoke has passed**, run `build_subset_equivalence_report.py`. It compares the already-persisted DB result bytes against the direct-source reference semantics and emits `eng197-subset-equivalence-report.json`.

The post-smoke differential is intentionally separate so `reference_oracle.py` never participates in database execution or pre-score result creation.

## Permission/security negatives

Under `SET ROLE relational_cmp_reader`:

- declared parameterized `resolve_claim` must execute;
- direct `INSERT`, `UPDATE`, `DELETE` and `CREATE TABLE` must fail with insufficient privilege;
- model-level free SQL and undeclared endpoints must already be rejected by the adapter without database execution.

No failed write is ignored: each expected denial is named in the report.

## Evidence identity

The report records:

- PostgreSQL `version()` string, `server_version`, `server_version_num`;
- Psycopg and libpq versions;
- database name;
- reader-role attribute/membership attestation;
- execution identity `container_digest_pinned`;
- the exact frozen container digest;
- source/package/freeze-manifest hashes;
- build SQL hashes;
- every pre-score artifact hash;
- all expected security-negative outcomes.

A native PostgreSQL installation may be used only for developer diagnostics in this remediation round; it is not sufficient evidence for the distinct independent re-review that identified the pre-execution digest-pin blocker.

## Lossless subset differential

`eng197-subset-equivalence-report.json` must show exact equality for every prototype case on the fields owned by the frozen relational subset:

- `status_code`;
- `action_code`;
- root `evidence` IDs;
- source `provenance` IDs.

It explicitly records `proof_graph_equivalence_claimed=false`; M16 does not expose the M6 full proof graph.

## Failure semantics

Any manifest drift, image-digest drift or absence, runtime-version drift, non-disposable database name, unsafe reader role, SQL error, status/action/evidence mismatch, recursive-closure mismatch, permission negative that unexpectedly succeeds, missing pre-score artifact or subset differential mismatch makes the run FAIL.

The smoke has no fallback to `reference_oracle.py`. Python reference semantics remain a test oracle only and cannot substitute for PostgreSQL execution.

## Producer freeze and execution commands

Manifest generation is a separate producer action, performed once after the intended candidate bytes are complete:

```powershell
python 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\research-execution\relational-comparator\prototype\build_freeze_manifest.py'
```

After that manifest is committed, execution uses only the check-only launcher. The caller must start PostgreSQL from the exact frozen digest and set both the disposable DSN and the same digest in `ENG197_POSTGRES_IMAGE_DIGEST`:

```powershell
$env:ENG197_POSTGRES_DSN = '<disposable eng197_ database DSN>'
$env:ENG197_POSTGRES_IMAGE_DIGEST = 'postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636'
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' relational-postgres-smoke
```

The launcher checks the frozen manifest and image digest, installs the exact frozen Python driver dependency, executes the live smoke, then emits the post-smoke subset-equivalence report. Evidence is written under `artifacts/eng-197/postgres-smoke/` by default. Do not commit credentials.
