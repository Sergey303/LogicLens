# Program audit remediation — 2026-08-05

This file records changes applied after `PROGRAM_AUDIT_2026-08-05.md`.

## ENG-153

- independent decision: `REVISE`;
- issue returned from `In Review` to `In Progress`;
- review comment contains eight blockers and required revision;
- GATE-001 remains blocked.

## Added W0 feasibility gate input

- `ENG-188 / WP-007` — resource, compute, annotation staffing and contingency feasibility;
- status: `Todo`;
- blocks `ENG-159 / GATE-001`;
- GATE-001 must not PASS without a powered and operationally feasible scope.

## Corrected W3 blind execution sequence

Previous unsafe sequence:

```text
HOLDOUT execution + score exposure
-> replication execution and analysis by one role
```

Corrected sequence:

```text
ENG-175 freeze/preregistration
  -> ENG-176 blind HOLDOUT execution, embargoed outcomes
  -> ENG-189 blind REPLICATION execution with no HOLDOUT access, embargoed outcomes
  -> ENG-177 / WP-306 controlled one-time unblinding and frozen analysis
  -> ENG-178 / GATE-301
```

Applied changes:

- `ENG-176` renamed and rewritten as blind HOLDOUT execution without unblinding;
- `ENG-189 / WP-305` added as an independent blind replication run;
- `ENG-177` rewritten as analysis-only `WP-306`, blocked by both execution packages;
- analyst must differ from both blind run operators.

## Added actual submission execution

- `ENG-190 / WP-406` — actual TMLR/OpenReview submission and immutable receipt;
- blocked by `ENG-184 / GATE-401`;
- the first-submission path now ends in a platform identifier and uploaded-hash audit rather than authorization alone.

## Added W5 post-submission route

Milestone: `W5 — Review response, revision and resubmission`.

- `ENG-191 / WP-501` — atomic review intake and classification;
- `ENG-192 / WP-502` — evidence-bound response and revision plan;
- `ENG-193 / WP-503` — approved symmetric revision work;
- `ENG-194 / GATE-501` — submit revision / discuss / adapt venue / accept / stop;
- `ENG-195 / WP-504` — execute the gate decision and archive publication outcome.

## Required ENG-153 revision scope

The revised DAG must include at least:

- exact roles and complete context/acceptance for all packages;
- `ENG-188`, `ENG-189`, `ENG-190`, and W5 `ENG-191…195`;
- actual optional robustness entries or removal of the false `ROB-001…ROB-005` claim;
- versioned semantic validator and committed validation report;
- terminal definitions for first submission and full publication lifecycle;
- synchronized Linear relations and role-separation checks.

No W1+ work is authorized until the revised ENG-153 passes independent review and GATE-001 later passes all W0 inputs.
