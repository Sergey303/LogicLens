# Critical path — Compile, Don’t Teach (revised executable DAG)

Status: revised producer artifact for `ENG-153 / WP-001` after independent `REVISE`  
Repository scope: `EpistemicCompilerLab/`  
Machine source: [`WORK_PACKAGES.yaml`](WORK_PACKAGES.yaml)  
Validator: [`scripts/validate_work_packages.py`](scripts/validate_work_packages.py)  
Linear snapshot: [`validation/linear-relations-snapshot.json`](validation/linear-relations-snapshot.json)  
Report: [`validation/validation-report.json`](validation/validation-report.json)

## Meaning

There are no reliable duration estimates, so this is not a fictitious time-based CPM. It records the mandatory structural route, fan-out/fan-in dependencies and the longest chain by edge count.

The **actual submission terminal is `WP-406`**, not `GATE-401`. The managed publication lifecycle terminates at `WP-504`.

## Gate backbone

```text
W0: {WP-001, WP-002, WP-003, WP-004, WP-005, WP-006, WP-007}
    -> GATE-001

W1: GATE-001 -> {WP-101, WP-102}
    {WP-101, WP-102} -> WP-103 -> WP-104
    {WP-005, WP-006, WP-101} -> WP-105
    {WP-101, WP-102, WP-103, WP-104, WP-105} -> GATE-101

W2: GATE-101 -> {WP-201, WP-202, WP-203, WP-204, WP-205, WP-206}
    {WP-201, WP-202, WP-203, WP-204, WP-205, WP-206} -> WP-207
    {WP-201, WP-202, WP-203, WP-204, WP-205, WP-206, WP-207} -> GATE-201

W3: GATE-201 -> WP-301
    {GATE-201, WP-301} -> WP-302
    WP-302 -> WP-303   # blind HOLDOUT, embargoed
    WP-302 -> WP-305   # blind REPLICATION, no HOLDOUT access
    {WP-303, WP-305} -> WP-306  # controlled unblinding + frozen analysis
    {WP-301, WP-302, WP-303, WP-306} -> GATE-301

W4: GATE-301 -> WP-401 -> WP-402
    GATE-301 -> WP-403 -> WP-404
    {WP-402, WP-403, WP-404} -> WP-405
    {WP-401, WP-402, WP-403, WP-404, WP-405} -> GATE-401
    GATE-401 -> WP-406  # actual TMLR/OpenReview submission and receipt

W5: WP-406 -(official reviews arrive)-> WP-501 -> WP-502 -> WP-503
    -> GATE-501 -> WP-504
```

`WP-305` reaches `GATE-301` through `WP-306`; direct dependencies intentionally match current Linear `blockedBy`.

## Safe W3

```text
freeze
-> blind HOLDOUT execution, outcome embargoed
-> blind REPLICATION execution in separate context without HOLDOUT access
-> independent completeness/leakage PASS for both
-> one controlled unblinding
-> frozen confirmatory analysis
-> GATE-301
```

The HOLDOUT operator, REPLICATION operator and analyst are three distinct roles and sessions.

## Composite issue splits

- `WP-201A`: production compiler/runtime path A;
- `WP-201B`: matched adapters M0–M14;
- `WP-203A`: source-bound TRAIN/DEV construction;
- `WP-203B`: blind A/B annotation;
- `WP-203C`: independent adjudication;
- `WP-301H`: HOLDOUT build/audit/seal;
- `WP-301R`: independent REPLICATION build/audit/seal.

A parent cannot pass until every internal unit passes independent review.

## Executable context packet

Before `Backlog -> Todo`, generate and hash:

```text
TASK.md
REQUIRED_READING.md
INPUT_MANIFEST.json
ALLOWED_PATHS.txt
FORBIDDEN_PATHS.txt
ACCEPTANCE.yaml
HANDOFF_SCHEMA.json
```

Every mandatory node contains exact context, allowed/forbidden paths, actions, complete deliverables, commands, five acceptance classes, STOP/PIVOT and structured handoff. Generic placeholders are rejected.

## Roles

Exact specialist roles replace phase aliases, including Claim–Evidence Architect, Novelty Reviewer, Independent Oracle Architect, Statistical Design Reviewer, Mutation and Dependency Auditor, Independent Leakage Auditor, Blind HOLDOUT Run Operator, Blind Replication Run Operator, Confirmatory Analyst and Submission Receipt Auditor.

Every critical package records identity, session, prior roles and conflicts. Producer, reviewer and gatekeeper are distinct.

## Actual submission and W5

`WP-406` creates the TMLR/OpenReview identifier, receipt, timestamp, uploaded-hash audit and anonymity audit of the actually uploaded version.

W5 manages official review intake, evidence-bound response, only preregistered symmetric revision experiments, `GATE-501`, and archival of the executed outcome.

## Optional robustness work

The following exist in both YAML and this document:

| ID | Work | Cutoff |
|---|---|---|
| `ROB-001` | second reproducible teacher or human baseline | before `WP-207` |
| `ROB-002` | additional public student model family | before `WP-207` |
| `ROB-003` | additional domain/source family | before `GATE-101` |
| `ROB-004` | extended latency/cost/token analysis | before `WP-302` |
| `ROB-005` | privacy-bounded public-surrogate simulation | before `GATE-301` |

They remain optional unless a gate explicitly promotes one through PIVOT.

## Longest chain

```text
WP-001 -> GATE-001 -> WP-101 -> WP-103 -> WP-104 -> GATE-101
-> WP-201 -> WP-207 -> GATE-201 -> WP-301 -> WP-302 -> WP-303
-> WP-306 -> GATE-301 -> WP-401 -> WP-402 -> WP-405 -> GATE-401
-> WP-406 -> WP-501 -> WP-502 -> WP-503 -> GATE-501 -> WP-504
```

Validated topology: **40 mandatory nodes**, **68 direct dependency edges**, longest chain **24 nodes / 23 edges**.

## Current authorization

Only W0 is actionable: `WP-001…WP-007`, then `GATE-001`.

W1 and later remain blocked. This revision does not authorize benchmark scaling, runtime expansion, sealed data or model evaluation.

## Reproduce validation

```text
python EpistemicCompilerLab/research-execution/scripts/validate_work_packages.py --as-of 2026-08-05
```
