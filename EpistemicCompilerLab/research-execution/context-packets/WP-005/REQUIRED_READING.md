# Required reading for WP-005

## Frozen local control inputs

- `EpistemicCompilerLab/research-execution/WORK_PACKAGES.yaml`
- `EpistemicCompilerLab/research-execution/schemas/work-package.schema.json`
- `EpistemicCompilerLab/research-execution/schemas/work-package-handoff.schema.json`
- `EpistemicCompilerLab/research-execution/validation/linear-relations-snapshot.json`
- `EpistemicCompilerLab/research-execution/CRITICAL_PATH.md`
- `EpistemicCompilerLab/research-execution/ENG-153_INDEPENDENT_REVIEW_ROUND2_2026-08-06.md`

The local files above remain hash-pinned by `INPUT_MANIFEST.json`; the R2 remediation does not rewrite those historical inputs.

## Package-specific semantic context

- `ORACLE_AND_SCORER_PROTOCOL.md`
- typed epistemic boundary
- historical schemas as non-normative input
- current `oracle/SEMANTIC_SPEC.md`
- current `oracle/SEMANTIC_REGISTRY.json`
- current `oracle/POLICY_TABLE.json`

## Mandatory independent-review findings driving this remediation

Read the Linear ENG-157 Independent Mutation and Dependency Review R2 (`REVISE`, 2026-08-09) and the repository audit it references before evaluating the remediation. The four bounded findings to close are:

1. stale generic evidence/proof vocabulary in `ORACLE_PACKET_CONTRACT.json` versus final blind-gold vocabulary;
2. producer preflight PASS not reproducible from the frozen candidate bytes;
3. contradictory freeze order among acceptance/handoff, gold protocol and independence boundary;
4. no candidate-wide validator/negative fixtures for those lifecycle drifts.

## Remediation normative surfaces

- `EpistemicCompilerLab/research-execution/context-packets/WP-005/ACCEPTANCE.v1.3.yaml` — authoritative detailed acceptance/freeze order;
- `EpistemicCompilerLab/research-execution/oracle/ORACLE_LIFECYCLE_CONTRACT.json` — machine-readable exact mirror of that freeze order;
- `EpistemicCompilerLab/research-execution/oracle/GOLD_ADJUDICATION_PROTOCOL.json`;
- `EpistemicCompilerLab/research-execution/oracle/ORACLE_PACKET_CONTRACT.json`;
- `EpistemicCompilerLab/research-execution/oracle/INDEPENDENCE_BOUNDARY.md`;
- `EpistemicCompilerLab/research-execution/oracle/ORACLE_LIFECYCLE_NEGATIVE_FIXTURES.json`;
- `EpistemicCompilerLab/research-execution/scripts/validate_oracle_gold_governance.py`.

The key distinction is intentional: **outcome gold is frozen before B-oracle runs, but outcome gold is not mounted or visible to B during computation**. Freeze prevents repair-from-B; physical isolation prevents answer leakage.

No sealed HOLDOUT/REPLICATION material is authorized context. Producer-side validation, however complete, is not independent acceptance or GATE-001 approval.
