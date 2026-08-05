# Linear publication project

## Project

**Compile, Don’t Teach — TMLR Flagship**  
https://linear.app/engdocsentinel/project/compile-dont-teach-tmlr-flagship-81a9ece02641

This Linear project is the operational source of truth for work status, ownership, dependencies, independent reviews and gate decisions for the flagship paper.

Technical pilots and historical runtime work remain in the separate Linear project **Epistemic Compiler Lab**. Pilot results `18/18` and `24/24` are hypothesis-forming evidence only, never confirmatory evidence.

## Linear documents

- Program Charter: https://linear.app/engdocsentinel/document/program-charter-compile-dont-teach-b1dfc9ae0393
- Agent Roles and Independence Matrix: https://linear.app/engdocsentinel/document/agent-roles-and-independence-matrix-ada38c91109b
- Work Package Operating Standard: https://linear.app/engdocsentinel/document/work-package-operating-standard-a9c5bb1d72fe
- Evidence, Gates and STOP/PIVOT Policy: https://linear.app/engdocsentinel/document/evidence-gates-and-stoppivot-policy-5e9304687d58

## Milestones

1. `W0` — Research governance and causal design.
2. `W1` — Contracts, sources and leakage-safe benchmark design.
3. `W2` — Implementation and DEV-only calibration.
4. `W3` — Protocol freeze, one-shot HOLDOUT and independent replication.
5. `W4` — Independent claim audit, anonymous artifact and TMLR submission.

## Work packages

Linear issues `ENG-153` through `ENG-184` define the publication workflow.

### Active wave

Only `W0` is initially actionable:

- `ENG-153` — executable research-program DAG;
- `ENG-154` — claim–evidence matrix and abstract contract;
- `ENG-155` — systematic related-work and novelty boundary;
- `ENG-156` — causal design and strongest matched controls;
- `ENG-157` — independent oracle/scorer boundary;
- `ENG-158` — power and confirmatory analysis plan;
- `ENG-159` — methodology gate.

All later work is blocked by explicit Linear dependencies. Do not start benchmark scaling, runtime expansion or sealed-data construction before `ENG-159` records `PASS`.

## Role and acceptance rule

Every critical package uses:

```text
Producer -> Independent Reviewer -> Gatekeeper -> PASS / REVISE / REJECT / PIVOT
```

The creator of a critical artifact must not approve it. Because the Linear workspace currently has one human member, the assignee is the accountable owner; the actual agent role, forbidden context, reviewer and acceptance criteria are defined in each issue description.

## Synchronization rules

- Linear tracks status, dependencies, ownership, decisions and review evidence.
- Git stores scientific contracts, code, manifests, hashes, raw artifacts and structured handoffs.
- A Linear issue may be marked `Done` only after its declared repository deliverables and independent review evidence exist.
- A task prompt or local implementation decision may not weaken the repository protocols or Linear gate criteria.
- Any benchmark-isolation violation invalidates the affected confirmatory run and must be recorded in both Git and Linear.

## Required reading order

1. [`TARGET_PAPER_COMPILE_DONT_TEACH.md`](TARGET_PAPER_COMPILE_DONT_TEACH.md)
2. [`TARGET_PAPER_FULL_EXECUTION_PATH_AND_STRICT_AUDIT.md`](TARGET_PAPER_FULL_EXECUTION_PATH_AND_STRICT_AUDIT.md)
3. [`critical-protocols/README.md`](critical-protocols/README.md)
4. This Linear project map.
5. The exact Linear work package assigned to the agent.
