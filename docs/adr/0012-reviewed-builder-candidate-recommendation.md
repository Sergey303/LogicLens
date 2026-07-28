# ADR-0012: reviewed Builder candidate recommendation

- Status: Accepted
- Linear: ENG-86, child of ENG-26
- Depends on: ADR-0010, ADR-0011
- Scope: explicit human recommendation of a technically passed Builder candidate

## Context

ADR-0010 deliberately stops at an isolated candidate artifact. A candidate may
load, pass its tests, preserve stable runtime outputs and pass the hidden oracle,
but none of those checks authorizes changing the active epoch. The first real
Qwen-only pass, `eng-80-qwen-001`, demonstrates that this boundary is now
practical rather than hypothetical.

The next decision must be attributable to a human reviewer and pinned to the
exact run, comparison report, candidate manifest and baseline package. A prose
comment is not sufficient because copied hashes can drift, inputs can be mixed
between runs, and a later activation process needs one machine-verifiable
selection record.

## Decision

### One provider-neutral review record

`contracts/candidate-review-v0.schema.json` defines a canonical JSON record with:

- a stable review ID;
- an explicit human decision: `recommend` or `reject`;
- reviewer identity and substantive reason;
- exact run, task, provider, baseline, proposal and candidate hashes;
- measured provider metrics copied from the run envelope;
- SHA-256 hashes of the three reviewed input files;
- the required technical checks;
- an explicit `activation.status = "not-performed"`;
- a domain-separated `reviewHash`.

The record contains no source paths, temporary directories, credentials,
provider prompt, hidden-oracle content or activation command.

### Recommendation requires one consistent passed run

Before either human decision is recorded, the offline verifier requires:

1. the run envelope to satisfy `builder-run-v0`;
2. run, comparison and candidate identities to agree;
3. provider identity and metrics to agree;
4. candidate and candidate-package hashes to agree;
5. the comparison file hash to match the hash pinned by the run;
6. baseline package, epoch and revision to agree;
7. candidate and hidden-oracle validation to be `passed`;
8. exactly the nine reviewed comparison validations to be present once and pass;
9. baseline and candidate stable runtime outputs to be byte-identical;
10. no active file to be modified or removed.

A human may still choose `reject` after all technical checks pass. This preserves
the distinction between technical eligibility and product or research
selection.

### Review hash excludes only itself

`reviewHash` is SHA-256 over a versioned domain and the canonical record with the
`reviewHash` field removed. Verification recomputes both the record from the
three source files and its review hash. Editing the reason, reviewer, decision
or any pinned identity invalidates the record.

### No activation capability

The tool has only `create` and `verify` commands. It cannot write into an active
package, change an epoch pointer, copy candidate files into reviewed source
directories or invoke a provider.

Atomic activation remains a separate future contract with stronger rollback,
pointer update and deployment checks. A `recommend` record is necessary
evidence for that future step, not permission to perform it.

## Verification

ENG-86 proves offline that:

1. a passed run creates a canonical recommendation;
2. all run, candidate and evidence hashes are pinned;
3. a human rejection can be recorded for a technically valid candidate;
4. active-file changes are rejected;
5. mixed candidate identities are rejected;
6. record tampering is detected;
7. no provider invocation or activation behavior exists.

## Consequences

- successful Qwen, Codex, fixture or repaired provider-neutral runs can be
  reviewed through the same contract;
- human judgment becomes explicit and auditable;
- a later activation tool can require one exact reviewed recommendation;
- passing tests or hidden oracle no longer risks becoming accidental
  self-activation;
- active epoch contents remain unchanged by review.
