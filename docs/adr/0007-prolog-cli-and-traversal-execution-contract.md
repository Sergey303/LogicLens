# ADR-0007: Prolog CLI and traversal execution contract

- Status: Proposed
- Linear: ENG-38
- Depends on: ADR-0002, ADR-0004, ADR-0005, ADR-0006
- Scope: zero-epoch traversal and the stable process boundary used by C#, Builder, Search and manual experiments

## Context

ENG-38 needs one bounded way to execute the reviewed SWI-Prolog epoch. The original command shape passed a command and JSON options as command-line arguments:

```text
swipl -q -s epochs/epoch-000/entry.pl -- <command> <json-options>
```

That is simple, but it makes correctness depend on Windows/PowerShell/Bash quoting, command-line length and locale behavior. It also leaves error serialization, hard limits, repeated-path identity and deterministic JSON underspecified.

The first implementation remains a short-lived process. A long-lived worker may replace it later without changing the logical request/response contract.

## Decision

### 1. JSON travels through stdin/stdout, not command-line arguments

Invocation:

```text
swipl -q -s epochs/epoch-000/entry.pl --
```

The caller writes exactly one UTF-8 JSON request to stdin and closes stdin. SWI-Prolog writes exactly one UTF-8 JSON response to stdout and exits.

Command-line arguments may select only reviewed operational modes such as a future `--version`. Entity identifiers, directions, limits, predicates, paths and query text are never interpreted as shell arguments.

### 2. Stable request envelope

```json
{
  "protocolVersion": "0.1",
  "requestId": "01J2...",
  "command": "subgraph",
  "epoch": 0,
  "revision": 0,
  "options": {}
}
```

Required fields:

- `protocolVersion` — exact supported protocol version;
- `requestId` — opaque caller-generated correlation identifier, returned unchanged;
- `command` — one value from the closed command set;
- `epoch` and `revision` — the state the caller expects;
- `options` — a command-specific object validated before execution.

Commands in v0:

```text
health
inspect-facts
entity-view
subgraph
```

There is no generic `query`, `consult`, module name, predicate name, file path or Prolog source option in v0.

### 3. Stable response envelope for success and expected failure

Successful response:

```json
{
  "protocolVersion": "0.1",
  "requestId": "01J2...",
  "status": "ok",
  "epoch": 0,
  "revision": 0,
  "result": {},
  "diagnostics": []
}
```

Expected command error:

```json
{
  "protocolVersion": "0.1",
  "requestId": "01J2...",
  "status": "error",
  "epoch": 0,
  "revision": 0,
  "error": {
    "code": "invalid_request",
    "message": "depth must be between 0 and 2",
    "details": {}
  },
  "diagnostics": []
}
```

For every request that reaches the reviewed command loop, stdout contains one response envelope even when the command fails. The process exits:

- `0` for `status = ok`;
- non-zero for `status = error`.

Stderr is reserved for process/bootstrap diagnostics that cannot be represented by the protocol. Callers must not parse ordinary results from stderr.

A syntax error before the command loop, missing epoch files or a broken SWI runtime may terminate without a valid response envelope; the caller classifies that as a process failure rather than a command error.

### 4. Requested limits and hard limits are different

The request may lower limits but may never raise reviewed hard limits.

```text
effectiveLimit = min(requestedLimit, configuredHardLimit)
```

Hard limits cover at least:

- traversal depth;
- node count;
- fact count;
- occurrence count;
- path length;
- output byte count;
- execution time.

The effective limits and any truncation are returned in diagnostics. Missing requested limits use reviewed defaults, not infinity.

The process is additionally bounded by the caller with an external timeout and kill policy. SWI-Prolog uses an internal time limit where practical. Both layers are required because one cannot safely substitute for the other.

### 5. Precise depth semantics

Depth is defined by expansion layers, not merely by which nodes appear.

- depth `0`: return the root node only; do not expand incident facts;
- depth `1`: expand all selected incident facts of the root and include nodes reached through eligible IRI edges;
- depth `2`: include depth-1 results and expand selected incident facts of depth-1 occurrences; facts already selected at a lower layer are not duplicated;
- later depths, if introduced, follow the same rule.

All selected incident facts remain visible even when an IRI fact is not traversal-eligible under ADR-0004. Edge eligibility controls expansion only.

### 6. Direction is relative to the current occurrence

For each traversal step:

```text
outgoing: current node is the fact subject; next node is the IRI object
incoming: current node is the IRI object; next node is the fact subject
```

The original canonical fact is never reversed. An occurrence step records:

```json
{
  "factId": "f:sha256:...",
  "direction": "incoming",
  "from": "organization:isi",
  "to": "person:1"
}
```

This allows UI and proof code to recover the original source triple without inventing a reversed fact.

### 7. Deterministic occurrence identity

Graph nodes and facts are unique, but occurrences are path-sensitive.

`OccurrenceId` is derived from:

```text
root entity
+ ordered list of (FactId, direction) traversal steps
```

It must not depend on enumeration order, memory addresses, generated counters or wall-clock values.

Two paths to the same node therefore produce two occurrences. Reaching an already visited node through another path is allowed. Reaching a node already present in the current path creates a terminal cycle occurrence and is not expanded further.

### 8. Deterministic output

Semantic ordering is fixed before JSON serialization:

- nodes by resource identifier;
- facts by `FactId`;
- occurrences by layer, then `OccurrenceId`;
- occurrence facts by layer, occurrence ID and `FactId`;
- diagnostics by stable code and stable context.

The implementation emits compact UTF-8 JSON with a fixed property order. Byte-for-byte equality is required within the pinned SWI-Prolog/runtime environment used by CI. Cross-version compatibility is defined by semantic JSON equality unless the runtime version is also pinned.

Timing, process ID, temporary paths and other volatile values are excluded from deterministic result documents. They may appear in a separate run report outside the command result.

### 9. Command boundaries

#### `health`

Returns protocol version, loaded epoch/revision, manifest hashes, available commands and configured hard limits. It does not execute traversal.

#### `inspect-facts`

Returns canonical base facts incident to one entity, including complete source triples and origins. It does not apply generic UI grouping.

#### `entity-view`

Returns the deterministic generic Prolog view defined by ADR-0006. Optional bounded depth may compose nested sections through the same traversal engine; it does not introduce new domain-specific profiles.

#### `subgraph`

Returns:

```text
root
limits/effective limits
nodes
facts
occurrences
occurrenceFacts
diagnostics
```

It does not return arbitrary Prolog terms, execute caller-provided predicates or modify the epoch.

### 10. Security and isolation

The reviewed entry module:

- imports only reviewed modules from the active epoch package;
- does not call `shell/1`;
- does not accept `consult/1` targets;
- does not accept filesystem paths from request JSON;
- does not dynamically construct callable predicates from request strings;
- treats all entity and resource identifiers as data;
- performs no writes to active epoch files;
- executes with a bounded working directory and environment supplied by the caller.

Builder and Search will later receive additional reviewed tools, but they do not gain a generic Prolog execution endpoint through this protocol.

## Validation order

For every request:

1. parse one JSON value;
2. validate envelope and command-specific shape;
3. validate protocol version;
4. validate requested epoch/revision;
5. calculate effective limits;
6. execute the whitelisted command under limits;
7. normalize and sort the result;
8. serialize one response envelope;
9. exit with the corresponding code.

## Required verification cases

1. JSON containing Cyrillic, quotes and backslashes passes through stdin without shell escaping.
2. Unknown command returns a structured error and non-zero exit.
3. Wrong protocol version is rejected before command execution.
4. Wrong epoch or revision is rejected explicitly.
5. Requested limits above hard limits are clamped and diagnosed.
6. `rdf:type` remains visible but does not create occurrences by default.
7. An unknown ordinary IRI predicate remains traversable.
8. Incoming and outgoing traversal retain the original source triple.
9. Two distinct paths to IIS create one node and two deterministic occurrences.
10. A cycle creates a terminal cycle occurrence and terminates.
11. Repeated execution in the pinned environment produces byte-identical stdout.
12. Volatile process data does not appear in deterministic output.
13. Timeout or output-limit termination changes no active files.
14. No request field can select a module, file path, predicate or raw Prolog goal.

## Rejected alternatives

### JSON in command-line arguments

Rejected because quoting and length behavior differs across PowerShell, cmd.exe, Bash and process-launch APIs.

### Success-only JSON

Rejected because C#, Builder and Search need one machine-readable failure contract. Stderr-only expected errors force fragile text parsing.

### Caller-controlled unbounded limits

Rejected because the same CLI is intended for LLM-assisted workflows and must remain safe under malformed or adversarial requests.

### Global visited-node suppression

Rejected because it erases distinct semantic paths such as “studied at IIS” and “worked at IIS”. Cycle prevention is path-local; output growth is bounded separately.

### Arbitrary Prolog query endpoint

Rejected for v0. It would bypass reviewed predicates, limits and evidence contracts and would become a remote code/configuration surface.

## Consequences

- The initial process remains simple and disposable.
- Windows and Unix callers use the same JSON protocol.
- A future long-lived Prolog worker can preserve the request/response envelope.
- Traversal semantics become testable independently of React and ASP.NET.
- Builder/Search gain a safe primitive rather than a generic code-execution channel.
- Exact deterministic output has a defined runtime boundary instead of an accidental promise across all SWI versions.
