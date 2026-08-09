# ENG-202 — General-capability regression check plan

Status: frozen pre-training diagnostic plan. It is not a publication endpoint and cannot select adapters.

## Purpose

Weight adaptation may improve the target task while degrading ordinary capabilities. `W-A`, every `W-B` seed and every `W-C` seed therefore run the same frozen non-target diagnostic set after training.

The diagnostic is deliberately small and synthetic. It is not claimed to estimate general intelligence or benchmark quality; it is only an early catastrophic-regression guard under a fixed contract.

## Frozen cases

`prototype/general_regression_dev.jsonl` contains exactly 12 DEV-only synthetic cases across four families:

1. simple arithmetic;
2. literal instruction following;
3. short Python code understanding;
4. compact JSON transformation.

There are three cases per family. None uses target-domain epistemic status, source provenance, Prolog/Python comparator artifacts, teacher evidence, course data, HOLDOUT or REPLICATION material.

## Evaluation

The frozen evaluator computes exact normalized answer correctness per case and family. Normalization is limited to UTF-8 trim plus CRLF→LF; semantic aliases are not added post hoc.

Run the same inference prompt/decoding budget for W-A/W-B/W-C. The regression diagnostic receives no adapter-specific hints.

Report:

- 12-case exact accuracy for W-A and every adapted seed;
- four 3-case family accuracies;
- per-case paired change from W-A;
- count of W-A-correct cases changed to incorrect by each adapter.

## No selection / no tuning

This set must not be used to:

- choose the best W-B/W-C seed;
- choose an intermediate checkpoint;
- extend optimizer steps;
- tune rank, learning rate or data;
- regenerate Codex targets;
- remove an unfavorable run.

The final-step-only and all-seed reporting rules remain authoritative.

## Predeclared diagnostic flags

These flags are descriptive feasibility warnings, not hypothesis-test thresholds:

- `REGRESSION_NONE`: no W-A-correct case flips to incorrect;
- `REGRESSION_PRESENT`: 1–2 W-A-correct cases flip;
- `REGRESSION_SEVERE`: >=3 W-A-correct cases flip or any family loses all three W-A-correct cases.

A severe flag does not permit recipe repair within the same candidate. It triggers a WP-004/WP-007 decision to retain the unfavorable result, exclude the weight-changing arm from confirmatory consideration, or version a new candidate and rerun the full predeclared process.

## Scientific boundary

Because this is a 12-case synthetic diagnostic, no broad claim such as “general capabilities are preserved” is allowed from a pass. The only permitted statement is that no catastrophic regression was observed on this frozen diagnostic set, if that is what the data show.
