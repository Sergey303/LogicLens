# ADR-0018: Authorization is separate from activation

- Status: Accepted
- Linear: ENG-106
- Depends on: ADR-0008, ADR-0017
- Scope: reviewed authorization for a staged Builder revision

## Context

Revision `0.1` can now exist as an isolated, runnable staged package. The staged
package proves that the selected Qwen rule, its test, UI binding, trusted wrapper,
baseline behavior, and rollback binding are mutually consistent.

That proof is still not permission to mutate an active location. Combining
verification and activation in one command would make it difficult to tell
whether a failure occurred before or after the active pointer changed. It would
also make an old decision reusable after either the staged package or the current
active package changed.

## Decision

### 1. Authorization is a separate immutable record

`activation-decision-v0` records one decision:

```text
authorize expected-current 0.0 -> staged target 0.1
```

The record pins:

- the exact staged package hash;
- promotion-plan and planned-revision hashes;
- ready assessment, overlay, candidate, and baseline hashes;
- the current active epoch, revision, and package hash;
- the target epoch, revision, and package hash;
- rollback to the exact current package;
- SHA-256 of the staged, active, candidate, and overlay manifests.

### 2. Authorization reruns verification

Before producing `authorize`, the tool:

1. validates the staged manifest schema;
2. recomputes all staged per-file hashes and the staged package hash;
3. verifies the current active package manifest and package hash;
4. requires the target to be exactly the next revision of the current epoch;
5. requires rollback to equal the current active state;
6. re-runs Prolog load, PlUnit, baseline smoke comparison, health, derived-query,
   stale-state, and unknown-predicate checks;
7. confirms that the active package is byte-identical before and after.

### 3. The decision is deterministic and tamper-evident

`decisionHash` uses:

```text
domain  = LogicLensActivationDecision\0
version = 1
payload = canonical JSON without decisionHash
```

The same reviewed inputs and decision ID produce byte-identical JSON.

### 4. The command cannot activate

The supported operations are only:

```text
create
verify
```

The tool does not copy a package into an active location, rename directories,
write a pointer, apply a revision, or switch traffic.

### 5. Future activation must consume this exact decision

A later activation transaction must verify the decision again immediately before
changing any pointer. It must fail if:

- current active package no longer equals `expectedCurrent`;
- staged package no longer equals `target`;
- rollback package is unavailable;
- `decisionHash` differs;
- any runtime gate fails.

## Rejected alternatives

### Activate directly from the staged package

Rejected because a valid package does not identify which current active state was
reviewed or whether that state changed after staging.

### Put an `approved` flag into the staged manifest

Rejected because the staged manifest describes package construction, not a
human-reviewed transition from one active state to another.

### Let the activation command create its own authorization

Rejected because verification and mutation would again share one failure domain.

## Consequences

- authorization can be reviewed, archived, and reproduced independently;
- stale authorization is detectable before any mutation;
- rollback is part of the decision rather than an operational afterthought;
- the next implementation can focus only on an atomic, compare-and-swap style
  activation transaction.
