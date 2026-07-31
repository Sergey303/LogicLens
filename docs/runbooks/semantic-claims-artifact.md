# Oracle Semantic Claims artifact v0

This research-only artifact freezes the first replay boundary after canonical facts:

```text
validated benchmark case
  -> exact oracleSemanticClaims
  -> deterministic semantic-claims artifact
```

It does not infer roles, call an LLM, compute a dataset profile, choose a component,
or modify an active epoch.

## Create

```powershell
python .\tools\semantic_claims_artifact.py create `
  --case-id clear-revision-comparison `
  --output .\artifacts\semantic-claims\clear.json
```

## Verify

```powershell
python .\tools\semantic_claims_artifact.py verify `
  --artifact .\artifacts\semantic-claims\clear.json
```

Both commands validate the frozen benchmark through
`verify_semantic_planning_benchmark.py` before reading a case.

## Contract boundary

The artifact contains:

- exact benchmark, manifest, case path, and case hashes;
- exact task language and goal plus a hash of task text;
- producer fixed to `oracle-fixture` and source field fixed to
  `oracleSemanticClaims`;
- a deep copy of the claims in their original order;
- a domain-separated `artifactHash`;
- canonical UTF-8 JSON bytes.

Verification compares the complete artifact with a newly reconstructed artifact from
the frozen case. A role rename, broadening, normalization, reordering, stale case,
changed producer, unknown field, recomputed hash over altered claims, or merely
non-canonical JSON formatting is rejected.

The v0 producer is intentionally restricted to the oracle fixture. Analyzer and LLM
outputs require later measured-run contracts rather than overloading this artifact.
