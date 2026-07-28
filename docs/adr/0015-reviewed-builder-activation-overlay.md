# ADR-0015: reviewed Builder activation overlay

- Status: Accepted
- Linear: ENG-98, child of ENG-26
- Depends on: ADR-0010, ADR-0012, ADR-0013, ADR-0014
- Scope: prepare a minimal trusted runtime integration artifact for one reviewed candidate

## Context

The real Qwen candidate passed candidate validation and the hidden oracle. A human
review record recommended that exact candidate, and a promotion plan proposed
revision 0.1. The activation-readiness assessment correctly blocked staging:
merely adding rule, test and UI files did not change the runtime revision, load
the candidate module or expose its exported predicate through the closed CLI.

A direct edit of the active epoch would collapse review, staging and activation
into one unsafe action. Copying a complete edited `cli_runtime.pl` would also
create a large trusted diff for one small derived predicate.

## Decision

### A two-file trusted overlay

`candidate-activation-overlay-v0` may contain exactly:

```text
entry.pl                         replace
rules/revision_runtime.pl        add
```

It may not replace `rules/cli_runtime.pl`, data, origins, ontology, smoke
requests, UI vocabulary or the active manifest. The existing reviewed runtime
remains the implementation for all baseline commands.

### Entry-selected revision wrapper

The replacement `entry.pl` selects `revision_runtime:handle_request/3`.
`revision_runtime.pl`:

- declares the planned epoch and revision;
- imports the unchanged baseline `cli_runtime.pl`;
- imports the single reviewed candidate rule;
- delegates existing commands after translating the request to the baseline
  revision and rewrites only the response epoch/revision envelope;
- preserves the baseline health result and appends `derived-query` to its
  available command list;
- exposes one exact predicate IRI through one exact command;
- rejects stale state, malformed derived requests and unknown predicates;
- limits the derived result to 1000 deterministic sorted rows.

The overlay generator derives the module, exported predicate and UI predicate
IRI from the already reviewed candidate bytes. Provider output cannot choose an
arbitrary handler, command, path or Prolog goal.

### Readiness follows the real entry handler

A runtime tree may contain the unchanged baseline `cli_runtime.pl` with revision
0 while `entry.pl` selects a reviewed revision wrapper with revision 1. The
readiness assessor therefore reads epoch/revision from the one module whose
`handle_request/3` is actually selected by `entry.pl`. It rejects missing,
ambiguous or non-exported handlers.

This avoids both false readiness from unrelated files and false blocking from a
retained delegated baseline module.

### Overlay identity

`overlayHash` is SHA-256 over a versioned domain, the canonical overlay manifest
without `overlayHash`, and the ordered paths and bytes of both overlay files.
The manifest pins:

- readiness assessment and its hash;
- promotion plan hash;
- candidate, candidate-package and baseline hashes;
- target epoch/revision;
- reviewed derived command, predicate IRI, module and arity;
- exact file operations, sizes and hashes;
- an explicit `not-performed` staging/apply/pointer intent.

### No staging or activation

The builder has only `create` and `verify`. It writes only to a new output
directory outside the candidate package. It does not copy the overlay into a
candidate or active package and does not create or update an active manifest or
pointer.

A later staged-revision builder must combine baseline, candidate and this exact
overlay in a separate directory, rerun runtime and readiness verification, and
produce a new immutable staged manifest before any activation can be discussed.

## Verification

ENG-98 proves that:

1. the known three-blocker assessment produces byte-identical overlay builds;
2. any other blocker set is rejected;
3. the overlay contains only the two allowlisted files;
4. baseline health delegates unchanged while the envelope reports revision 1;
5. `derived-query` returns the reviewed entity and evidence facts;
6. revision 0 requests receive `stale_state`;
7. unknown predicate IRIs are rejected;
8. the entry-selected readiness assessment becomes `ready` in an isolated copy;
9. overlay tampering is detected;
10. active files and pointers remain untouched.

## Consequences

- the candidate can progress toward an honest functional staged revision;
- the large baseline CLI remains reviewed and unchanged;
- one generic wrapper pattern can support later reviewed arity-2 derived
  predicates, subject to a new overlay record for each binding;
- the overlay is necessary evidence for staging, but still grants no activation
  authority.
