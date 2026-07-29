# ADR-0019: Atomic Builder activation uses immutable packages and a durable pointer

- Status: Accepted
- Linear: ENG-107
- Depends on: ADR-0008, ADR-0017, ADR-0018
- Scope: first real activation transaction from revision 0.0 to revision 0.1

## Context

Revision `0.1` has a verified staged package and an immutable `authorize` decision.
Neither artifact changes the active runtime. The original portable-package design also
has no active pointer: a directory is active only by convention. Replacing that
directory in place would create a period in which readers could observe a partial
copy and would make rollback depend on reconstructing overwritten files.

The transaction must therefore distinguish three things:

1. immutable package bytes;
2. the small record that selects one package;
3. the durable journal that explains an interrupted pointer change.

## Decision

### 1. Deployment layout

A deployment root has this layout:

```text
current.json
.activation.lock
packages/
  e000000-r000000-<full-package-sha256>/
  e000000-r000001-<full-package-sha256>/
transactions/
  <transaction-id>.journal.json
  <transaction-id>.attestation.json
```

Package directory names are content addressed. Existing package directories are
verified and reused, never overwritten. Revision `0.0` and revision `0.1` therefore
remain available simultaneously.

### 2. `current.json` is the only mutable activation record

`active-pointer-v0` pins:

- monotonic generation;
- epoch and revision;
- package hash and relative package path;
- activation decision hash;
- transaction ID;
- a domain-separated `pointerHash`.

The package path must name exactly one child of `packages/`. Absolute paths,
traversal and symlinks are rejected.

### 3. Initialization is explicit

`initialize` imports the exact active `0.0` portable package into the content-addressed
store, verifies its active manifest and creates generation `0` of `current.json`.
It refuses a non-empty or already initialized deployment root.

### 4. Activation is compare-and-swap

Immediately before mutation, `activate`:

1. acquires an exclusive local lock;
2. recovers or refuses every unfinished older transaction;
3. verifies `activation-decision-v0` and `decisionHash` again;
4. verifies the current pointer and exact current package;
5. requires the pointer to equal `expectedCurrent`;
6. verifies and installs the exact staged package in its immutable final path;
7. runs the complete pre-switch staged runtime gate;
8. writes a durable `prepared` journal;
9. rereads `current.json` and requires byte-equivalent pointer state;
10. atomically replaces `current.json` with generation + 1.

The pointer replacement uses a temporary file on the same filesystem. The file is
flushed before the move. POSIX uses `os.replace` followed by parent-directory
`fsync`; Windows uses `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING` and
`MOVEFILE_WRITE_THROUGH`.

### 5. Commit requires a control run through the selected pointer

After the swap, the transaction resolves the package again from `current.json` and
reruns:

- baseline smoke comparison;
- health at revision `0.1`;
- `derived-query`;
- stale-state rejection;
- unknown-predicate rejection.

Only after all checks pass is the journal changed to `committed` and a deterministic
attestation written. Merely changing the pointer is not a successful activation.

### 6. Handled failures roll back before returning

Any caught error after journal creation moves the journal to `rolling-back`, restores
the exact previous pointer atomically, verifies the previous package and runs its
health request. A successful rollback produces `rolled-back` journal and attestation
and the activation command returns a failure status.

A failure before the pointer swap records that no pointer update occurred. A failure
after the swap records both the attempted update and the verified restoration.

### 7. Process and power interruption are recovered fail-closed

A process can disappear between the atomic pointer swap and the control run, so no
ordinary exception handler can literally execute at that moment. The durable journal
covers this case.

`recover` and every later `activate` inspect nonterminal journals while holding the
same exclusive lock. If `current.json` names the target, recovery atomically restores
the previous pointer. If it already names the previous package, recovery verifies it
without another write. Any third pointer state is refused. Recovery then verifies the
rollback runtime and emits a rollback attestation.

A stale lock is removed automatically only when it was created on the same host and
its recorded PID is no longer alive. An unrecognizable or live lock is never broken.

This provides deterministic recovery from handled errors and interrupted local
processes. It cannot promise success if the storage device itself loses acknowledged
writes or becomes unavailable; such failures remain visible as a nonterminal or
`rollback-failed` journal and block further activation.

### 8. Attestations are tamper evident

The committed or rolled-back attestation pins:

- before and after pointers;
- decision, target and rollback hashes;
- all transaction checks;
- the final journal hash;
- whether apply was performed, rolled back or never reached;
- whether recovery was required;
- a domain-separated `transactionHash`.

## Rejected alternatives

### Replace the active package directory in place

Rejected because readers can observe a partial tree and rollback requires restoring
many files rather than one pointer.

### Rename the old directory away and the new directory into its name

Rejected because two directory operations still expose an intermediate state and make
the directory name carry identity that already belongs in the manifest and pointer.

### Delete revision 0.0 after a successful smoke test

Rejected because rollback must remain an immediate pointer operation and because the
reviewed decision explicitly pins the old package.

### Continue activation automatically after crash recovery

Rejected. A recovered activation returns to the reviewed old state and requires an
explicit fresh invocation, preventing an operator from missing that recovery occurred.

## Consequences

- revision `0.1` can be installed without rewriting revision `0.0`;
- the active change is one compare-and-swap pointer operation;
- handled failures restore and verify `0.0` before returning;
- interrupted processes are recovered from the durable journal;
- stale decisions and concurrent activations fail before mutation;
- future revisions must teach the authorization layer to accept a pointer-selected
  staged-revision package as the current baseline, because revision `0.1` deliberately
  retains its immutable staged manifest rather than rewriting package bytes after
  activation.
