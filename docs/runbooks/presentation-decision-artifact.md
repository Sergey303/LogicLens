# Presentation Decision artifact v0

Status: research-only oracle-planner gate.

This stage consumes two already verified inputs for one frozen benchmark case:

```text
Semantic Claims artifact v0
Deterministic Dataset Profile artifact v0
        ↓
Presentation Decision artifact v0
```

It does not compile a UI Document, add a React component, or claim that
`comparison_table` exists in the production UI contract. The component name is a
research candidate whose usefulness and rejection behavior are being tested before a
contract change is proposed.

## Trusted planner boundary

`tools/presentation_decision_artifact.py` computes the decision without reading the
case's `expectedPresentation` field. Only after computation does it require an exact
match with that frozen oracle field.

The planner evaluates these hard constraints in a fixed order:

1. at least two entities exist;
2. a repeated record shape exists;
3. the task requests comparison;
4. at least one supported shared semantic dimension exists;
5. a supported row label exists;
6. every selected dimension is supported;
7. a generic fallback is attached;
8. primary and fallback-only facts cover every mandatory FactId.

Failure precedence is explicit:

- too few entities or no repeated shape → `repeated_records_required`;
- a non-comparison task → `comparison_task_required`;
- no supported shared dimensions → `insufficient_shared_semantic_dimensions`;
- shared dimensions without a row label fail closed as an invalid planner input.

An ambiguous time-like dimension is excluded from the comparison table and remains in
the generic fallback. When competing `possible` claims include `time_value` and another
`*_time` role, the planner records `ambiguous_time_semantics` and rejects a timeline
candidate for the same reason. Role strings remain exact fixture-local labels; the
planner does not normalize them.

## Artifact contents

The canonical JSON artifact records:

- frozen benchmark and case hashes;
- exact Semantic Claims and Dataset Profile artifact hashes;
- trusted planner identity and algorithm version;
- every evaluated hard constraint;
- selected or rejected outcome and reason;
- mandatory, primary, and fallback-only FactIds;
- the complete presentation decision;
- exact oracle comparison;
- a domain-separated artifact hash.

## Run locally

```bash
python tools/semantic_claims_artifact.py create \
  --case-id ambiguous-time-excluded \
  --output /tmp/claims.json

python tools/dataset_profile_artifact.py create \
  --semantic-claims /tmp/claims.json \
  --output /tmp/profile.json

python tools/presentation_decision_artifact.py create \
  --semantic-claims /tmp/claims.json \
  --dataset-profile /tmp/profile.json \
  --output /tmp/decision.json

python tools/presentation_decision_artifact.py verify \
  --semantic-claims /tmp/claims.json \
  --dataset-profile /tmp/profile.json \
  --artifact /tmp/decision.json
```

The verifier reconstructs the artifact from the frozen case and both verified inputs.
Altered decisions, changed coverage, stale hashes, noncanonical JSON, or mismatched
inputs are rejected.
