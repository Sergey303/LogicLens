# ENG-197 — Live PostgreSQL smoke contract

Status: **mandatory before producer handoff to re-review**. This is TRAIN/DEV synthetic execution evidence, not a behavioral Qwen result.

## Runtime

The remediation candidate is pinned by `RUNTIME_DEPENDENCIES.json`:

- PostgreSQL server exactly `18.4` (`server_version_num = 180004`);
- `psycopg[binary]==3.3.4`;
- database name must start with `eng197_`.

The database-name guard exists because the smoke deliberately rebuilds the `relational_cmp` schema. Do not point it at a general development or production database.

## Required sequence

1. Connect to a disposable database whose name begins `eng197_`.
2. Verify runtime pins before modifying schema.
3. Acquire the ENG-197 advisory lock for the duration of the run.
4. `DROP SCHEMA IF EXISTS relational_cmp CASCADE` and rebuild from committed `generated/schema.sql`, `generated/seed.sql`, `generated/permissions.sql`.
5. Attest `relational_cmp_reader`: no login, superuser, CREATEDB, CREATEROLE, replication, BYPASSRLS or inherited role membership. An unsafe pre-existing role makes the run FAIL; the smoke does not silently rewrite server-global role state.
6. Switch to the frozen read-only role for the model/runtime execution path.
7. Execute every M16 registry call through `prototype/db_executor.py` and its constant parameterized SQL path.
8. Persist the actual canonical PostgreSQL row bytes and hashes to `pre-score/*.json` **before** evaluator expectations are semantically parsed.
9. Only after all DB artifacts exist, open evaluator-only TRAIN/DEV expectations and compare status/action.
10. Require exact coverage of `supported`, `refuted`, `conflicting`, `unknown`; `proto-01` must additionally prove recursive positive closure from `a-001` through `r-001` to `p-allowed` with the correct root evidence/provenance.
11. Run adapter and database permission negatives.
12. Record measured build time, per-call latency, generated package bytes and database relation/index bytes.
13. Emit `eng197-live-postgres-report.json` and retain every pre-score record.
14. **After the smoke has passed**, run `build_subset_equivalence_report.py`. It compares the already-persisted DB result bytes against the direct-source reference semantics and emits `eng197-subset-equivalence-report.json`.

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
- execution identity (`native_exact_version_not_image_pinned` or `container_digest_pinned`);
- container digest when a container is used;
- source/package/freeze-manifest hashes;
- build SQL hashes;
- every pre-score artifact hash;
- all expected security-negative outcomes.

A native exact-version run is acceptable producer evidence but is explicitly not represented as an image-bit-identical environment. Independent reviewer may require an image-pinned rerun before final acceptance.

## Lossless subset differential

`eng197-subset-equivalence-report.json` must show exact equality for every prototype case on the fields owned by the frozen relational subset:

- `status_code`;
- `action_code`;
- root `evidence` IDs;
- source `provenance` IDs.

It explicitly records `proof_graph_equivalence_claimed=false`; M16 does not expose the M6 full proof graph.

## Failure semantics

Any runtime-version drift, non-disposable database name, unsafe reader role, SQL error, status/action/evidence mismatch, recursive-closure mismatch, permission negative that unexpectedly succeeds, missing pre-score artifact, subset differential mismatch or manifest drift makes the run FAIL.

The smoke has no fallback to `reference_oracle.py`. Python reference semantics remain a test oracle only and cannot substitute for PostgreSQL execution.

## Command

After setting the DSN:

```powershell
$env:ENG197_POSTGRES_DSN = 'postgresql://USER:PASSWORD@localhost:5432/eng197_smoke'
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' relational-postgres-smoke
```

The launcher installs the exact frozen Python driver dependency, builds/checks the complete freeze manifest, executes the live smoke, then emits the post-smoke subset-equivalence report. Evidence is written under `artifacts/eng-197/postgres-smoke/` by default. Do not commit credentials.
