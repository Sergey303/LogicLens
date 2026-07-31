# Semantic planning benchmark v0 verification

The frozen benchmark lives at:

```text
experiments/presentation/semantic-planning-v0/
```

Verify it from the repository root:

```powershell
python .\tools\verify_semantic_planning_benchmark.py
```

Machine-readable output:

```powershell
python .\tools\verify_semantic_planning_benchmark.py --json
```

The verifier is standard-library-only and fail-closed. It checks:

- the frozen external SHA-256 trust anchor for `manifest.json`;
- every listed file byte count and SHA-256;
- absence of unlisted files, path traversal, and symbolic links;
- exact v0 object keys and literal shapes;
- unique FactIds, claimIds, questionIds, caseIds, and manifest paths;
- all answer, evidence, alternative, dimension, and coverage references;
- deterministic profile counts, common predicates, and candidate coverage;
- hard separation between rich-view coverage and fallback-only facts;
- mandatory availability of the generic fallback.

The verifier deliberately does **not** normalize or allowlist oracle `role` strings.
Values such as `publication_time`, `monetary_amount`, and `age` are frozen
research labels, not an accepted production vocabulary.

A change to the benchmark cannot pass merely by updating `manifest.json` together
with its files. The verifier pins the already-reviewed manifest SHA-256 outside the
benchmark directory. Replacing the benchmark therefore requires an explicit review
of both the frozen data and its trust anchor, or preferably a new benchmark version.

Focused tests:

```powershell
python .\tests\semantic_planning_benchmark_test.py
```

The tests create isolated temporary fixtures and cover valid input, manifest tamper,
coordinated manifest/data replacement, unlisted files, duplicate FactIds, broken
references, profile mismatches, coverage gaps, invalid literals, and preservation of
fixture-local semantic roles.
