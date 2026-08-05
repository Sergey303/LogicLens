# Program audit — Compile, Don’t Teach

Date: 2026-08-05  
Scope: `ENG-153…ENG-184`, repository commit `f6bf7ac40fa78c25aff5a2b00b929d2c30b90714`  
Reviewer decision for ENG-153: **REVISE**

## 1. Executive verdict

The Linear gate backbone is coherent and the producer preserved the flagship claim boundary. The current DAG is not yet an executable research operating system.

Blocking defects:

1. exact Linear roles, context, deliverables and acceptance checks were collapsed into phase-level aliases and generic placeholders;
2. `CRITICAL_PATH.md` claims `ROB-001…ROB-005`, while `WORK_PACKAGES.yaml` has `optional: {}`;
3. no versioned validator or committed machine-readable validation report exists;
4. HOLDOUT is scored before independent replication is executed;
5. replication execution and confirmatory analysis are assigned to one role;
6. the terminal node authorizes submission but does not perform submission;
7. the plan has no explicit post-submission review/revision/resubmission route;
8. resource, annotation-staffing and compute feasibility are not a W0 gate input.

## 2. ENG-153 acceptance audit

| Requirement | Result | Finding |
|---|---|---|
| schema validation | Partial PASS | Producer reports PASS; no committed rerunnable validator/report |
| acyclic graph | PASS by inspection/report | Must be independently rerunnable |
| zero mandatory orphans | PASS by report | Reachability logic must move into validator |
| exact producer/reviewer/gate/STOP | FAIL | Generic phase roles and inherited placeholders do not match Linear |
| no claim expansion | PASS | Central boundary and non-claims preserved |
| optional robustness separated | FAIL | Documentation/YAML contradiction |
| ends at artifact and submission | FAIL | Ends at authorization `GATE-401`, not actual submission |

## 3. System-wide mandatory remediation

Every package specification must include or resolve immutably:

- exact producer, independent reviewer and gatekeeper roles;
- `why_now` and exact dependency rationale;
- required paths/documents and input SHA-256 manifest;
- allowed and forbidden paths/data/results;
- complete actions and deliverables;
- machine-checkable acceptance commands/metrics;
- scientific, independence, adversarial and reproducibility checks;
- explicit STOP/PIVOT and structured handoff schema;
- evidence contribution to one claim or threat control.

A context packet must be generated before `Backlog -> Todo`:

```text
TASK.md
REQUIRED_READING.md
INPUT_MANIFEST.json
ALLOWED_PATHS.txt
FORBIDDEN_PATHS.txt
ACCEPTANCE.yaml
HANDOFF_SCHEMA.json
```

## 4. Per-package audit

### W0

| Issue | Decision | Required change |
|---|---|---|
| ENG-153 / WP-001 | REVISE | exact specs; real roles; optional work; validator; actual submission route |
| ENG-154 / WP-002 | REVISE | define claim-row schema, planned table IDs, wording levels and evidence status enum |
| ENG-155 / WP-003 | REVISE | add databases, backward/forward citation chasing, search saturation and pre-submission refresh |
| ENG-156 / WP-004 | REVISE | freeze estimands and baseline-selection rule; do not pretend strongest baseline is known before DEV |
| ENG-157 / WP-005 | MINOR REVISE | require clean-room context and reviewer with no production implementation access |
| ENG-158 / WP-006 | REVISE | deliver executable simulation code, assumptions manifest and compute/annotation feasibility envelope |
| ENG-159 / GATE-001 | REVISE | add resources/staffing feasibility and independent-session identity checks |

Add mandatory W0 package: resource, compute, annotation staffing, licensing and schedule feasibility.

### W1

| Issue | Decision | Required change |
|---|---|---|
| ENG-160 / WP-101 | REVISE | reviewer must not be the sole producer of the prior oracle-boundary artifact; require second semantic reviewer |
| ENG-161 / WP-102 | REVISE | seal replication-family identities from runtime/parser developers; define redistribution tiers |
| ENG-162 / WP-103 | REVISE | define annotator identities, agreement thresholds, adjudication authority and replacement rule |
| ENG-163 / WP-104 | MINOR REVISE | add mandatory synthetic leakage drills and fail-closed acceptance commands |
| ENG-164 / WP-105 | REVISE | exact mutation registry, score normal forms and independent implementation handoff |
| ENG-165 / GATE-101 | REVISE | require staffing feasibility, source-license audit and zero unresolved annotation ambiguity |

### W2

| Issue | Decision | Required change |
|---|---|---|
| ENG-166 / WP-201 | SPLIT | production compiler/runtime and M0–M14 adapters are separate independently reviewable artifacts |
| ENG-167 / WP-202 | REVISE | enforce repository/path isolation; dependency scanner and clean-room build required |
| ENG-168 / WP-203 | SPLIT/REVISE | separate corpus construction, blind annotation and adjudication reports |
| ENG-169 / WP-204 | MINOR REVISE | publish red-team leakage drill matrix and expected detections |
| ENG-170 / WP-205 | REVISE | add model-license/availability policy, hardware budget and provider-drift fallback |
| ENG-171 / WP-206 | REVISE | preserve as H4-supporting track; define reproducible human baseline and closed-teacher fallback |
| ENG-172 / WP-207 | REVISE | DEV may select only by frozen rules; all configuration decisions and discarded modes retained |
| ENG-173 / GATE-201 | REVISE | require code/data/model lock, clean-room oracle PASS and final blinded-execution plan |

### W3

| Issue | Decision | Required change |
|---|---|---|
| ENG-174 / WP-301 | SPLIT | build/audit HOLDOUT and REPLICATION as separately sealed artifacts, preferably by different blinded roles |
| ENG-175 / WP-302 | REVISE | preregister an embargo/unblinding protocol; neither result visible before both executions finish |
| ENG-176 / WP-303 | REVISE | execute and store HOLDOUT; score may be computed but inaccessible until replication run completes |
| ENG-177 / WP-304 | SPLIT | separate blind replication operator from confirmatory analyst; analyst receives both only after sealed completion |
| ENG-178 / GATE-301 | PASS AFTER FIX | route logic is strong after blind sequence and role separation are corrected |

Required corrected order:

```text
freeze
-> execute HOLDOUT blindly
-> execute REPLICATION blindly with no HOLDOUT access
-> completeness/leakage checks for both
-> one controlled unblinding event
-> frozen confirmatory analysis
-> GATE-301
```

### W4 and submission

| Issue | Decision | Required change |
|---|---|---|
| ENG-179 / WP-401 | MINOR REVISE | reviewer identity/session separation and conflict declaration |
| ENG-180 / WP-402 | MINOR REVISE | manuscript lint against claim matrix and prohibited wording |
| ENG-181 / WP-403 | REVISE | add early artifact dry-run before final manuscript to avoid late reproducibility failure |
| ENG-182 / WP-404 | MINOR REVISE | operator must lack author-repository access and record all deviations |
| ENG-183 / WP-405 | MINOR REVISE | official-source snapshot, verification date and policy hashes/quotes within limits |
| ENG-184 / GATE-401 | REVISE | this is authorization only; add actual submission package with receipt/OpenReview ID |

Add:

- actual submission work package after GATE-401;
- review triage, response matrix, symmetric revision experiments and resubmission/withdraw gate;
- accepted-version artifact release/camera-ready package when applicable.

## 5. Independence risks

Role names alone do not create independence. Each critical review must record:

- agent/session identity;
- input manifest and inaccessible paths;
- prior roles held by that identity;
- conflict declaration;
- whether producer outputs were visible before independent construction;
- reviewer commands and raw findings.

The same human owner may coordinate Linear, but producer and reviewer must use separate, logged contexts and must not share hidden implementation/data when clean-room independence is claimed.

## 6. Relation audit

Verified directly against Linear for W0, W1 and critical W2/W3 convergence nodes:

- ENG-153…158 block ENG-159;
- ENG-159 blocks ENG-160/161;
- ENG-160/161 block ENG-162; ENG-162 blocks ENG-163;
- ENG-157/158/160 block ENG-164;
- ENG-160…164 block ENG-165;
- ENG-166…171 converge into ENG-172 and ENG-173;
- ENG-173 blocks ENG-174/175; ENG-174 also blocks ENG-175;
- ENG-175 -> ENG-176 -> ENG-177 -> ENG-178.

These edges match the current YAML backbone. The scientific ordering inside W3 must nevertheless be revised as specified above.

## 7. Acceptance decision

- ENG-153: **REVISE**, returned to `In Progress`.
- GATE-001 remains blocked.
- W1–W4 remain `Backlog`.
- Only W0 packages may proceed, but their outputs must use the strengthened context/acceptance standard.

No benchmark scaling, runtime expansion or sealed-data work is authorized by this audit.
