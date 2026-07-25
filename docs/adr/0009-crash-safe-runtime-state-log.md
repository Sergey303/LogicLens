# ADR-0009: crash-safe runtime state log

- Status: Proposed
- Linear: ENG-24
- Scope: runtime `ApplyDelta` persistence and recovery

## Context

ADR-0001 requires four externally visible properties at the same time:

1. a state-changing delta changes the graph and revision exactly once;
2. a no-op command keeps the revision unchanged but still receives an idempotency receipt;
3. retrying the same `CommandId` returns the original result;
4. a failed command changes neither graph, journal, receipts nor revision.

Persisting a graph change and its receipt in separate files creates an unsafe crash window. A process can durably write one and fail before writing the other. On restart the server could then either lose an accepted change or apply a retry twice.

## Decision

### One append-only commit stream

The v0 runtime store uses one append-only file:

```text
runtime-state.llog
```

Each committed frame contains one accepted command receipt. A state-changing receipt additionally contains the actual normalized add/delete operations and the before/after revision. No-op receipts contain empty operation arrays and the same before/after revision.

The conceptual state-change journal and accepted-command receipt index are reconstructed from the same committed records:

```text
all frames                 -> receipts by CommandId
frames with actual changes -> ordered state-change journal
```

This deliberately avoids a transaction across separate journal, revision and receipt files.

### Frame format

Each frame is:

```text
magic
format version
payload length
UTF-8 JSON payload
SHA-256(payload)
commit marker
```

The JSON property order, fact order, delete order, timestamp format and fact-object representation are deterministic.

A frame is accepted only after the complete frame, including the commit marker, has been written and `Flush(true)` succeeds. The in-memory graph, revision and receipt index are updated only after that durable append returns.

### Recovery

Startup begins from a supplied immutable snapshot identified by `SnapshotId` and `BaseRevision`, then scans the log in order.

- A frame whose commit marker and payload are incomplete is an uncommitted tail. Recovery truncates the file to the last complete frame.
- A complete frame with an invalid checksum, invalid JSON contract, broken revision chain, duplicate `CommandId`, impossible add/delete operation or different `SnapshotId` is corruption. Startup fails instead of silently dropping it.
- A crash after durable append but before the caller receives a response is recovered as an accepted command. Retrying the same `CommandId` returns the reconstructed receipt.

### ApplyDelta order

For a new command:

1. normalize and hash the request;
2. return the old result for an exact `CommandId` retry;
3. reject reuse of a `CommandId` with another request hash;
4. compare `ExpectedRevision` with current revision;
5. compute actual state changes on the current graph;
6. build one receipt/change record;
7. append and durably flush one complete frame;
8. apply that record to in-memory state;
9. return the recorded result.

If writing throws before durable completion, the current store instance becomes faulted and must be reopened. Recovery removes any incomplete tail.

### Delta normalization

- add operations are canonicalized through `CanonicalFact` and sorted by `FactId`;
- duplicate adds and deletes are deduplicated;
- operation order does not change request identity;
- adding an already active fact is a no-op;
- deleting an absent fact at the current revision is a no-op;
- delete plus add of the same already active FactId preserves the existing fact and origins;
- an actual replacement is one delete and one different add, producing one revision increment.

The request hash includes the expected revision and actor, but not server acceptance time.

### Provenance

A newly added fact receives one edit origin containing:

```text
OriginId = edit:<CommandId>:<FactId>
Actor
CommandId
accepted UTC timestamp
```

Re-adding the same canonical triple restores the same `FactId` with a new edit origin. Existing archival origins are not modified by no-op adds.

### Concurrency boundary

One process owns a runtime state log for writing. The store keeps an exclusive writer handle for its lifetime. Multiple-process coordination and distributed consensus are outside v0.

## Verification

ENG-24 must prove on Windows and Linux:

- add and replacement revision semantics;
- exact retry after later revisions;
- conflicting `CommandId` rejection;
- no-op receipt persistence without revision change;
- stale revision rejection without appended bytes or receipt;
- replay equivalence from snapshot plus log;
- stable FactId on delete and re-add;
- truncated frame recovery;
- recovery of a frame durably written before a simulated process crash;
- rejection of checksum corruption and snapshot mismatch;
- one-writer enforcement;
- byte-identical logs for the same snapshot, normalized commands and clock.

## Consequences

- Receipt and state-change durability share one commit point.
- Runtime startup is linear in the number of frames until a later checkpoint/compaction milestone is justified.
- The log is not a general event-sourcing API and is not exposed to React.
- The HTTP editing endpoint and synchronization with the running SWI graph are separate follow-up work after this storage contract is proven.
