# ADR-0010: provider-neutral Builder candidate package

- Status: Proposed
- Linear: ENG-46, child of ENG-26
- Depends on: ADR-0003, ADR-0007, ADR-0008
- Scope: trusted input, isolation, validation and comparison for Builder candidates

## Context

ENG-26 compares Qwen and Codex while both solve the same epoch-building task. A useful comparison requires more than two folders of generated Prolog. Both providers need one stable input contract, one validation pipeline and one report format. Otherwise provider-specific wrappers can silently change permissions, tests, limits or scoring.

A generated candidate is untrusted. It must not receive write access to the active epoch, choose arbitrary filesystem paths, replace the reviewed entry point, load arbitrary modules or introduce an unknown UI component. It also must not activate itself after passing only syntax checks.

## Decision

### Provider output is a proposal directory

A provider, manual repair step or deterministic fixture produces:

```text
proposal.json
files/
  rules/candidate_*.pl
  tests/candidate_*_tests.pl
  ui/*.json
```

`proposal.json` conforms to `contracts/epoch-candidate-v0.schema.json` and records:

- candidate and task identity;
- expected base epoch and revision;
- provider kind, name, model and optional run ID;
- UI and CLI contract versions;
- optional measured CLI calls, manual fixes, elapsed time and cost;
- every proposed file and its reviewed kind.

The proposal does not contain an output path, active package path, Prolog goal, module selector, predicate selector or activation instruction.

### Candidate v0 is additive

The first trusted slice may add only:

```text
rules/candidate_*.pl
tests/candidate_*_tests.pl
ui/*.json
```

It may not replace or remove:

- `entry.pl`;
- active data or origins;
- ontology files;
- CLI runtime;
- generic view, traversal or visibility rules;
- active manifest or smoke requests.

This is intentionally narrower than the final Builder. It proves proposal identity, isolation, executable candidate tests and deterministic comparison before allowing reviewed replacement overlays.

### Paths are data, never execution arguments

Every declared path is parsed as a POSIX relative path. Absolute paths, `..`, backslashes, symlinks, undeclared files, duplicate declarations and paths outside the allowlist are rejected.

The candidate is copied into a newly created isolated package directory. The active package is read and hashed before work starts and is hashed again after all checks. Any change is a verification failure.

### Prolog safety boundary

Candidate Prolog must be UTF-8 and may use only reviewed directives:

```text
module
use_module
begin_tests
end_tests
```

Rule files may import only `../data/epoch_data.pl`. Test files may import only declared candidate rule modules.

The static gate rejects filesystem, process, network, mutation and dynamic invocation primitives, including shell/process calls, arbitrary consult/load, file operations, assertion/retraction and dynamic `call` forms. Absolute paths and URLs are rejected.

Static checks do not replace execution checks. SWI-Prolog must load all candidate modules under a hard timeout and run all declared candidate tests. A candidate without at least one rule and one test is invalid.

### UI bindings remain declarative

Candidate UI files contain only a version and predicate-to-component bindings. Components are restricted to the trusted UI Document v0 data vocabulary:

```text
Property
TextBlock
RawProlog
Diagnostic
```

Unknown rich components such as `Table`, `Graph`, `Form` or arbitrary HTML are rejected before package creation.

### Stable active runtime remains unchanged

After candidate modules and tests pass, the portable `health`, `entity-view` and `subgraph` smoke requests execute against both baseline and candidate package copies. Their stdout must be byte-identical.

Passing this check means only that the additive candidate did not change the currently active runtime contract. It does not mean the candidate feature is activated or selected as the recommended epoch.

### Deterministic candidate identity

`candidateHash` is SHA-256 over a versioned domain plus canonical `proposal.json` and all candidate file paths and bytes.

`candidatePackageHash` is SHA-256 over a separate versioned domain plus the complete copied baseline and candidate additions, excluding `candidate-manifest.json` itself.

The generated candidate manifest contains no timestamps, temporary paths, process IDs or machine-specific values. Rebuilding the same proposal over the same baseline must produce a byte-identical package and report.

### Comparison report

The deterministic report records:

- base epoch, revision and package hash;
- candidate and provider identity;
- provider-supplied measured metrics;
- candidate and package hashes;
- rule, test and UI file counts;
- every required validation result;
- added files;
- modified and removed active files, which must both be empty in v0;
- whether stable runtime outputs remained identical.

The report is suitable as one input to the later Qwen/Codex comparison. It deliberately does not invent correctness, time or cost values that the provider run did not supply.

### No activation

A valid candidate package remains an artifact. This contract provides no command or API that changes the active epoch pointer. Selection, repair, human review and atomic activation require later contracts.

## Verification

ENG-46 must prove:

1. the valid fixture builds twice into byte-identical candidate packages and reports;
2. the active package passes its own manifest and portable smoke verification first;
3. candidate Prolog loads and its declared tests pass;
4. baseline and candidate portable smoke outputs are byte-identical;
5. the active package tree is unchanged after successful and failed validation;
6. path traversal and output overlap are rejected;
7. a candidate without tests is rejected;
8. dangerous Prolog calls and unreviewed directives are rejected;
9. unknown UI components are rejected;
10. undeclared files are rejected;
11. a proposal bound to another revision is rejected;
12. accepted artifacts and logs are retained by CI.

## Rejected alternatives

### Let each provider write directly into an epoch checkout

Rejected because permissions, hidden files and provider-specific cleanup would become part of the experiment and could mutate reviewed inputs.

### Accept a patch or archive without a manifest

Rejected because file identity, provider metadata, expected revision and declared intent would be ambiguous.

### Allow arbitrary replacement overlays immediately

Rejected because replacing reviewed runtime modules needs a stronger semantic diff, compatibility and activation contract. The additive slice establishes the trusted boundary first.

### Trust syntax success as candidate correctness

Rejected because syntax does not prove tests, bounded execution, UI vocabulary, active-package immutability or deterministic output.

### Embed provider invocation in the trusted package builder

Rejected because Ollama and Codex are proposal producers, not trusted validators. Both must pass through the same provider-neutral contract.

## Consequences

- Qwen, Codex, a human repair and a deterministic fixture can produce the same proposal shape.
- Provider credentials and invocation details remain outside the trusted candidate validator.
- Candidate tests become mandatory evidence rather than optional prose.
- Active epoch files remain immutable during candidate evaluation.
- ENG-26 still requires two real provider runs and a recommended repaired version; ENG-46 supplies only their common trusted foundation.
