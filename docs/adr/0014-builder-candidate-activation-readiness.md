# ADR-0014: Builder candidate activation readiness

- Status: Accepted
- Linear: ENG-95, blocks ENG-89
- Depends on: ADR-0010, ADR-0012, ADR-0013
- Scope: prove that a reviewed additive candidate can become a functional runtime revision before staging

## Context

The first real Qwen candidate passed candidate validation, hidden-oracle validation,
human review and promotion planning. The resulting plan correctly pins three
additive files and proposes revision `0.1`.

That evidence is necessary but not sufficient for activation. The current active
runtime still declares `loaded_revision(0)`, `entry.pl` does not import the
candidate rule module, and the closed CLI protocol has no invocation path for
`researcher_at_iis/2`. Copying the three files into a package would therefore
produce a package that contains the feature but cannot load or expose it.

Calling that package revision `0.1` would create false confidence and move the
problem across the activation boundary.

## Decision

### Readiness is a separate machine-verifiable record

`candidate-activation-readiness-v0` assesses:

1. the promotion plan schema and `promotionPlanHash`;
2. the exact candidate manifest and candidate file bytes;
3. the exact active baseline package hash;
4. the epoch and revision declared by the proposed runtime tree;
5. a trusted `use_module` load path for every candidate rule module;
6. a reviewed invocation path for every exported candidate predicate.

The record is canonical and domain-hashed. It has one of two statuses:

- `ready`: every check is true and the blocker list is empty;
- `blocked`: at least one readiness check is false and every failure has a
  stable code, explanation and remediation.

A blocked assessment is a successful assessment result, not an infrastructure
failure.

### Runtime tree is an input, never an output

The assessor receives both:

- the immutable active baseline used by the promotion plan;
- a proposed runtime tree to inspect.

For the current candidate, the proposed runtime tree is the already validated
candidate package. It proves that additive files alone are dormant. A future
reviewed activation-overlay contract may build another proposed runtime tree and
submit it to the same assessor.

### Three functional checks are mandatory

#### Target revision represented

The proposed runtime must declare the exact target epoch and revision. A package
that advertises revision `0.1` in planning metadata while the runtime still
accepts only revision `0.0` is blocked.

#### Candidate rule loaded

A trusted runtime source outside the untrusted candidate module and its tests
must import every candidate rule module. Candidate tests importing their own
module do not count as activation.

#### Candidate predicate exposed

Every exported candidate predicate must have an invocation path in trusted
runtime source. Merely loading a module is not enough when no closed command,
registry or reviewed rule can call it.

These checks intentionally establish a lower bound. Future contracts may add a
stronger semantic registry, UI projection and authorization proof.

### No staging or activation capability

The assessor has only `assess` and `verify` commands. It does not copy files,
write manifests, update pointers, invoke providers or apply promotion plans.
Every assessment records:

```json
{
  "staging": "not-performed",
  "apply": "not-performed",
  "activePointerUpdate": "not-performed"
}
```

## Current expected verdict

`eng-87-plan-001` must be blocked by at least:

- `runtime_revision_not_represented`;
- `candidate_rule_not_loaded`;
- `candidate_predicate_not_exposed`.

This does not invalidate the candidate or the promotion plan. It proves that a
reviewed activation overlay is still required before ENG-89 can stage revision
`0.1`.

## Verification

ENG-95 proves offline that:

1. dormant additive files are blocked with exact remediation;
2. an artificial revision-aware runtime that loads and invokes the candidate is
   marked ready;
3. plan, baseline and candidate bytes are independently verified;
4. assessment and plan tampering are rejected;
5. no provider, staging, apply or pointer-switch path exists.

## Consequences

- a valid candidate can no longer become a misleading no-op revision;
- staging waits for an explicit reviewed integration design;
- the same readiness gate can verify a future activation overlay;
- the active epoch remains unchanged while the missing runtime contract is
  designed and tested.
