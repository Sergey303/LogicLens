# ADR-0013: Builder candidate promotion plan

- Status: Accepted
- Linear: ENG-87, child of ENG-26
- Depends on: ADR-0010, ADR-0012
- Scope: deterministic planning of an additive revision without applying it

## Context

ADR-0010 produces an isolated candidate artifact. ADR-0012 records a human
`recommend` decision bound to one exact passed run. Neither contract answers the
next operational questions: which revision is proposed, which files would be
added, what their exact bytes are, what identity the planned revision has, and
which baseline must be restored if a later apply step fails.

Those facts must be frozen before any tool receives permission to touch an
active package or pointer. Otherwise the apply step could silently select newer
candidate bytes, infer a different revision, or improvise a rollback target.

## Decision

### A promotion plan is a separate immutable artifact

`candidate-promotion-plan-v0` records:

- the exact reviewed recommendation and `reviewHash`;
- the candidate, candidate-package and baseline identities;
- source epoch and revision;
- the next additive revision number;
- every added rule, test and UI file with path, kind, size and SHA-256;
- empty modified and removed active-file sets;
- a baseline rollback target;
- a domain-separated planned-revision identity;
- a domain-separated `promotionPlanHash`;
- explicit `planned-only` and `not-performed` apply state.

The plan contains no machine path, temporary directory, command, credential,
active package location or pointer value.

### Only a recommended review is eligible

The planner validates `candidate-review-v0`, recomputes its `reviewHash`, and
requires:

- `decision = recommend`;
- all seven review checks to be exactly `true`;
- `activation.status = not-performed`.

A technically valid candidate that a human rejected cannot produce a promotion
plan.

### Candidate bytes are reverified

The candidate manifest file must have the hash pinned by the review. Its task,
baseline, candidate and candidate-package identities must match the reviewed
subject.

Every declared additive file is read from the isolated candidate package and
checked for:

- the reviewed `rules/`, `tests/` or `ui/` path vocabulary;
- absence of absolute paths, traversal, backslashes and symlinks;
- exact byte length;
- exact SHA-256.

The plan lists only those verified files in deterministic path order.

### Target revision and rollback are mechanical

Candidate v0 remains additive, so the target keeps the same epoch and increments
the baseline revision by one. The rollback target is the exact source epoch,
revision and baseline package hash.

`plannedRevisionHash` is not presented as an already-built active package hash.
It is a domain-separated identity over the reviewed recommendation, baseline,
candidate, target revision and exact added-file records. A later apply contract
must build the target package and prove how its actual package hash relates to
this plan.

### No apply capability

The planner has only `create` and `verify`. It does not copy candidate files,
write manifests, rename directories, update an active pointer or invoke a model.
The record always states:

```json
{
  "manifest": "planned-only",
  "activePointerUpdate": "not-performed",
  "apply": "not-performed"
}
```

A future apply contract must independently verify this plan, build into a new
location, run full checks, and perform an atomic pointer change with rollback.

## Verification

ENG-87 proves offline that:

1. a recommended review creates a deterministic next-revision plan;
2. exact added-file bytes and the rollback baseline are pinned;
3. candidate file tampering is rejected;
4. a human rejection cannot be promoted;
5. plan tampering and path traversal are rejected;
6. no provider or apply operation exists.

## Consequences

- review and deployment remain separate decisions;
- the later apply step receives no freedom to choose candidate bytes or rollback;
- planned revision identity is reproducible before any active state changes;
- the active epoch remains unchanged throughout planning;
- Qwen, Codex, fixtures and repaired provider-neutral candidates use one plan
  format after human recommendation.
