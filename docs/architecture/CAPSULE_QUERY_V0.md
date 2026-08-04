# Capsule Query v0

Status: implemented strict-claim runtime contract  
Runtime: Python 3.12 + SWI-Prolog  
Input boundary: verified LogicLens capsule package + JSON request  
Output boundary: closed JSON decision frame

## Purpose

`tools/capsule_query.py` is the universal read-only query boundary for the strict assertion subset currently compiled by LogicLens capsules.

It does not query mutable authoring JSONL directly. The tool first verifies the immutable capsule package, validates the typed request against the packaged semantic model, executes the generated assertions in SWI-Prolog, cross-checks the result against packaged assertion metadata, and emits one schema-validated JSON result.

The v0 boundary supports only:

- predicates whose `valueSpace` is `strict_claim`;
- open-world semantics;
- explicit negative evidence;
- statuses `supported`, `refuted`, `unknown`, and `conflicting`.

Measurements, probability distributions, fuzzy membership and numerical decision policies remain outside this runtime contract.

## Request

```json
{
  "schemaVersion": "0.1",
  "operation": "strict-claim",
  "target": {
    "predicate": "owns_outcome",
    "arguments": [
      "role.product_owner",
      "outcome.product_value"
    ]
  }
}
```

The request is checked against `contracts/capsule-query-v0.schema.json` and the semantic files embedded in the package:

- predicate existence;
- value space;
- arity;
- argument types;
- declared semantic identifiers.

Unknown predicates, undeclared role/outcome IDs, closed-world predicates and implicit-negation predicates are rejected.

## Command

```powershell
py -3 tools\capsule_query.py `
  --package <compiled-capsule-package> `
  --request query.json `
  --swipl swipl `
  --pretty
```

Use `--request -` to read one JSON object from stdin. Without `--output`, successful JSON is written to stdout. Failures use a non-zero exit code and write a structured JSON error to stderr.

## Result

The result binds the request to:

- world, capsule and package hashes;
- the declared predicate signature;
- strict status and recommended action;
- supporting and opposing assertion IDs;
- provenance and source summaries;
- scope and generalisability;
- dependency groups and warnings;
- an explicit SWI-Prolog verification marker.

## Execution contract

1. Verify `capsule-package.json`, `capsule.lock.json`, every file hash and the exact packaged file set.
2. Validate the request JSON Schema.
3. Resolve the predicate from packaged semantic declarations.
4. Validate arity and every argument against packaged semantic IDs.
5. Load packaged prepared assertions and source metadata.
6. Execute the target against `files/generated/assertions.pl` in a short-lived SWI-Prolog process.
7. Independently derive the evidence set from packaged JSONL and require exact agreement with SWI-Prolog.
8. Emit a schema-validated deterministic JSON result.

No shell command, network request, mutable Prolog database operation or authoring-file lookup is allowed in the query path.

## Strict statuses

| Evidence | Status | Action |
|---|---|---|
| support only | `supported` | `answer_with_source_scope` |
| oppose only | `refuted` | `explain_explicit_role_boundary` |
| neither | `unknown` | `abstain_and_request_context` |
| both | `conflicting` | `report_conflict_and_compare_models` |

`unknown` never means false. A context-dependent or local assertion is returned with an explicit warning.

## Trust boundary

The result verifies what the loaded capsule supports. It does not prove that an LLM correctly extracted a target from free-form user text. A future Markdown evaluator must bind every extracted target to an exact quote from the learner answer before calling this query boundary.
