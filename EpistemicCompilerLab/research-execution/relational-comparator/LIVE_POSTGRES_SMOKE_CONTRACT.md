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
5. Switch to the frozen read-only `relational_cmp_reader` role for the model/runtime execution path.
6. Execute every M16 registry call through `prototype/db_executor.py` and its constant parameterized SQL path.
7. Persist the actual canonical PostgreSQL row bytes and hashes to `pre-score/*.json` **before** evaluator expectations are consulted.
8. Only after persistence, compare the rows to evaluator-only TRAIN/DEV expectations.
9. Require exact coverage of `supported`, `refuted`, `conflicting`, `unknown`; `proto-01` must additionally prove the recursive positive closure from `a-001` through `r-001` to `p-allowed`.
10. Run adapter and database permission negatives.
11. Record measured build time, per-call latency, generated package bytes and database relation/index bytes.
12. Emit one machine-readable `eng197-live-postgres-report.json` and retain every pre-score record.

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
- execution identity (`native_exact_version_not_image_pinned` or `container_digest_pinned`);
- container digest when a container is used;
- source/package/freeze-manifest hashes;
- build SQL hashes;
- every pre-score artifact hash;
- all expected security-negative outcomes.

A native exact-version run is acceptable producer evidence but is explicitly not represented as an image-bit-identical environment. Independent reviewer may require an image-pinned rerun before final acceptance.

## Failure semantics

Any runtime-version drift, non-disposable database name, SQL error, status/action/evidence mismatch, recursive-closure mismatch, permission negative that unexpectedly succeeds, missing pre-score artifact, or manifest drift makes the smoke FAIL.

The smoke has no fallback to `reference_oracle.py`. Python reference semantics remain a test oracle only and cannot substitute for PostgreSQL execution.

## Command

After installing the frozen driver dependency and setting the DSN:

```powershell
$env:ENG197_POSTGRES_DSN = 'postgresql://USER:PASSWORD@localhost:5432/eng197_smoke'
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' relational-postgres-smoke
```

The command writes evidence under `artifacts/eng-197/postgres-smoke/` by default. Do not commit credentials.
