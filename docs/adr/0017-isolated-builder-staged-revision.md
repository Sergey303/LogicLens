# ADR-0017: isolated Builder staged revision

- Status: Accepted
- Linear: ENG-89, child of ENG-26
- Depends on: ADR-0010, ADR-0012, ADR-0015, ADR-0016
- Scope: materialize a reviewed revision without activating it

## Context

A valid candidate, human recommendation and promotion plan are not yet a runnable
revision. ENG-95 proved that copying only the three candidate files creates a
formal revision whose runtime still reports 0.0 and does not expose the derived
predicate. ENG-98 and ENG-104 added a reviewed warning-free overlay that changes
only `entry.pl` and adds `rules/revision_runtime.pl` in an isolated preview.

The next artifact must combine the exact active baseline, the three reviewed
candidate files and the two allowlisted overlay files into one reproducible
package. It must remain separate from the active package and active pointer.

## Decision

### `staged-revision-v0`

A staged revision is a complete runnable package with its own `manifest.json`.
The manifest binds the package to:

- the exact promotion plan and planned revision hash;
- the blocker-free ready assessment;
- the warning-free overlay;
- the candidate and candidate-package hashes;
- the exact baseline package and rollback revision.

The staged package is built from baseline files excluding the old active
manifest. The three candidate files are added. The overlay replaces `entry.pl`
and adds `rules/revision_runtime.pl`. No other replacement or addition is
allowed.

### Independent package identity

The staged package uses the domain-separated hash
`LogicLensStagedRevision\0`, version 1, over every package file except its own
manifest. The manifest stores each file hash and the aggregate package hash.
Verification reconstructs the expected package from all reviewed inputs and
requires byte equality.

### Validation before manifest publication

Before `manifest.json` is written, the builder repeats:

1. plan, readiness, overlay, candidate and baseline identity checks;
2. candidate UTF-8, dangerous-call and UI vocabulary checks;
3. SWI-Prolog rule loading;
4. PlUnit execution;
5. all portable baseline smoke requests with revision-envelope normalization;
6. health 0.1, derived-query, stale-state and unknown-predicate checks;
7. absence of the overlay weak-import warning;
8. byte equality of the active package before and after staging.

The pre-existing `subgraph.pl` singleton-variable warning is not introduced by
staging and is outside this ADR.

### Staging is not activation

The CLI has only `create` and `verify`. It writes solely to a fresh output tree.
Its manifest records:

```json
{
  "staging": "isolated-output-only",
  "apply": "not-performed",
  "activePointerUpdate": "not-performed"
}
```

A future activation contract must independently verify the staged package and
perform an atomic pointer update with rollback. This ADR provides no such
operation.

## Consequences

- revision 0.1 can now be reviewed as one complete runnable artifact;
- candidate and trusted integration code cannot drift independently;
- rollback remains pinned to active revision 0.0;
- staging failures cannot modify the active package;
- activation remains a separate explicit decision and implementation.
