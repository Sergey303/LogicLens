# Deterministic Dataset Profile artifact v0

This research-only stage consumes a verified oracle Semantic Claims artifact and
computes dataset structure without reading UI choices or using an LLM:

```text
frozen canonical facts
+ verified semantic claims artifact
  -> trusted dataset-profile-v0 analyzer
  -> deterministic dataset profile artifact
```

## Create

First create the semantic claims input:

```powershell
python .\tools\semantic_claims_artifact.py create `
  --case-id clear-revision-comparison `
  --output .\artifacts\semantic-claims\clear.json
```

Then compute the profile:

```powershell
python .\tools\dataset_profile_artifact.py create `
  --semantic-claims .\artifacts\semantic-claims\clear.json `
  --output .\artifacts\dataset-profiles\clear.json
```

Verify it by complete deterministic reconstruction:

```powershell
python .\tools\dataset_profile_artifact.py verify `
  --semantic-claims .\artifacts\semantic-claims\clear.json `
  --artifact .\artifacts\dataset-profiles\clear.json
```

## Analyzer v0 rules

The analyzer derives:

- entity order from first subject occurrence;
- exact entity and fact counts;
- `repeatedRecordShape` when at least two entities have the same multiset of
  object shapes (`iri`, plain literal, language literal, or datatype literal);
- common predicates as the exact intersection, ordered by the first entity;
- at most one common supported `identifier` or `display_label` predicate as the
  row label;
- candidate dimensions only for repeated-record datasets and common non-row
  predicates with semantic claims;
- dimension eligibility only when every referenced claim is `supported`;
- technical predicates only from supported `policy_role/technical_metadata`
  claims;
- mandatory coverage as every canonical FactId in source order.

`repeatedRecordShape` is deliberately structural, not a claim of comparability.
For example, temperature, price, and age records can share the same object-shape
signature while still having no common predicates or semantic dimensions.

## Oracle boundary

The analyzer computes the profile without reading `oracleDatasetProfile`. Only after
computation does the research gate require exact equality with the frozen oracle
profile. A mismatch prevents artifact creation.

The artifact binds:

- benchmark manifest and case hashes;
- the exact Semantic Claims artifact hash;
- trusted analyzer identity and algorithm version;
- computed profile;
- frozen oracle-profile hash and exact-match result;
- a domain-separated artifact hash;
- canonical UTF-8 JSON bytes.

This stage does not select a UI component, calculate utility, normalize semantic
roles, or modify production runtime state.
