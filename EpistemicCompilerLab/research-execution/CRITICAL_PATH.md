# Critical path — Compile, Don’t Teach

Status: producer artifact for `ENG-153 / WP-001`  
Repository scope: `EpistemicCompilerLab/`  
Operational source of truth: Linear project **Compile, Don’t Teach — TMLR Flagship**  
Machine-readable source: [`WORK_PACKAGES.yaml`](WORK_PACKAGES.yaml)  
Schema: [`schemas/work-package.schema.json`](schemas/work-package.schema.json)

## 1. Interpretation of “critical path”

The project has no duration estimates, so this document does **not** claim a unique schedule-critical path. It defines two reproducible notions:

1. **Structural critical set** — every mandatory node that is an ancestor of `GATE-401`.
2. **Longest dependency chain by edge count** — a diagnostic only; it is not a time estimate.

All 32 Linear nodes `ENG-153…ENG-184` are mandatory ancestors of `GATE-401`. Therefore all of them are structurally critical. Parallel branches may have schedule slack only after durations and resource constraints are estimated.

## 2. Gate backbone

```text
W0: {WP-001, WP-002, WP-003, WP-004, WP-005, WP-006}
    -> GATE-001

W1: GATE-001 -> {WP-101, WP-102}
    {WP-101, WP-102} -> WP-103 -> WP-104
    {WP-005, WP-006, WP-101} -> WP-105
    {WP-101, WP-102, WP-103, WP-104, WP-105}
    -> GATE-101

W2: GATE-101 -> {WP-201, WP-202, WP-203, WP-204, WP-205, WP-206}
    {WP-201, WP-202, WP-203, WP-204, WP-205, WP-206}
    -> WP-207
    {WP-201, WP-202, WP-203, WP-204, WP-205, WP-206, WP-207}
    -> GATE-201

W3: GATE-201 -> WP-301
    {GATE-201, WP-301} -> WP-302 -> WP-303 -> WP-304
    {WP-301, WP-302, WP-303, WP-304}
    -> GATE-301

W4: GATE-301 -> WP-401 -> WP-402
    GATE-301 -> WP-403 -> WP-404
    {WP-402, WP-403, WP-404} -> WP-405
    {WP-401, WP-402, WP-403, WP-404, WP-405}
    -> GATE-401
```

Gate decisions are strict:

| Gate | Decision space | Unlocks |
|---|---|---|
| `GATE-001` | `PASS / REVISE / REJECT / PIVOT` | W1 contracts and benchmark design |
| `GATE-101` | `PASS / REVISE / REJECT / PIVOT` | W2 implementation and DEV-only work |
| `GATE-201` | `PASS / REVISE / REJECT / PIVOT` | sealed construction and preregistration |
| `GATE-301` | full paper / minimal contract / boundary study / failure analysis / stop | evidence-bounded W4 route |
| `GATE-401` | `PASS / REVISE / DO NOT SUBMIT` | actual TMLR submission |

No downstream phase may start on `REVISE`, `REJECT`, `PIVOT`, or an unresolved Blocker unless the gate record explicitly defines the new narrower route.

## 3. Representative longest structural chains

The graph contains several equal longest chains because W0, W1, W2, and W4 contain parallel mandatory branches. Each longest chain has 18 nodes and 17 edges.

A representative artifact chain is:

```text
WP-001
-> GATE-001
-> WP-101
-> WP-103
-> WP-104
-> GATE-101
-> WP-201
-> WP-207
-> GATE-201
-> WP-301
-> WP-302
-> WP-303
-> WP-304
-> GATE-301
-> WP-403
-> WP-404
-> WP-405
-> GATE-401
```

A representative evidence/manuscript chain has the same length and replaces the W4 artifact branch with:

```text
GATE-301 -> WP-401 -> WP-402 -> WP-405 -> GATE-401
```

The terminal wave explicitly contains:

1. `WP-403` — anonymous reproducibility artifact;
2. `WP-404` — clean-room reproduction;
3. `WP-405` — current TMLR/OpenReview policy verification and submission package;
4. `GATE-401` — final submission authorization.

Thus the flagship route cannot terminate at a manuscript alone.

## 4. Phase entry and exit conditions

### W0 — Research governance and causal design

**Entry:** non-sealed scientific contracts and historical pilots are available.  
**Parallel work:** WP-001…WP-006.  
**Exit:** independent `GATE-001 PASS`.

Immediate STOP/PIVOT triggers include occupied novelty, unsupported central claims, answer-copying or solver/no-solver confounding, infeasible power, and inability to design an independent oracle.

### W1 — Contracts, sources, and leakage-safe benchmark design

**Entry:** `GATE-001 PASS`.  
**Core convergence:** semantics and sources feed case design; case design feeds leakage design; semantic/oracle/statistical inputs feed scorer design.  
**Exit:** independent `GATE-101 PASS`.

No production implementation or confirmatory case generation is authorized before this gate.

### W2 — Implementation and DEV-only calibration

**Entry:** `GATE-101 PASS`.  
**Parallel work:** production runtime, independent oracle, TRAIN/DEV corpus, leakage tooling, model/run harness, and isolated teacher tracks.  
**Convergence:** all six branches feed WP-207 DEV-only calibration.  
**Exit:** independent `GATE-201 PASS`.

Any sealed access, undetected leakage drill, oracle circularity, model/config drift, or power failure blocks the phase.

### W3 — Freeze, one-shot HOLDOUT, and independent REPLICATION

**Entry:** `GATE-201 PASS`.  
**Sequence:** sealed dataset -> preregistration -> one-shot HOLDOUT -> independent REPLICATION and frozen analysis.  
**Exit:** `GATE-301` selects exactly one evidence-bounded paper route.

Partial HOLDOUT inspection, post-result changes, favorable-subset selection, or replication contamination invalidates the affected route.

### W4 — Claim audit, anonymous artifact, and submission

**Entry:** an explicit `GATE-301` route.  
**Parallel branches:** independent claim audit/manuscript and anonymous artifact/clean-room reproduction.  
**Convergence:** current venue-policy verification and complete submission package.  
**Exit:** `GATE-401 PASS`.

A manuscript claim cannot survive by author intent, and submission is forbidden while anonymity, licensing, reproduction, evidence, or policy Blockers remain.

## 5. Claim and threat coverage

Every mandatory node links to one or more of:

- hypotheses `H1…H6`; or
- explicit threat controls such as oracle circularity, leakage, answer copying, underpower, extraction dominance, one-model/domain concentration, anonymity, licensing, or reproducibility.

`H6` is secondary. Failure of privacy-bounded portability may remove H6 without invalidating H1, provided no private-data leakage affects the primary experiment.

No package may introduce fuzzy membership, answer-level probability, model training, persistent service, cryptographic privacy claims, or a broader universal claim.

## 6. Optional robustness work

Optional robustness items are listed separately in `WORK_PACKAGES.yaml` as `ROB-001…ROB-005`:

- second reproducible teacher or human-designed teacher baseline;
- an additional public student model family;
- an additional domain/source family;
- extended latency/cost/token-efficiency analysis;
- privacy-bounded portability simulation on public surrogate data.

They are not prerequisites for `GATE-401` unless a gate explicitly promotes one after a documented PIVOT. They must be frozen before their declared cutoff and must not delay, contaminate, or underpower the primary contrast.

## 7. Change control

A graph or scope change is valid only when:

1. the corresponding Linear relation/status/decision is updated;
2. this DAG is updated in the same bounded change;
3. affected input hashes and downstream invalidations are recorded;
4. the change does not weaken a critical protocol;
5. an independent reviewer and gatekeeper remain distinct from the artifact creator.

After confirmatory freeze, scientific choices cannot be edited in place. A changed scientific choice creates a new protocol version and invalidates the previous confirmatory status.

## 8. Machine checks performed for WP-001

Validation snapshot: 2026-08-05.

| Check | Result |
|---|---:|
| JSON Schema Draft 2020-12 validation | PASS |
| Mandatory nodes | 32 |
| Dependency edges | 59 |
| Unique node IDs | PASS |
| Unknown dependencies | 0 |
| DAG cycles | 0 |
| Topologically sorted nodes | 32 / 32 |
| Mandatory orphan nodes | 0 |
| Mandatory nodes reaching `GATE-401` | 32 / 32 |
| Work packages missing producer/reviewer/gatekeeper/gate/STOP | 0 |
| Nodes without H1–H6 or threat-control link | 0 |
| Anonymous artifact reaches final submission gate | PASS |
| Longest dependency chain | 18 nodes / 17 edges |

Validation environment used for the producer check:

```text
Python 3.13.5
PyYAML 6.0.3
jsonschema 4.26.0
```

The independent reviewer must rerun validation and adversarially compare this graph with current Linear relations before accepting WP-001.
