# ADR-0016: warning-free Builder activation overlay import

- Status: Accepted
- Linear: ENG-104
- Depends on: ADR-0015

## Context

The real `eng-98-overlay-002` run proved that the reviewed activation overlay
turns the candidate runtime from `blocked` into `ready` without staging or
activating it. SWI-Prolog nevertheless reported that the local
`revision_runtime:handle_request/3` definition overrides a weak import from
`cli_runtime`.

The wrapper intentionally defines its own `handle_request/3` and delegates
baseline commands through qualified calls to `cli_runtime:handle_request/3`.
Importing the baseline module's exports is therefore unnecessary and produces
avoidable noise in every runtime invocation.

## Decision

A compatibility renderer loads the baseline module using an explicit empty
import list:

```prolog
:- use_module('cli_runtime.pl', []).
```

All baseline calls remain module-qualified. The compatibility renderer changes
only this one directive in the already reviewed overlay output; the entry
point, derived registry, stale-state handling, candidate binding and hashing
logic remain unchanged.

CI runs both the full activation-overlay contract and a focused SWI-Prolog load
test through the compatibility renderer. The focused test fails if stderr
contains `overrides weak import from cli_runtime`.

The pre-existing `subgraph.pl` singleton-variable warning is outside this ADR.
It occurs in the baseline runtime and is not introduced by the activation
overlay.

## Consequences

- the reviewed wrapper no longer shadows an imported predicate;
- qualified delegation to the baseline runtime is explicit;
- generated overlay bytes and overlay hashes change and require a fresh real
  artifact;
- no active package, staged package or active pointer is modified.
